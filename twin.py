import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# --------------------------------------------------
# Setup
# --------------------------------------------------

load_dotenv()

key = os.getenv("GOOGLE_API_KEY")
model = os.getenv("MODEL")

if not key:
    raise ValueError("GOOGLE_API_KEY is missing from .env")

if not model:
    raise ValueError("MODEL is missing from .env")

google_Client = genai.Client(api_key=key)

BASE_DIR = Path(__file__).resolve().parent


# --------------------------------------------------
# Tool 1: Save visitor details
# --------------------------------------------------

def record_user_details_tool(
    email: str,
    name: str = "Name not provided",
    notes: str = "not provided",
) -> str:
    """Save visitor contact details to a text file."""

    file_path = BASE_DIR / "user_details.txt"

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(
            f"Date: {datetime.now()}\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Notes: {notes}\n"
            f"{'-' * 50}\n"
        )

    return "User details recorded successfully."


# --------------------------------------------------
# Tool 2: Save unanswered questions
# --------------------------------------------------

def record_unknown_question_tool(question: str) -> str:
    """Save a question the digital twin cannot answer."""

    file_path = BASE_DIR / "unknown_questions.txt"

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(
            f"Date: {datetime.now()}\n"
            f"Question: {question}\n"
            f"{'-' * 50}\n"
        )

    return "Unknown question recorded successfully."


# --------------------------------------------------
# Chat function
# --------------------------------------------------

def chat(message, history, twin_context):

    system_prompt = f"""
    You are a digital twin representing the person described below.

    You are chatting with visitors on this person's website.

    Answer questions about the person's career, background, skills,
    work experience, education, projects, and achievements.

    If asked, explain that you are an AI digital twin.

    Be professional, friendly, and engaging.

    Do not invent information or make unsupported claims.

    If you cannot answer a professional question using the supplied
    information, call record_unknown_question_tool with the user's
    question. Then politely explain that you do not know the answer.

    If a visitor voluntarily provides their email address, call
    record_user_details_tool with their email, name if available,
    and relevant notes.

    Do not ask for contact details unnecessarily.

    Never claim that information was saved unless the tool succeeds.

    Person's uploaded information:

    {twin_context}
    """

    # Add user message to history
    history.append(
        types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )
    )

    # Send conversation to Gemini
    response = google_Client.models.generate_content(
        model=model,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[
                record_user_details_tool,
                record_unknown_question_tool,
            ],
        ),
    )

    answer = response.text or "I couldn't generate a response."

    # Save Gemini response to history
    if response.candidates:
        model_content = response.candidates[0].content

        if model_content:
            history.append(model_content)

    return answer