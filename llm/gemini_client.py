import os
import google.generativeai as genai
from core.config import settings

genai.configure(api_key=settings.gemini_api_key)

def call_gemini(prompt:str,model:str="gemini-1.5-flash")->str:
    llm = genai.GenerativeModel(model_name=model)
    response = llm.generate_content(prompt)
    return response.text.strip()


