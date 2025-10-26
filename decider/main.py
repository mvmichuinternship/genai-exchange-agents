import asyncio
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import decider_agent  # Your fixed agent

async def run_decider_session():
    """
    Simple interactive runner for Decider.
    """
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="decider", user_id="local")

    print("Decider Started! Type 'quit' to exit.\n")

    try:
        while True:
            user_message = input("You: ").strip()
            if user_message.lower() in ['quit', 'exit', 'q']:
                break
            if not user_message:
                continue

            # Use string message (ADK Agent supports direct str; fallback to Content)
            try:
                async for event in decider_agent.async_stream_query(
                    user_id="local",
                    session_id=session.id,
                    message=user_message  # Direct str (simpler)
                ):
                    if hasattr(event, 'content') and event.content.parts:
                        text = event.content.parts[0].text
                        print(f"Decider: {text}", end="", flush=True)
                    else:
                        print(f"[Event: {getattr(event, 'event_type', 'unknown')}]", end="")
                print("\n" + "="*50)
            except Exception as e:
                print(f"Invocation error: {e}")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Sync delete (no await)
        session_service.delete_session(session.id)

if __name__ == "__main__":
    asyncio.run(run_decider_session())
