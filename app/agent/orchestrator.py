from __future__ import annotations

from sqlalchemy.orm import Session

from app.agent.llm import LLMClient
from app.agent.policies import check_completeness
from app.agent.state_machine import AgentPhase
from app.evidence.verifier import verify_all
from app.extraction.normalizer import extract_json_blob, merge_structured
from app.extraction.parser import extract_from_text
from app.memory.session import SessionMemory
from app.recommendations.generator import build_recommendations
from app.recommendations.ranking import rank_recommendations
from app.recommendations.validator import validate_recommendations
from app.reasoning.multi_metric import MultiMetricReasoner
from app.retrieval.hybrid_search import get_hybrid_search
from app.retrieval.query_builder import build_retrieval_query
from app.schemas.environment import EnvironmentalState
from app.schemas.responses import AgentQueryResponse, EvidenceItem


class AgentOrchestrator:
    def __init__(self) -> None:
        self.memory = SessionMemory()
        self.reasoner = MultiMetricReasoner()
        self.llm = LLMClient()

    def run(
        self,
        db: Session,
        session_id: str | None,
        message: str | None,
        environment: dict | None,
    ) -> AgentQueryResponse:
        pipeline: list[str] = []
        pipeline.append(AgentPhase.UNDERSTAND.value)
        sid = self.memory.get_or_create(db, session_id)
        state = self.memory.load_state(db, sid)

        pipeline.append(AgentPhase.EXTRACT.value)
        incoming = EnvironmentalState()
        if message:
            incoming = extract_from_text(message, incoming)
            blob = extract_json_blob(message)
            if blob:
                incoming = merge_structured(incoming, blob)
            llm_json = self.llm.extract_json(message) if self.llm.available() else None
            if llm_json:
                incoming = merge_structured(incoming, llm_json, source="llm")
        if environment:
            incoming = merge_structured(incoming, environment)

        pipeline.append(AgentPhase.VALIDATE.value)
        state = self.memory.apply_update(state, incoming)
        if message:
            self.memory.add_message(db, sid, "user", message)

        pipeline.append(AgentPhase.CHECK_COMPLETENESS.value)
        completeness = check_completeness(state)
        if not completeness.complete:
            pipeline.append(AgentPhase.CLARIFY.value)
            questions = completeness.questions
            intro = (
                "I can assess this, but I need additional high-value information to distinguish "
                "whether the main constraint is soil degradation, water availability, or habitat simplification:"
            )
            numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))
            text = f"{intro}\n\n{numbered}"
            if self.llm.available():
                polished = self.llm.complete(
                    f"Missing variables: {completeness.missing}\nQuestions: {questions}\nState: {state.model_dump()}"
                )
                if polished:
                    text = polished
            pipeline.append(AgentPhase.UPDATE_MEMORY.value)
            self.memory.save_state(db, sid, state)
            self.memory.add_message(db, sid, "assistant", text)
            return AgentQueryResponse(
                status="clarification_required",
                session_id=sid,
                message=text,
                missing_information=completeness.missing,
                clarifying_questions=questions,
                environmental_state=state,
                pipeline=pipeline,
            )

        pipeline.append(AgentPhase.RETRIEVE.value)
        query = build_retrieval_query(message or "", state, problem="biodiversity decline")
        search = get_hybrid_search()
        evidence = search.search(db, query, state=state)
        if not evidence:
            pipeline.extend([AgentPhase.RESPOND.value, AgentPhase.UPDATE_MEMORY.value])
            msg = (
                "I found insufficient evidence to make a reliable quantitative estimate for this specific condition. "
                "I can still provide a qualitative recommendation, but the expected magnitude of improvement is uncertain."
            )
            self.memory.save_state(db, sid, state)
            self.memory.add_message(db, sid, "assistant", msg)
            return AgentQueryResponse(
                status="insufficient_evidence",
                session_id=sid,
                message=msg,
                summary=msg,
                environmental_state=state,
                evidence=[],
                pipeline=pipeline,
            )

        pipeline.append(AgentPhase.REASON.value)
        reasoning = self.reasoner.reason(state)
        pipeline.append(AgentPhase.GENERATE_OPTIONS.value)
        recs = build_recommendations(state, reasoning, evidence)
        recs = validate_recommendations(recs)
        recs = rank_recommendations(recs)
        pipeline.append(AgentPhase.VERIFY.value)
        recs = verify_all(recs, evidence)
        recs = recs[:3]
        reasoning.candidate_interventions = [rec.action for rec in recs]

        pipeline.append(AgentPhase.RESPOND.value)
        summary = self._summary(state, reasoning, recs)
        message_out = self._format_message(summary, recs)
        pipeline.append(AgentPhase.UPDATE_MEMORY.value)
        self.memory.save_state(db, sid, state)
        self.memory.add_message(
            db,
            sid,
            "assistant",
            message_out,
            payload={"recommendations": [r.model_dump() for r in recs]},
        )
        unique_evidence = self._unique_evidence(evidence)
        return AgentQueryResponse(
            status="recommendation_ready",
            session_id=sid,
            message=message_out,
            summary=summary,
            environmental_state=state,
            reasoning=reasoning,
            recommendations=recs,
            evidence=unique_evidence,
            pipeline=pipeline,
        )

    def _unique_evidence(self, evidence: list[EvidenceItem]) -> list[EvidenceItem]:
        seen: set[str] = set()
        out: list[EvidenceItem] = []
        for item in evidence:
            if item.document_id in seen:
                continue
            seen.add(item.document_id)
            out.append(item)
        return out[:8]

    def _summary(self, state: EnvironmentalState, reasoning, recs) -> str:
        parts = ["Identified conditions: " + "; ".join(reasoning.constraints)]
        if recs:
            parts.append("Priority intervention: " + recs[0].action + ".")
        parts.append(
            "Quantitative site-specific percentages are withheld unless a retrieved source supports them."
        )
        return " ".join(parts)

    def _format_message(self, summary: str, recs) -> str:
        blocks = [summary, ""]
        for i, rec in enumerate(recs, start=1):
            metrics = "\n".join(
                f"• {metric}  {rec.expected_direction.get(metric, '')}"
                for metric in rec.metrics_impacted
            )
            evidence_lines = "\n".join(
                f"- {item.title} ({item.publisher or item.source}, {item.year})"
                for item in rec.evidence
            )
            blocks.append(
                f"RECOMMENDATION {i}\n"
                f"{'─' * 36}\n\n"
                f"{rec.action}\n\n"
                f"WHY\n{rec.why_it_works}\n\n"
                f"METRICS\n{metrics}\n\n"
                f"TIME HORIZON\n{rec.time_horizon}\n\n"
                f"EVIDENCE\n{evidence_lines}\n\n"
                f"CONFIDENCE\n{rec.confidence}\n\n"
                f"ESTIMATED EFFECT\n{rec.estimated_effect}\n\n"
                f"ASSUMPTIONS\n" + "\n".join(f"• {a}" for a in rec.assumptions) + "\n\n"
                f"TRADEOFFS\n" + "\n".join(f"• {t}" for t in rec.tradeoffs) + "\n\n"
                f"HOW TO MEASURE\n{rec.measurement_plan}\n"
            )
        return "\n".join(blocks)
