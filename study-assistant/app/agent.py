import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext, load_artifacts
from google.genai import types


async def upload_study_material(file_path: str, tool_context: ToolContext) -> str:
    """Uploads a local study material file (e.g. PDF, text notes) to the agent session.

    Args:
        file_path: The local absolute or relative path to the PDF book or study notes file.

    Returns:
        A success or error message indicating the upload result.
    """
    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist on disk."

    filename = os.path.basename(file_path)
    lower_path = file_path.lower()

    if lower_path.endswith(".pdf"):
        mime_type = "application/pdf"
    elif lower_path.endswith(".txt"):
        mime_type = "text/plain"
    elif lower_path.endswith(".md"):
        mime_type = "text/markdown"
    else:
        mime_type = "application/octet-stream"

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename, part)
        return (
            f"Success: Uploaded '{filename}' to the session. You can now use "
            f"it to ask questions, generate quizzes, summaries, or explain concepts."
        )
    except Exception as e:
        return f"Error reading or uploading the file: {e}"


async def list_study_materials(tool_context: ToolContext) -> list[str]:
    """Lists the filenames of all uploaded study materials available in the current session.

    Returns:
        A list of names of uploaded study documents.
    """
    return await tool_context.list_artifacts()


SYSTEM_INSTRUCTION = """You are a strict, grounded AI Study Assistant for students. Your goal is to help students learn using ONLY their uploaded study materials (PDFs/notes).

Instructions:
1. Always check the list of available study materials. You must call `load_artifacts` to load the contents of the relevant document(s) before answering any questions about them.
2. Answer the student's questions based ONLY on the loaded study material. Do not use external or pre-trained knowledge to answer questions not present in the documents.
3. If the required information is not present in the loaded material, or if no study material has been uploaded yet, clearly state: "I'm sorry, but I couldn't find that information in the uploaded study material." Never invent or extrapolate answers.
4. When asked to generate quizzes (MCQs, True/False, or Short Questions), generate them based strictly on the loaded material. Provide answers only when requested.
5. When asked to summarize or explain concepts, base your summary/explanation strictly on the material in the uploaded document. Use simple language, clear structure, and helpful analogies, but do not introduce new facts.
6. Keep conversation memory during the current session to ensure a cohesive dialog.
"""

root_agent = Agent(
    name="study_assistant",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_INSTRUCTION,
    tools=[upload_study_material, list_study_materials, load_artifacts],
)

app = App(
    root_agent=root_agent,
    name="app",
)
