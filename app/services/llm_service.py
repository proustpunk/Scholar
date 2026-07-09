from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_notes(chunks: list, api_key: str) -> str:
    """Send chunks to Groq and generate structured notes."""
    combined_text = "\n\n".join(chunks)

    prompt = f"""You are a study assistant. Read the textbook excerpt below and identify its main concept(s).
Then generate notes using this exact 3-Layer Ladder structure, built entirely around the concept(s) found in the text — do not substitute a different topic.

**Layer 1: The Sticky Analogy** (for beginners)
- A vivid real-world story (not code) illustrating the core dilemma or idea in the text.
- Make it memorable so the fundamental trade-off or principle sticks.

**Layer 2: The Translation** (for non-technical professionals)
- Drop the analogy, translate into the text's actual domain terminology.
- Define the core ideas in plain English first, then formally (with formulas/definitions if the text has them).
- State any inverse trade-offs or tensions explicit in the text.

**Layer 3: The Exam Crib Sheet** (for technical accuracy)
- Exact formulas/definitions from the text, including any derived terms.
- Explain *why* specific methods/operations are used, if the text explains this.
- 2-3 real-world scenarios where this concept applies, grounded in the text.
- 1-2 "gotcha" points a professor might quiz on, if evident from the text.

Stylistic rules:
- Bold headers between layers.
- Paragraphs max 3 sentences.
- Bold the single most important takeaway per layer.
- Format it like actual exam notes.
- Donot tell what method, and structure you are using to give result.

Text:
{combined_text}

Generate the notes now, based only on the text above:"""

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
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
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )

    return response.choices[0].message.content