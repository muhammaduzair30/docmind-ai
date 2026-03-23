import os
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger("docmind_sys")

_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key or _api_key == "PASTE_YOUR_NEW_API_KEY_HERE":
    logger.warning("GEMINI_API_KEY is not set or still has the placeholder value. "
                   "Please set a valid key in your .env file.")

client = genai.Client(api_key=_api_key)


def generate_answer(question: str, chunks: list[str]) -> str:

    if not chunks:
        return "No relevant information found in the documents."

    context = "\n\n".join(str(c) for c in chunks)

    prompt = f"""
You are an AI assistant that answers questions using ONLY the provided context.

Context:
{context}

Question:
{question}

If the answer is not in the context, respond:
"The document does not contain this information."
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.2},
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"AI model error: {e}") from e