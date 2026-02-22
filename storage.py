import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data/calls")
TRANSCRIPT_DIR = Path("transcripts")
REPORTS_DIR = Path("reports")

for d in [DATA_DIR, TRANSCRIPT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def call_path(call_sid: str) -> Path:
    return DATA_DIR / f"{call_sid}.json"

def load_call(call_sid: str) -> dict | None:
    p = call_path(call_sid)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def save_call(state: dict) -> None:
    call_path(state["call_sid"]).write_text(json.dumps(state, indent=2), encoding="utf-8")

def init_call(call_sid: str, scenario_id: str, scenario_text: str) -> dict:
    state = {
        "call_sid": call_sid,
        "scenario_id": scenario_id,
        "scenario_text": scenario_text,
        "created_at": _now_iso(),
        "status": "in_progress",
        "turns": [],  # list of {speaker, text, ts}
        "meta": {},
    }
    save_call(state)
    return state

def append_turn(call_sid: str, speaker: str, text: str) -> dict:
    state = load_call(call_sid) or {"call_sid": call_sid, "turns": [], "meta": {}}
    state.setdefault("turns", [])
    state["turns"].append({"speaker": speaker, "text": text, "ts": _now_iso()})
    save_call(state)
    return state

def set_meta(call_sid: str, **kwargs) -> dict:
    state = load_call(call_sid) or {"call_sid": call_sid, "turns": [], "meta": {}}
    state.setdefault("meta", {})
    state["meta"].update(kwargs)
    save_call(state)
    return state

def set_status(call_sid: str, status: str) -> dict:
    state = load_call(call_sid) or {"call_sid": call_sid, "turns": [], "meta": {}}
    state["status"] = status
    save_call(state)
    return state

def write_transcript_txt(call_sid: str) -> Path:
    state = load_call(call_sid)
    if not state:
        raise ValueError(f"No call state for {call_sid}")

    lines = []
    lines.append(f"CallSid: {call_sid}")
    lines.append(f"Scenario: {state.get('scenario_id')} - {state.get('scenario_text')}")
    lines.append(f"Status: {state.get('status')}")
    lines.append("")

    for t in state.get("turns", []):
        who = "AGENT" if t["speaker"] == "agent" else "PATIENT"
        lines.append(f"[{who}] {t['text']}")

    out = TRANSCRIPT_DIR / f"{call_sid}.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
