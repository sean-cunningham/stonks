"""Ensure live order routing stays confined to the stub adapter."""

from pathlib import Path


def test_place_live_only_on_future_stub_adapter():
    app_root = Path(__file__).resolve().parents[1] / "app"
    hits: list[Path] = []
    for path in sorted(app_root.rglob("*.py")):
        rel = path.relative_to(app_root)
        if rel.as_posix() == "services/execution/live_adapter_stub.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "place_live" in text:
            hits.append(path)
    assert hits == [], f"place_live referenced outside stub: {hits}"
