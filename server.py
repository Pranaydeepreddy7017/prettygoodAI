from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from config import settings
from scenarios import pick_scenario_id, scenario_prompt
from storage import (
    init_call, load_call, save_call, append_turn, set_status, set_meta, write_transcript_txt
)

import re
from patient_profile import PATIENT
from llm import generate_patient_turn


app = Flask(__name__)

def _gather_listen(action_url: str) -> Gather:
    return Gather(
        input="speech dtmf",
        action=action_url,
        method="POST",
        timeout=15,
        speech_timeout="1",
        language="en-US",
        speech_model="phone_call",
    )



# def rule_based_reply(agent_text: str) -> str | None:
#     t = agent_text.lower().strip()
#     first = PATIENT["full_name"].split()[0].lower()
#     if ("speaking with" in t) or ("am i speaking with" in t):
#         if first in t:
#             return f"Yes, this is {PATIENT['full_name'].split()[0]}."
#         return f"Yes, this is {PATIENT['full_name']}."
    
#     # 1) Confirmation questions
#     if any(p in t for p in ["is that correct", "is this correct", "correct?", "confirm", "let me confirm"]):
#         return "Yes, that’s correct."

#     # 2) Name requests (catch: "full name", "your name", "first and last name")
#     if any(p in t for p in ["full name", "your name", "first and last name", "first name", "last name", "name please"]):
#         return f"My name is {PATIENT['full_name']}."

#     # 3) DOB requests
#     # if any(p in t for p in ["date of birth", "dob", "birth date", "birthday"]):
#     #     return PATIENT["dob_spoken"]

#     def _is_dob_request(t: str) -> bool:
#     # Only treat as DOB request if the agent is asking for it
#         patterns = [
#             r"\b(what is|what's|provide|give|tell|confirm)\b.*\b(date of birth|dob|birthdate|birthday)\b",
#             r"\b(i need|we need|i'll need|can i have|may i have)\b.*\b(date of birth|dob|birthdate|birthday)\b",
#             r"\b(date of birth|dob|birthdate|birthday)\b\s*\?",  # "DOB?"
#         ]
#         return any(re.search(p, t) for p in patterns)
    
#     # DOB (only if requested)
#     if _is_dob_request(t):
#         return PATIENT["dob_spoken"]


#     # 4) Insurance
#     if "insurance" in t:
#         return f"My insurance is {PATIENT['insurance']}."

#     # 5) ZIP / postal code
#     if any(p in t for p in ["zip", "postal code", "zipcode"]):
#         return PATIENT["zip"]

#     # 6) Phone number request (optional)
#     if any(p in t for p in ["phone number", "number you have on file", "call back number"]):
#         # You can either provide a fixed test number, or say you’re not sure.
#         # Pick one:
#         return PATIENT.get("phone", "I’m not sure what number is on file.")

#     return None


@app.get("/health")
def health():
    return {"ok": True}


@app.route("/voice", methods=["GET", "POST"])
def voice():
    call_sid = request.values.get("CallSid")
    scenario_id = pick_scenario_id(request.args.get("scenario"))
    scenario_text = scenario_prompt(scenario_id)

    if call_sid and not load_call(call_sid):
        init_call(call_sid, scenario_id, scenario_text)

    resp = VoiceResponse()
    resp.pause(length=2)
    
    # Listens first 
    action_url = f"{settings.PUBLIC_BASE_URL}/gather"
    resp.append(_gather_listen(action_url))
    resp.redirect(f"{action_url}?empty=1", method="POST")

    return str(resp)

def ensure_call_initialized(call_sid: str) -> dict:
    state = load_call(call_sid)
    if not state:
        scenario_id = pick_scenario_id(None)
        scenario_text = scenario_prompt(scenario_id)
        return init_call(call_sid, scenario_id, scenario_text)

    #
    if "scenario_text" not in state or "scenario_id" not in state:
        scenario_id = state.get("scenario_id") or pick_scenario_id(None)
        scenario_text = scenario_prompt(scenario_id)
        state["scenario_id"] = scenario_id
        state["scenario_text"] = scenario_text
        save_call(state)

    return state


