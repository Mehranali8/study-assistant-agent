import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

# Import the Study Assistant app
from app.agent import app as adk_app



async def run_query(runner, session_id, user_id, query_text):
    print(f"\n--- User Query: {query_text} ---")
    new_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query_text)]
    )
    
    # Process output events
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message
    ):
        if event.partial:
            continue
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="")
        # If there are function calls, print them
        function_calls = event.get_function_calls()
        if function_calls:
            for fc in function_calls:
                print(f"\n[Tool Call: {fc.name} with args {fc.args}]")
    print()
    await asyncio.sleep(15)



async def main():
    # Write a temporary notes.txt file for testing
    notes_content = (
        "Mascot Info: The mascot of the Kaggle AI Agents Capstone is a friendly little robot helper named 'Kaggley'. "
        "Kaggley loves to help students with coding assignments and study guides.\n"
        "Speed of Light: The speed of light in a vacuum is exactly 299,792,458 meters per second."
    )
    notes_path = "notes.txt"
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(notes_content)
    print(f"Created temporary file '{notes_path}' for testing.")

    # Initialize the Runner with in-memory services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    runner = Runner(
        app=adk_app,
        session_service=session_service,
        artifact_service=artifact_service,
        auto_create_session=True,
    )
    
    session_id = "test-session-123"
    user_id = "student-mehran"

    try:
        # Test 1: Ask a question before uploading any documents
        await run_query(
            runner, session_id, user_id,
            "Who is the mascot of the Kaggle Agents capstone?"
        )
        
        # Test 2: Upload the local notes file
        abs_notes_path = os.path.abspath(notes_path)
        await run_query(
            runner, session_id, user_id,
            f"Please upload the study material at '{abs_notes_path}'"
        )
        
        # Test 3: List study materials to verify
        await run_query(
            runner, session_id, user_id,
            "List my uploaded study materials."
        )

        # Test 4: Ask grounded question
        await run_query(
            runner, session_id, user_id,
            "Who is the mascot of the Kaggle Agents capstone and what do they do?"
        )

        # Test 5: Ask ungrounded question (not in document)
        await run_query(
            runner, session_id, user_id,
            "What is the height of Mount Everest?"
        )

        # Test 6: Generate quiz
        await run_query(
            runner, session_id, user_id,
            "Generate a 1-question True/False quiz about the speed of light based on the uploaded notes."
        )

    finally:
        # Clean up temporary test file
        if os.path.exists(notes_path):
            os.remove(notes_path)
            print(f"\nRemoved temporary file '{notes_path}'.")


if __name__ == "__main__":
    asyncio.run(main())
