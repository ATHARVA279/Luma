import os
import json
import time
import re
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from typing import List

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found in environment. "
        "Please set it in Backend/.env file. "
        "Get your free API key at: https://ai.google.dev/"
    )

genai.configure(api_key=GEMINI_API_KEY)

# Choose a model; you can change according to availability
MODEL = "gemini-2.5-flash"  # Stable model with wide availability

def _extract_retry_delay(error_message: str) -> int:
    """Extract retry delay from error message if available"""
    match = re.search(r'retry in (\d+)', error_message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'retry_delay.*seconds:\s*(\d+)', error_message)
    if match:
        return int(match.group(1))
    return 60  # Default to 60 seconds

def _call_gemini_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    """
    Call Gemini API with exponential backoff retry logic for rate limits
    """
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:
                    print(f"⏳ Rate limit hit. Retrying attempt {attempt + 1}/{max_retries}...")
                    continue
                else:
                    # Last attempt failed, raise with user-friendly message
                    retry_delay = _extract_retry_delay(error_str)
                    raise Exception(
                        f"Gemini API rate limit exceeded. You've hit the daily quota (50 requests/day for free tier). "
                        f"Please wait {retry_delay} seconds or upgrade your API plan at https://ai.google.dev/pricing"
                    )
            else:
                # Non-rate-limit error, raise immediately
                raise e
    
    raise Exception("Failed to call Gemini API after retries")

def _truncate_text(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit]

def extract_concepts_from_text(text: str) -> dict:
    """
    Sends a prompt to Gemini asking for concepts and relationships in JSON.
    Returns parsed JSON dict.
    """
    truncated_text = _truncate_text(text, 3800)
    prompt = """
You are an expert educational assistant. Extract key concepts from the text as SHORT KEYWORDS OR PHRASES (1-3 words each).

IMPORTANT: Each concept should be a concise keyword or short phrase, NOT a full sentence.

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

    # Use the generative model interface with retry logic
    model = genai.GenerativeModel(MODEL)
    try:
        raw = _call_gemini_with_retry(model, prompt)
    except Exception as e:
        print(f"⚠️ Concept extraction error: {str(e)}")
        # Return empty structure on rate limit
        return {"concepts": [], "relationships": [], "error": str(e)}

    # Try to find JSON inside the response
    try:
        # If the model returned text and includes markdown code fences, strip them
        cleaned = raw.strip()
        # Find first "{" and last "}" for robustness
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        data = json.loads(cleaned)
        # Validate basic keys
        if not isinstance(data.get("concepts"), list) or not isinstance(data.get("relationships"), list):
            raise ValueError("Invalid JSON shape")
        return data
    except Exception as e:
        # If parsing fails, return fallback minimal structure
        return {"error": "failed_to_parse_model_response", "raw": raw}

def generate_mcq_from_text(text: str, count: int = 10, topics: List[str] = None) -> List[dict]:
    """
    Generate `count` MCQs from text using Gemini.
    Returns list of {question, options: [..], answer: "A"/"B", explanation}
    """
    count = int(max(1, min(20, count)))
    truncated_text = _truncate_text(text, 3800)
    
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
        raw = _call_gemini_with_retry(model, prompt)
    except Exception as e:
        print(f"⚠️ MCQ generation error: {str(e)}")
        raise Exception(f"Quiz generation failed: {str(e)}")

    try:
        # extract JSON array from response
        cleaned = raw.strip()
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        data = json.loads(cleaned)
        return data
    except Exception as e:
        # If parsing fails, attempt to return an error-friendly structure
        return [{"question": "Parsing failed", "options": [], "answer": None, "explanation": raw}]

def ask_question_about_text(question: str, text: str, history: List[dict] = None) -> str:
    """
    Basic Q&A that uses the document text as context.
    history: optional list of {"role":"user"/"assistant", "content": "..."} to provide conversational context.
    """
    history = history or []
    ctx = _truncate_text(text, 3000)
    # build a prompt that includes last few messages for context
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

Question: {question}

Answer:
    """

    model = genai.GenerativeModel(MODEL)
    try:
        raw = _call_gemini_with_retry(model, prompt)
    except Exception as e:
        print(f"⚠️ Q&A error: {str(e)}")
        return f"Unable to answer due to API rate limits. Please try again in a few moments. Error: {str(e)}"
    
    # simple cleanup
    return raw.strip()
