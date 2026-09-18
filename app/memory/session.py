from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EnvironmentalObservation, EnvironmentalStateRecord, Message
from app.db.models import Session as SessionModel
from app.memory.environmental_state import merge_states
from app.schemas.environment import EnvironmentalState


class SessionMemory:
    def create_session(self, db: Session, title: str | None = None) -> str:
        session_id = str(uuid.uuid4())
        db.add(SessionModel(session_id=session_id, title=title or "Biodiversity consultation"))
        db.add(
            EnvironmentalStateRecord(
                session_id=session_id,
                state_json=EnvironmentalState().model_dump(),
            )
        )
        db.commit()
        return session_id

    def get_or_create(self, db: Session, session_id: str | None) -> str:
        if session_id:
            existing = db.get(SessionModel, session_id)
            if existing:
                return session_id
        return self.create_session(db)

    def load_state(self, db: Session, session_id: str) -> EnvironmentalState:
        record = (
            db.query(EnvironmentalStateRecord)
            .filter(EnvironmentalStateRecord.session_id == session_id)
            .one_or_none()
        )
        if not record:
            return EnvironmentalState()
        return EnvironmentalState.model_validate(record.state_json)

    def save_state(self, db: Session, session_id: str, state: EnvironmentalState) -> None:
        record = (
            db.query(EnvironmentalStateRecord)
            .filter(EnvironmentalStateRecord.session_id == session_id)
            .one_or_none()
        )
        payload = state.model_dump()
        if record is None:
            record = EnvironmentalStateRecord(session_id=session_id, state_json=payload)
            db.add(record)
            db.flush()
        else:
            record.state_json = payload
        db.query(EnvironmentalObservation).filter(
            EnvironmentalObservation.state_id == record.state_id
        ).delete()
        for path, obs in state.known_paths().items():
            db.add(
                EnvironmentalObservation(
                    state_id=record.state_id,
                    path=path,
                    value_json=obs.model_dump(),
                )
            )
        db.commit()

    def add_message(
        self, db: Session, session_id: str, role: str, content: str, payload: dict[str, Any] | None = None
    ) -> None:
        db.add(Message(session_id=session_id, role=role, content=content, payload=payload))
        db.commit()

    def messages(self, db: Session, session_id: str) -> list[Message]:
        return (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.message_id.asc())
            .all()
        )

    def apply_update(self, current: EnvironmentalState, incoming: EnvironmentalState) -> EnvironmentalState:
        return merge_states(current, incoming)
