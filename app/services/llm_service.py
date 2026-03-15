import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"temperature": 0.2},
    )

    return response.text