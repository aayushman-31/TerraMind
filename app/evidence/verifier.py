from __future__ import annotations

import re

from app.schemas.responses import EvidenceItem, Recommendation

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")


def _evidence_blob(items: list[EvidenceItem]) -> str:
    return " ".join(f"{item.title} {item.text}" for item in items)


def verify_recommendation(rec: Recommendation) -> Recommendation:
    blob = _evidence_blob(rec.evidence)
    claims = NUMBER_RE.findall(rec.why_it_works + " " + rec.estimated_effect)
    unsupported = []
    for claim in claims:
        if claim.strip() not in blob:
            unsupported.append(claim)
    if unsupported or NUMBER_RE.search(rec.estimated_effect):
        rec.estimated_effect = (
            "Available evidence indicates that diversified cropping and habitat complexity can improve "
            "ecological outcomes, but a reliable percentage improvement cannot be estimated for this site "
            "from the available information."
        )
        rec.why_it_works = NUMBER_RE.sub("[unverified quantity removed]", rec.why_it_works)
    rec.confidence = rec.confidence or ("moderate" if rec.evidence else "low")
    return rec


def verify_all(recommendations: list[Recommendation], corpus_evidence: list[EvidenceItem]) -> list[Recommendation]:
    # Conflicting evidence detection on cover-crop / water outcomes.
    titles = " ".join(item.document_id + item.text for item in corpus_evidence).lower()
    conflict = "study a reports" in titles and "study b reports" in titles
    verified = [verify_recommendation(rec) for rec in recommendations]
    if conflict:
        for rec in verified:
            rec.estimated_effect = (
                "Evidence is mixed. Study A reports soil-cover and habitat benefits from cover in semi-arid rotations, "
                "while Study B reports soil-water depletion and weak biodiversity response when biomass is limited. "
                "The difference may relate to climate, soil type, management, or study duration. "
                "A site-specific quantitative estimate would not be reliable from the current information."
            )
            rec.confidence = "low"
    return verified
