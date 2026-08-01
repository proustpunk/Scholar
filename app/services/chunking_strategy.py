import os
from app.core.config import settings
from groq import Groq

client = Groq(api_key=settings.GROQ_API_KEY)

def get_model_context_window(model_id):

    try:
        model_info = client.models.retrieve(model_id)
        return model_info.context_window
    except Exception as e:

        print(f"Error {e}")
        return -1


gpt_oss_ctx = get_model_context_window("openai/gpt-oss-120b")
qwen_ctx = get_model_context_window("qwen/qwen3.6-27b") # Note: check the exact model ID

print(f"GPT-OSS 120B Context Window: {qwen_ctx}")