import random

SCENARIOS = {

    # "appt_schedule": (
    #     "You need to schedule a new appointment for your wife for march 2nd monday 2pm. give details register and book an appointment. You have mild symptoms of cold and fever and want the earliest available slot."
    # ),
    "schedule_new_appointment":(
        "You need to schedule a new appointment- any time works, just a regular checkup. no constraints on date/time."
    ) ,
    #"double_booking":(
    #   "You have an existing appointment scheduled for Monday, March 2nd at 11:00 AM. You are calling to schedule an additional appointment for your wife, who is not available on Mondays. Ask the agent for nearby alternative dates that would allow both appointments to be scheduled on the same day within a two-hour time window. Evaluate whether the agent correctly maintains your existing appointment, clearly distinguishes it from the new booking request, and avoids overwriting or confusing the two appointments."
    # ),
    
    #   "barge_in": (
    #          "You are trying to schedule an appointment. Even before the agents says how can i help you, interrupt and ask details about stress test preparation. and wait and see if the agent asks for our details or appointment details"
    # ),

    # "impatient_caller": (
    #     "you are in hurry and want to reschedule  an existing appointment to a later date, give your name and date of birth in the first turn itself even before the agent asks and ask to reschedule like you are in a hurry"
    # ),

    # "date_confusion": (
    #     "After confirming an appointment date, ask something else, later mention a different appointment date from original casually."),
    #     "reschedule": (
    #     "You already have a confirmed appointment on February 26th at 2:15 p.m. "
    #     "You need to reschedule it to the first week of March due to a conflict. "
    #     "Do not cancel the appointment unless explicitly asked. "
    #     "Try to keep the same provider if possible."
    # ),

    #     "self_correction_date_time": (
    #     "You already have a confirmed appointment on  Tuesday, March 3rd at 12:00 p.m "
    #     "You need to reschedule it. During the conversation, intentionally self-correct like a real person. "
    #     "For example: say 'Can we do next wednesday—actually Thursday?' and later '2 PM—sorry, make that 12 PM.' "
    #     "Speak naturally. The goal is to see whether the agent correctly updates the appointment and "

    #     "Do not end the call until the rescheduling is fully confirmed with the new date and time."
    # ),

    #     "self_correction_delayed": (
    #     "You already have a confirmed appointment on Tuesday, March 3rd at 12:00 p.m. "
    #     "You want to reschedule it. First, ask to move it to wednesday, March 4th at 12:00 p.m. "
    #     "Let the agent confirm this new date/time. "
    #     "if there are no options look for the next closest date"
    #     "After two or three additional conversational turns (e.g., asking what to bring or parking), "
    #     "correct yourself and say you actually meant 2:00 p.m. (lets see if they remember wednesday March 4th or if they get confused)"
    #     "Speak naturally. Do not end the call until the agent clearly confirms the FINAL date and time."
    # ),
    #     "date_inconsistency_after_confirm": (
    #         "Goal: reschedule an appointment to march 5rd thursday and obtain a final confirmed date/time from the agent. "
    #         "Do NOT end the call AFTER the agent states a confirmed date/time. "
    #         "After the agent confirms the date/time, ask two more unrelated question (e.g., what to bring), "
    #         "then casually mention a DIFFERENT date/day as if you believe that's the appointment "
    #         "(e.g., 'Perfect, I’ll be there Friday March 6th'). "
    #         "Wait to see if the agent catches and corrects the inconsistency."
    #     ),    

    # "call_drop": (
    #     "You are trying to schedule an appointment. After providing your details and confirming the appointment date, say that you couldnt hear them and ask again")
        
    # "reschedule": (
    #     "You already have an appointment for February 26th at 2:15 p.m but need to reschedule to first week of march due to a conflict."
    #  ),
    # "cancel": (
    #     "You want to cancel an appointment and ask if there is any cancellation fee or policy."
    # ),
    # "med_refill": (
    #     "You need a medication refill. You ran out and want to know the process and expected timeline."
    # ),
    # "hours_location_insurance": (
    #     "You have general questions: office hours, location, and whether your insurance is accepted."
    # ),

    # "edge_case": (
    #     "Stress test: give incomplete info, ask multiple questions at once, and ask for clarification if they are vague."
    # ),

    #     "enquire_office_hours": (
    #         "You want to know the office hours for the upcoming week and doctor appointments availability for next week"
    #     ),
}

def pick_scenario_id(requested: str | None) -> str:
    if requested and requested in SCENARIOS:
        return requested
    return random.choice(list(SCENARIOS.keys()))

def scenario_prompt(scenario_id: str) -> str:
    if scenario_id in SCENARIOS:
        return SCENARIOS[scenario_id]
    # fallback: return the first scenario prompt (works even if you comment others)
    return next(iter(SCENARIOS.values()))

