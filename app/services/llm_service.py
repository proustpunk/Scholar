from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_notes(chunks: list) -> str:
    """Send chunks to Groq and generate structured notes."""
    combined_text = "\n\n".join(chunks)

    prompt = f"""You are a study assistant. Based on the following text from a textbook, 
generate clear, structured notes that a student can use to study.

Format the notes with:
- Main topics as headings
- Key concepts as bullet points
- Important definitions clearly labeled
- Any formulas or examples included

Text:
{combined_text}

Generate the notes now:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )

    return response.choices[0].message.content

def answer_question(question: str, context: str) -> str:
    """Answer a question based on provided context."""
    prompt = f"""You are a study assistant. Answer the following question based only on the provided context.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )

    return response.choices[0].message.content