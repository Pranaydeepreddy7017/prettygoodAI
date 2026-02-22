import time
import argparse
import traceback
from twilio.rest import Client
from config import settings
from scenarios import SCENARIOS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1, help="Number of calls")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between calls")
    parser.add_argument("--scenario", type=str, default="", help="Force one scenario id")
    args = parser.parse_args()

    print("run_calls.py started", flush=True)
    print(f"PUBLIC_BASE_URL = {settings.PUBLIC_BASE_URL}", flush=True)
    print(f"FROM (Twilio #) = {settings.TWILIO_FROM_NUMBER}", flush=True)
    print(f"TO (TEST_LINE)  = {settings.TEST_LINE}", flush=True)

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    scenario_ids = list(SCENARIOS.keys())
    for i in range(args.n):
        scenario = args.scenario if args.scenario in SCENARIOS else scenario_ids[i % len(scenario_ids)]
        url = f"{settings.PUBLIC_BASE_URL}/voice?scenario={scenario}"

        print(f"Creating call {i+1}/{args.n} -> url={url}", flush=True)

        call = client.calls.create(
            to=settings.TEST_LINE,
            from_=settings.TWILIO_FROM_NUMBER,
            url=url,
            method="POST",
            record=True,
            status_callback=f"{settings.PUBLIC_BASE_URL}/status",
            status_callback_event=["initiated", "answered", "completed"],
            status_callback_method="POST",
        )

        print(f"✅ Started call: {call.sid} scenario={scenario}", flush=True)
        time.sleep(args.delay)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("❌ run_calls.py crashed:", flush=True)
        traceback.print_exc()