@app.route("/gather", methods=["POST"])
def gather():
    call_sid = request.values.get("CallSid")
    if not call_sid:
        return "Missing CallSid", 400

    state = ensure_call_initialized(call_sid)

    agent_text = (request.values.get("SpeechResult") or "").strip()
    digits = (request.values.get("Digits") or "").strip()

    if agent_text:
        append_turn(call_sid, "agent", agent_text)
        print(f"\n[CALL {call_sid}] AGENT: {agent_text}", flush=True)

    if digits:
        append_turn(call_sid, "agent", f"[DTMF] {digits}")
        print(f"\n[CALL {call_sid}] AGENT_DTMF: {digits}", flush=True)

        # --- IGNORE COMPLIANCE / RECORDING MESSAGES ---
    if agent_text:
        lower = agent_text.lower()
        compliance_phrases = [
            "recorded",
            "quality",
            "training purposes",
            "quality assurance",
        ]

        if any(p in lower for p in compliance_phrases):
            print(f"[CALL {call_sid}] Ignoring compliance message: {agent_text}", flush=True)

            # Just listen again, don't respond
            resp = VoiceResponse()
            action_url = f"{settings.PUBLIC_BASE_URL}/gather"
            resp.append(_gather_listen(action_url))
            resp.redirect(f"{action_url}?empty=1", method="POST")
            return str(resp)
        
    def looks_incomplete(t: str) -> bool:
        t = t.strip().lower()
        if len(t) < 12:
            return True
        if t.endswith(("and", "but", "so", "because", "to", "for", "with")):
            return True
        if not any(p in t for p in ["?", "please", "can you", "could you", "what", "when", "where", "dob", "date of birth"]):
            # no clear question/ask detected
            return True
        return False

    if agent_text and looks_incomplete(agent_text):
        # just listen again instead of replying and interrupting
        resp = VoiceResponse()
        action_url = f"{settings.PUBLIC_BASE_URL}/gather"
        resp.append(_gather_listen(action_url))
        resp.redirect(f"{action_url}?empty=1", method="POST")
        return str(resp)


    # reload after appending turns
    state = ensure_call_initialized(call_sid)
    turns = state.get("turns", [])


    max_pairs = settings.MAX_TURNS * 2
    resp = VoiceResponse()

    if len(turns) >= max_pairs:
        closing = "Thanks, that’s all I needed. Bye."
        append_turn(call_sid, "patient", closing)
        print(f"[CALL {call_sid}] PATIENT: {closing}\n", flush=True)
        resp.say(closing)
        resp.hangup()
        return str(resp)

    patient_text = None
    # if agent_text:
    #     patient_text = rule_based_reply(agent_text)

    if not patient_text:
        patient_text = generate_patient_turn(state["scenario_text"], turns)
    
    patient_text = patient_text.strip()
    if patient_text.lower().startswith("patient:"):
        patient_text = patient_text.split(":", 1)[1].strip()
    
    patient_text = re.sub(r"\[\s*your name\s*\]", PATIENT["full_name"], patient_text, flags=re.I)
    patient_text = re.sub(r"\{\s*your name\s*\}", PATIENT["full_name"], patient_text, flags=re.I)


    if patient_text.strip() == "<END_CALL>":
        closing = "Thanks, that answers my question. Bye."
        append_turn(call_sid, "patient", closing)
        print(f"[CALL {call_sid}] PATIENT: {closing}\n", flush=True)
        resp.say(closing)
        resp.hangup()
        return str(resp)

    append_turn(call_sid, "patient", patient_text)
    print(f"[CALL {call_sid}] PATIENT: {patient_text}\n", flush=True)
    resp.say(patient_text)

    action_url = f"{settings.PUBLIC_BASE_URL}/gather"
    resp.append(_gather_listen(action_url))
    resp.redirect(f"{action_url}?empty=1", method="POST")
    return str(resp)



@app.route("/status", methods=["POST"])
def status():
    call_sid = request.values.get("CallSid")
    call_status = request.values.get("CallStatus")  # initiated/answered/completed, etc.

    if call_sid:
        set_status(call_sid, call_status)
        set_meta(call_sid, twilio_call_status=call_status)

        if call_status == "completed":
            try:
                write_transcript_txt(call_sid)
            except Exception:
                pass

    return ("", 204)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
