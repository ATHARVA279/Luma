from typing import List, Dict
import google.generativeai as genai
import os
import re
import time

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def _extract_retry_delay(error_message: str) -> int:
    match = re.search(r'retry in (\d+)', error_message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'retry_delay.*seconds:\s*(\d+)', error_message)
    if match:
        return int(match.group(1))
    return 60

def _call_gemini_with_retry(model, prompt: str, max_retries: int = 2) -> str:
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Retrying attempt {attempt + 1}/{max_retries}...")
                    continue
                else:
                    retry_delay = _extract_retry_delay(error_str)
                    raise Exception(
                        f"Gemini API rate limit exceeded (50 requests/day for free tier). "
                        f"Please wait {retry_delay} seconds or upgrade at https://ai.google.dev/pricing"
                    )
            else:
                raise e
    
    raise Exception("Failed after retries")

def _get_model():
    return genai.GenerativeModel("gemini-2.0-flash")

def generate_study_notes(content: str, topic: str = "General") -> Dict:
    model = _get_model()
    
    try:
        summary_prompt = f"""Analyze this content about "{topic}" and provide a concise summary (3-4 sentences):

Content:
{content[:3000]}

Summary:"""
        
        summary = _call_gemini_with_retry(model, summary_prompt).strip()
        
        key_points_prompt = f"""Extract 5-7 key points from "{topic}". Return as JSON array of strings:

{content[:3000]}"""
        
        key_points_text = _call_gemini_with_retry(model, key_points_prompt).strip()
        key_points_raw = _parse_json_array(key_points_text)
        key_points = _normalize_key_points(key_points_raw)
        
        definitions_prompt = f"""Extract important terms and definitions from "{topic}". Return as JSON object with term:definition pairs:

{content[:3000]}"""
        
        definitions_text = _call_gemini_with_retry(model, definitions_prompt).strip()
        definitions_raw = _parse_json_object(definitions_text)
        definitions = _normalize_definitions(definitions_raw)
        
        flashcards = _generate_flashcards(content, topic, model)
        
        mind_map = _generate_mind_map(key_points, topic)
        
        practice_questions = _generate_practice_questions(content, topic, model)
        
        return {
            "topic": topic,
            "summary": summary,
            "key_points": key_points,
            "definitions": definitions,
            "mind_map": mind_map,
            "flashcards": flashcards,
            "practice_questions": practice_questions,
            "estimated_study_time": _estimate_study_time(content),
            "difficulty_level": _estimate_difficulty(key_points, definitions)
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Note generation error: {error_msg}")
        raise Exception(f"Note generation failed: {error_msg}")

def generate_quick_summary(content: str, max_sentences: int = 3) -> str:
    model = _get_model()
    
    prompt = f"""Provide a {max_sentences}-sentence summary:

{content[:2000]}"""
    
    try:
        return _call_gemini_with_retry(model, prompt).strip()
    except Exception as e:
        return f"Summary unavailable due to rate limits: {str(e)}"

def extract_key_concepts(content: str, top_n: int = 10) -> List[str]:
    model = _get_model()
    
    prompt = f"""Extract the top {top_n} key concepts. Return as JSON array:

{content[:2000]}"""
    
    result = model.generate_content(prompt).text.strip()
    return _parse_json_array(result)

def _generate_flashcards(content: str, topic: str, model) -> List[Dict]:
    prompt = f"""Create 5 flashcards for "{topic}" with question and answer. Return as JSON array:

{content[:2000]}"""
    
    flashcards_text = model.generate_content(prompt).text.strip()
    flashcards_data = _parse_json_array(flashcards_text, default=[])
    
    if not flashcards_data:
        return [
            {"question": "What is the main topic?", "answer": topic},
            {"question": "Key concept?", "answer": "See summary"}
        ]
    
    return flashcards_data

def _generate_mind_map(key_points: List[str], topic: str) -> Dict:
    mind_map = {
        "central_topic": topic,
        "branches": []
    }
    
    for i, point in enumerate(key_points[:6]):
        if isinstance(point, dict):
            point_text = point.get('text', '') or point.get('title', '') or str(point)
        else:
            point_text = str(point)
        
        words = point_text.split()[:4]
        branch_title = " ".join(words) if words else f"Point {i+1}"
        
        mind_map["branches"].append({
            "id": f"branch_{i+1}",
            "title": branch_title,
            "details": point_text,
            "sub_branches": []
        })
    
    return mind_map

def _generate_practice_questions(content: str, topic: str, model) -> List[Dict]:
    prompt = f"""Create 3 practice questions about "{topic}". Return as JSON array:

{content[:2000]}"""
    
    questions_text = model.generate_content(prompt).text.strip()
    questions = _parse_json_array(questions_text, default=[])
    
    if not questions:
        return [
            {
                "question": f"Explain the main concepts of {topic}",
                "difficulty": "medium",
                "hint": "Review the summary section"
            }
        ]
    
    return questions

def _estimate_study_time(content: str) -> int:
    if not isinstance(content, str):
        content = str(content)
    
    words = len(content.split())
    reading_time = words / 225
    study_time = reading_time * 1.5
    return max(5, int(study_time))

def _estimate_difficulty(key_points: List[str], definitions: Dict) -> str:
    total_words = 0
    for p in key_points:
        if isinstance(p, dict):
            point_text = p.get('text', '') or p.get('title', '') or str(p)
        else:
            point_text = str(p)
        total_words += len(point_text.split())
    
    avg_point_length = total_words / max(len(key_points), 1)
    num_definitions = len(definitions)
    
    if avg_point_length > 20 or num_definitions > 10:
        return "Advanced"
    elif avg_point_length > 12 or num_definitions > 5:
        return "Intermediate"
    else:
        return "Beginner"

def _parse_json_array(text: str, default: List = None) -> List:
    import json
    
    if default is None:
        default = []
    
    try:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        return json.loads(text)
    except:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            return [line.strip('- ').strip() for line in lines[:10]]
        
        return default

def _parse_json_object(text: str, default: Dict = None) -> Dict:
    import json
    
    if default is None:
        default = {}
    
    try:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        return default

def _normalize_key_points(key_points: List) -> List[str]:
    normalized = []
    for point in key_points:
        if isinstance(point, dict):
            text = point.get('point', '') or point.get('text', '') or point.get('description', '') or str(point)
            normalized.append(text)
        elif isinstance(point, str):
            normalized.append(point)
        else:
            normalized.append(str(point))
    return normalized

def _normalize_definitions(definitions) -> Dict[str, str]:
    if isinstance(definitions, list):
        result = {}
        for item in definitions:
            if isinstance(item, dict):
                term = item.get('term', '') or item.get('word', '') or item.get('concept', '')
                definition = item.get('definition', '') or item.get('def', '') or item.get('meaning', '')
                if term and definition:
                    result[term] = definition
        return result
    elif isinstance(definitions, dict):
        if 'terms' in definitions and isinstance(definitions['terms'], list):
            return _normalize_definitions(definitions['terms'])
        elif 'definitions' in definitions:
            return _normalize_definitions(definitions['definitions'])
        else:
            return {k: str(v) if not isinstance(v, str) else v for k, v in definitions.items()}
    return {}
