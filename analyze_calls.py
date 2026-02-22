from pathlib import Path
from storage import load_call, REPORTS_DIR
from llm import analyze_transcript

def main():
    calls_dir = Path("data/calls")
    out_md = []

    for p in sorted(calls_dir.glob("*.json")):
        call_sid = p.stem
        state = load_call(call_sid)
        if not state or not state.get("turns"):
            continue

        issues = analyze_transcript(state["scenario_text"], state["turns"])
        out_md.append(f"## Call {call_sid}")
        out_md.append(f"**Scenario:** {state.get('scenario_id')}")
        out_md.append("")
        out_md.append(issues)
        out_md.append("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "bug_report.md"
    report_path.write_text("\n".join(out_md), encoding="utf-8")
    print(f"Wrote {report_path}")

if __name__ == "__main__":
    main()
