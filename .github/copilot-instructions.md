# AI Coding Agent Instructions for PrettyGoodAI

## Project Overview
PrettyGoodAI is a **voice-based phone agent simulator** that tests medical office receptionist workflows. Real agents call the system via Twilio, and the system responds with an AI-generated patient (or rule-based fallback) to simulate realistic phone conversations. After calls complete, transcripts are analyzed for quality issues.

## Architecture: Core Data Flow
```
Twilio (inbound call)
  ↓
server.py (/voice, /gather endpoints)
  ├→ load scenario (scenarios.py)
  ├→ persist call state (storage.py)
  ├→ patient response: rule-based (server.py) → LLM (llm.py)
  └→ speak response back via TwiML
```

**Key insight:** Call state is **JSON files on disk** (one per CallSid), not a database. Each endpoint loads/appends/saves synchronously.

## Critical Components

### `storage.py` — The Single Source of Truth
- Stores all call state in `data/calls/{call_sid}.json`
- Structure: `{call_sid, scenario_id, scenario_text, created_at, status, turns[], meta{}}`
- **Pattern:** `load_call()` → mutate → `save_call()`. No in-memory state.
- Transcripts written to `transcripts/{call_sid}.txt` on call completion
- **When adding features:** Always update storage.py first to add fields

### `server.py` — Request Handling & Orchestration
- `/voice` (GET/POST): Entry point, initializes call, first gather action
- `/gather` (POST): Receives agent speech/DTMF, generates patient response, continues conversation
- `/status` (POST): Webhook for Twilio call lifecycle events (answered/completed)
- **Key function:** `rule_based_reply()` — quick pattern matching for verification data (name, DOB, insurance)
  - Returns immediate response or None to trigger LLM
  - Examples: detects "date of birth", returns `PATIENT["dob_spoken"]`
  - **Modify here first** before adding expensive LLM calls

### `llm.py` — AI-Powered Patient & QA
- `generate_patient_turn()`: Uses OpenAI to generate next patient utterance
  - Takes scenario + conversation history, trims to last 12 turns
  - Responds with `<END_CALL>` when patient is satisfied (explicit termination)
- `analyze_transcript()`: QA analysis—finds bugs/hallucinations in agent responses
  - Lower temperature (0.2) for consistency
- **System prompts are hardcoded** (not in config)—update them in llm.py, not elsewhere

### `config.py` — Central Configuration
- All settings use `os.getenv()` with sensible defaults
- **MODEL_NAME is the single source of truth** for LLM model
- **Important:** Missing env vars will crash—check PUBLIC_BASE_URL, TWILIO_* secrets before running

### `scenarios.py` — Test Scenarios
- 6 predefined scenarios (appt_schedule, reschedule, cancel, med_refill, hours_location_insurance, edge_case)
- Scenario picked randomly or by query parameter: `/voice?scenario=reschedule`
- **To add new scenarios:** Add to SCENARIOS dict, that's it (no database)

## Developer Workflows

### Running the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export PUBLIC_BASE_URL=https://your-ngrok-url.ngrok.io
export TWILIO_ACCOUNT_SID=...
export TWILIO_AUTH_TOKEN=...
export TWILIO_FROM_NUMBER=+1...

# Run Flask dev server (auto-reloads, debug mode on)
python server.py
```

### Simulating Calls Locally
- Use Twilio's test voice capabilities or call your `/voice` endpoint with a mock CallSid
- Check `data/calls/` for JSON state files
- Check `transcripts/` for text transcripts (written only on call completion)

### Missing File: `patient_profile.py`
- Imported in server.py but **does not exist** — needs to be created
- Should define `PATIENT` dict with fields: `dob_spoken`, `full_name`, `zip`, `insurance`, `is_existing_patient`
- Example:
  ```python
  PATIENT = {
      "full_name": "Alice Johnson",
      "dob_spoken": "March 5th, 1990",
      "zip": "90210",
      "insurance": "Blue Cross",
      "is_existing_patient": True,
  }
  ```

## Patterns & Conventions

### Turn Representation
All turns stored as `{"speaker": "agent"|"patient", "text": str, "ts": ISO8601 timestamp}`
- **speaker names are lowercase** (not "AGENT"/"PATIENT")
- Logging uses uppercase for readability

### LLM Temperature Settings
- Patient generation: **0.7** (natural variation, mistakes allowed)
- QA analysis: **0.2** (consistent, factual evaluation)

### Call Termination
Two explicit signals:
1. **LLM returns `<END_CALL>`** → closes call gracefully
2. **Turn count exceeds MAX_TURNS** → closes call immediately
- Both cases say goodbye via TTS and hangup

### Guardrail Pattern: Rule-Based First
The `rule_based_reply()` function demonstrates the design philosophy: **avoid LLM for simple, deterministic responses**. Before expanding LLM usage, check if rule-based matching works.

## Integration Points

### Twilio Voice Webhooks
- **Input:** `SpeechResult` (STT), `Digits` (DTMF), `CallSid`, `CallStatus`
- **Output:** TwiML (XML) via VoiceResponse
- **Model:** `phone_call` speech model, 8s timeout, auto speech timeout
- Callback chain: `/voice` → `/gather` → `/gather` (loop) → `/status` (lifecycle)

### OpenAI API
- Called only when rule-based reply fails
- Model configured via `settings.MODEL_NAME` (change in one place)
- Uses chat completions API, not legacy completions

## Testing & Debugging
- **Print statements** are intentional (flush=True for real-time logging)
- Enable Flask debug mode for auto-reload
- Check call state JSON files directly: `cat data/calls/CallSid.json | jq`
- Review transcripts in `transcripts/` for QA analysis patterns

## Common Modifications

| Need | Where |
|------|-------|
| Change LLM model | `config.py` (MODEL_NAME env var) |
| Add verification field | `patient_profile.py` + `rule_based_reply()` |
| New scenario | `scenarios.py` (SCENARIOS dict) |
| System prompt tuning | `llm.py` (SYSTEM_PATIENT or SYSTEM_QA) |
| Call length limit | `config.py` (MAX_TURNS) |
| Conversation history window | `llm.py` (_format_history max_turns param) |

---

**Last updated:** 2026-02-16
