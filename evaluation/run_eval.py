from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

CASES = json.loads((Path(__file__).resolve().parents[1] / "evaluation" / "cases.json").read_text(encoding="utf-8"))


def evaluate() -> dict:
    report = {"n": len(CASES["cases"]), "passed": 0, "details": []}
    with TestClient(app) as client:
        for case in CASES["cases"]:
            payload = {"message": case.get("query") or json.dumps(case.get("input") or {}), "environment": case.get("input")}
            data = client.post("/api/v1/agent/query", json=payload).json()
            expect = case["expect"]
            ok = False
            if expect == "clarifying questions":
                ok = data["status"] == "clarification_required"
            elif "multi-variable" in expect or "reasoning" in expect:
                ok = data["status"] in {"recommendation_ready", "clarification_required"}
                if data.get("reasoning"):
                    ok = len(data["reasoning"].get("activated_variables") or []) >= 2
            elif "uncertainty" in expect or "abstention" in expect:
                blob = json.dumps(data).lower()
                ok = "cannot be estimated" in blob or "insufficient" in blob or "mixed" in blob or data["status"] == "insufficient_evidence"
            report["details"].append({"id": case["id"], "ok": ok, "status": data.get("status")})
            report["passed"] += int(ok)
    return report


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2))
