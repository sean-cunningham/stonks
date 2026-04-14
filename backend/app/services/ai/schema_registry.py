"""JSON Schema for xAI structured Responses; app validates with Pydantic after parse."""

from app.schemas.event_analysis import EventAnalysisJudgment


def event_judgment_json_schema() -> dict:
    return EventAnalysisJudgment.model_json_schema()


def event_judgment_response_format() -> dict:
    return {
        "type": "json_schema",
        "name": "event_analysis_judgment",
        "schema": event_judgment_json_schema(),
        "strict": True,
    }
