import requests
import uuid

APP_URL = "https://decider-agent-195472357560.us-central1.run.app"  # Replace with your deployed URL
TOKEN = None  # Set your identity token here if authentication is enabled, else None

HEADERS = {
    "Content-Type": "application/json"
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def call_agent(message_text, user_id="test_user", session_id=None):
    payload = {
        "app_name": "decider_agent",
        "user_id": user_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message_text}]
        },
        "streaming": False
    }
    if session_id:
        payload["session_id"] = session_id

    response = requests.post(f"{APP_URL}/run_sse", json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def main():
    # Start new workflow
    session_id = None
    start_text = "start; Analyze the requirements for a hospital patient management login flow"
    print("Starting workflow...")
    resp = call_agent(start_text)
    session_id = resp.get("session_id")
    print("Response:", resp)

    # Approve the analysis
    if session_id:
        approve_text = f"approved; ; {session_id}"
        print("\nApproving analysis...")
        resp = call_agent(approve_text, session_id=session_id)
        print("Response:", resp)

    # Optionally, test editing
    edit_text = f"edited; Added MFA requirements to analysis; {session_id}"
    print("\nEditing analysis...")
    resp = call_agent(edit_text, session_id=session_id)
    print("Response:", resp)

    # Reject scenario
    reject_text = f"rejected; ; {session_id}"
    print("\nRejecting analysis...")
    resp = call_agent(reject_text, session_id=session_id)
    print("Response:", resp)


if __name__ == "__main__":
    main()
