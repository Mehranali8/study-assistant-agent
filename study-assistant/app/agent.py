import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext, load_artifacts
from google.genai import types


async def upload_study_material(file_path: str, tool_context: ToolContext) -> str:
    """Uploads a local study material file (PDF, TXT, MD) to the current session."""

    # Clean input
    file_path = file_path.strip().replace('"', "").replace("'", "")

    # Resolve relative path from this file's directory
    if not os.path.isabs(file_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, file_path)

    file_path = os.path.abspath(file_path)

    # DEBUG
    print("=" * 60)
    print("DEBUG FILE PATH:", file_path)
    print("FILE EXISTS:", os.path.exists(file_path))
    print("=" * 60)

    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist on disk."

    filename = os.path.basename(file_path)

    ext = os.path.splitext(filename)[1].lower()

    mime_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }

    mime_type = mime_types.get(ext, "application/octet-stream")

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )

        await tool_context.save_artifact(filename, part)

        return (
            f"Success! '{filename}' uploaded successfully.\n"
            f"You can now ask questions, summaries, explanations, MCQs, "
            f"True/False, or Short Questions from this document."
        )

    except Exception as e:
        return f"Upload failed:\n{str(e)}"


async def list_study_materials(tool_context: ToolContext) -> list[str]:
    """Lists uploaded study material."""
    return await tool_context.list_artifacts()


SYSTEM_INSTRUCTION = """
You are a strict AI Study Assistant.

Rules:
1. Answer ONLY from uploaded study material.
2. Always load uploaded artifacts before answering.
3. If no study material exists, clearly ask the user to upload one.
4. Generate quizzes ONLY from uploaded material.
5. Never invent information.
"""


root_agent = Agent(
    name="study_assistant",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        upload_study_material,
        list_study_materials,
        load_artifacts,
    ],
)


app = App(
    root_agent=root_agent,
    name="app",
)