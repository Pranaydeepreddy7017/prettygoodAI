from openai import OpenAI
from config import settings
from patient_profile import PATIENT
client = OpenAI()

SYSTEM_PATIENT = """You are roleplaying as a REAL patient calling a medical office.
Be natural and realistic. Keep each turn short (1–2 sentences).
Do NOT mention you are an AI or that this is a test.
Never change your identity: do not change your name or date of birth.
If the conversation is complete, output exactly: <END_CALL>
"""


def _format_history(turns: list[dict], max_turns: int = 12) -> str:
    trimmed = turns[-max_turns:]
    out = []
    for t in trimmed:
        role = "Agent" if t["speaker"] == "agent" else "Patient"
        out.append(f"{role}: {t['text']}")
    return "\n".join(out)

def generate_patient_turn(scenario_text: str, turns: list[dict]) -> str:
    history = _format_history(turns)
    identity = f"""You are this patient:
- Full name: {PATIENT['full_name']}
- Date of birth: {PATIENT['dob_spoken']}
- ZIP: {PATIENT['zip']}
- Insurance: {PATIENT['insurance']}
Rules:
- Always keep the same identity (do NOT change your name/DOB).
- Do NOT invent a different name.
"""

    user_prompt = f"""Scenario:
{scenario_text}


Conversation so far:
{history}

Write the patient's next line now."""
    try:
        resp = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PATIENT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # 🔒 NEVER crash the call
        print("LLM ERROR (fallback used):", e, flush=True)
        return "Sorry, could you repeat that?"


SYSTEM_QA = """You are evaluating a phone agent. Find bugs/quality issues:
- ignore the first two turns (they are usually just greetings and not important) 
-DO NOT FOCUS ON SIMPLE ISSUES AND DO NOT NITPICK GRAMMAR OR SPELLING MISTAKES THEY ARE NOT IMPORTANT. 
- focus on the agent's responses which should be helpful, accurate, and relevant to the patient's needs
- identify if the patient's intent is not being addressed
- identify if the patient is inconsistent or confused (e.g., they ask for a date change but the agent doesn't follow)
- identify incorrect info, hallucinations, misunderstandings
- awkward or unsafe phrasing
- failure to answer, loops, contradictions
Return a concise bullet list. If none, say: "No obvious issues found."""

def analyze_transcript(scenario_text: str, turns: list[dict]) -> str:
    history = _format_history(turns, max_turns=999)
    prompt = f"""Scenario:
{scenario_text}

Transcript:
{history}

List issues in the AGENT responses (not the patient)."""
    resp = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_QA},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
