import os
import json
import re
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from typing import List

from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

MODEL = Config.GEMINI_MODEL

def _call_gemini_direct(model, prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text if hasattr(response, "text") else str(response)

def _truncate_text(text: str, limit: int = 50000) -> str:
    return text if len(text) <= limit else text[:limit]

def extract_concepts_from_text(text: str) -> dict:
    truncated_text = _truncate_text(text, Config.MAX_TEXT_LENGTH_CONCEPTS)
    prompt = """
You are an expert educational assistant. Analyze the ENTIRE text provided below to extract the most important key concepts.

IMPORTANT:
1. Look for concepts across the WHOLE document, not just the beginning.
2. Extract concepts as SHORT KEYWORDS OR PHRASES (1-3 words each).
3. Do NOT use full sentences.

Examples of GOOD concepts:
- "Event Loop"
- "Microtask Queue"
- "Call Stack"
- "Async Programming"
- "Promise Resolution"

Examples of BAD concepts (avoid these):
- "Understanding how the event loop works is essential"
- "The call stack is where functions are executed"

Extract the 10 most important concepts as SHORT KEYWORDS/PHRASES and describe relationships between them.

Return strictly valid JSON with two keys:
  - "concepts": ["concept1", "concept2", ...] (each concept should be 1-3 words)
  - "relationships": [{"source":"A", "relation":"rel", "target":"B"}, ... ]

Do not include extra commentary. Use the document context for relationships.

Text:
""" + truncated_text

    model = genai.GenerativeModel(MODEL)
    try:
        raw = _call_gemini_direct(model, prompt)
    except Exception as e:
        print(f"⚠️ Concept extraction error: {str(e)}")
        return {"concepts": [], "relationships": [], "error": str(e)}

    try:
        cleaned = raw.strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        data = json.loads(cleaned)
        if not isinstance(data.get("concepts"), list) or not isinstance(data.get("relationships"), list):
            raise ValueError("Invalid JSON shape")
        return data
    except Exception as e:
        return {"error": "failed_to_parse_model_response", "raw": raw}

def generate_mcq_from_text(text: str, count: int = 10, topics: List[str] = None) -> List[dict]:
    count = int(max(Config.MIN_QUIZ_QUESTIONS, min(Config.MAX_QUIZ_QUESTIONS, count)))
    truncated_text = _truncate_text(text, Config.MAX_TEXT_LENGTH_QUIZ)
    
    topics_hint = ""
    if topics:
        topics_hint = f"\nFocus on these topics: {', '.join(topics)}\n"
    
    prompt = f"""
You are an expert teacher creating high-quality quiz questions for studying and interview preparation.

{topics_hint}
Create {count} multiple choice questions (MCQs) based on the text below.

QUESTION QUALITY GUIDELINES:
1. **Conceptual Understanding**: Test core concepts, not just memorization
2. **Practical Application**: Include scenario-based questions that test real-world application
3. **Interview-Ready**: Frame questions similar to technical interviews
4. **Clear & Specific**: Questions should be unambiguous with one correct answer
5. **Challenging but Fair**: Balance between easy, medium, and difficult questions
6. **Diverse Coverage**: Cover different aspects of the topics

QUESTION TYPES TO INCLUDE:
- Definition/Concept questions (What is X?)
- Comparison questions (Difference between X and Y?)
- Application questions (When would you use X?)
- Scenario-based questions (Given situation Z, what happens?)
- Best practice questions (What's the best approach for X?)

For each question return a JSON object with keys:
  - "question": string (clear, specific, interview-style question)
  - "options": ["A) ...", "B) ...", "C) ...", "D) ..."] (all options should be plausible)
  - "answer": one of "A","B","C","D" (the correct option letter)
  - "explanation": detailed explanation (2-3 sentences explaining why the answer is correct and why others are wrong)
  - "difficulty": "easy", "medium", or "hard"
  - "type": "concept", "application", "scenario", or "comparison"

Return a JSON array of these objects only—no extra text.

Text:
""" + truncated_text

    model = genai.GenerativeModel(MODEL)
    try:
        raw = _call_gemini_direct(model, prompt)
    except Exception as e:
        print(f"⚠️ MCQ generation error: {str(e)}")
        raise Exception(f"Quiz generation failed: {str(e)}")

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing error: {str(e)}")
        print(f"⚠️ Problematic JSON (first 500 chars): {cleaned[:500]}")
        return [{
            "question": "Quiz generation incomplete - please try again",
            "options": ["A) Try again", "B) Reduce question count", "C) Try different topics", "D) Check content length"],
            "answer": "A",
            "explanation": f"The AI response was malformed or incomplete. This can happen with very long content. Error: {str(e)[:100]}"
        }]
    except Exception as e:
        return [{"question": "Parsing failed", "options": [], "answer": None, "explanation": raw}]

def ask_question_about_text(question: str, text: str, history: List[dict] = None) -> str:
    history = history or []
    ctx = _truncate_text(text, Config.MAX_TEXT_LENGTH_QA)
    convo_hint = ""
    if history:
        convo_hint += "Conversation history:\n"
        for msg in history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            convo_hint += f"{role}: {content}\n"

    prompt = f"""
You are an intelligent assistant with expertise in explaining concepts clearly.

PRIORITY: Use the document context below to answer questions when relevant information is available.

Document context:
{ctx}

{convo_hint}

INSTRUCTIONS:
1. If the question is directly answerable from the document context, use that information as your primary source.
2. If the question is related to the document's topic but asks for comparisons, alternatives, or broader context (e.g., "does Python have hooks?" when document is about React hooks), you can use your general knowledge to provide a helpful comparison or explanation while noting it's not in the original material.
3. Keep answers concise (50-200 words) but informative.
4. If asked about something completely unrelated to the document, politely redirect to the document's topic.
5. IMPORTANT: Do NOT use markdown formatting in your response. Avoid using backticks (`), asterisks (*), or other markdown syntax. Write in plain text only.

Question: {question}

Answer:
    """

    model = genai.GenerativeModel(MODEL)
    try:
        raw = _call_gemini_direct(model, prompt)
    except Exception as e:
        print(f"⚠️ Q&A error: {str(e)}")
        return f"Unable to answer due to an error. Please try again. Error: {str(e)}"
    
    return raw.strip()
