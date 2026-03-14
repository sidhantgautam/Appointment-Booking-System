from fastapi import APIRouter
from pydantic import BaseModel

from ai.agent import run_agent
from ai.memory import get_memory, clear_memory, get_conversation_history
from utils.language import detect_language, translate_to_english, translate_from_english, get_language_name
from services.performance_monitor import PerformanceMonitor, LatencyTracker, performance_context
import re
import uuid

router = APIRouter(prefix="/ai", tags=["AI"])


class TextInput(BaseModel):
    text: str
    session_id: str = None  # Optional session_id, defaults to None
    return_in_original_language: bool = True  # Translate response back to user's language


@router.post("/agent")
def agent_process(data: TextInput):

    user_text = data.text
    
    # Create performance tracker
    request_id = f"text_{uuid.uuid4().hex[:8]}"
    tracker = PerformanceMonitor.create_tracker(request_id)
    
    # Generate session_id if not provided
    session_id = data.session_id if data.session_id else "default_user"
    
    # Add metadata
    tracker.add_metadata("session_id", session_id)
    tracker.add_metadata("text_length", len(user_text))
    tracker.add_metadata("return_in_original_language", data.return_in_original_language)

    # Language detection and translation
    with performance_context("language_detection", tracker):
        lang = detect_language(user_text)
        lang_name = get_language_name(lang)
    
    tracker.add_metadata("detected_language", lang)
    
    # Translation to English
    with performance_context("translation_to_english", tracker):
        # Don't translate time-only inputs
        time_only_pattern = r'^\s*\d{1,2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?|:\d{2}\s*(?:AM|PM|am|pm)?)\s*$'
        if re.match(time_only_pattern, user_text, re.IGNORECASE):
            english_text = user_text
        else:
            english_text = translate_to_english(user_text, lang)

    tracker.add_metadata("english_text_length", len(english_text))

    # AI Agent processing
    with performance_context("llm_reasoning", tracker):
        result = run_agent(english_text, session_id=session_id)
    
    tracker.add_metadata("agent_action", result.get("action", "unknown"))
    
    translated_response = None
    with performance_context("translation_from_english", tracker):
        if data.return_in_original_language and lang != "en":
            # Extract message from result
            message = result.get("message") or result.get("error")
            if message:
                translated_response = translate_from_english(message, lang)
                # Update result with translated message
                if "message" in result:
                    result["message_translated"] = translated_response
                elif "error" in result:
                    result["error_translated"] = translated_response

    # Log performance
    performance_summary = tracker.log_performance()
    
    # Log text pipeline specific metrics
    PerformanceMonitor.log_text_pipeline_performance(
        request_id=request_id,
        translation_duration=(
            tracker.timings.get("translation_to_english", {}).get("duration_ms", 0) +
            tracker.timings.get("translation_from_english", {}).get("duration_ms", 0)
        ),
        llm_duration=tracker.timings.get("llm_reasoning", {}).get("duration_ms", 0),
        total_duration=performance_summary["total_duration_ms"],
        metadata={
            "session_id": session_id,
            "language": lang,
            "text_length": len(user_text)
        }
    )

    return {
        "request_id": request_id,
        "session_id": session_id,
        "original_text": user_text,
        "detected_language": lang,
        "language_name": lang_name,
        "translated_text": english_text,
        "agent_result": result,
        "response_translated": translated_response,
        "performance": {
            "total_duration_ms": performance_summary["total_duration_ms"],
            "component_timings": {
                "language_detection_ms": tracker.timings.get("language_detection", {}).get("duration_ms", 0),
                "translation_ms": (
                    tracker.timings.get("translation_to_english", {}).get("duration_ms", 0) +
                    tracker.timings.get("translation_from_english", {}).get("duration_ms", 0)
                ),
                "llm_reasoning_ms": tracker.timings.get("llm_reasoning", {}).get("duration_ms", 0)
            }
        }
    }


class SessionRequest(BaseModel):
    session_id: str


@router.get("/session/{session_id}")
def get_session_memory(session_id: str):
    """Get the current memory state for a session"""
    memory = get_memory(session_id)
    return {
        "session_id": session_id,
        "memory": memory
    }


@router.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Get conversation history for a session"""
    history = get_conversation_history(session_id)
    return {
        "session_id": session_id,
        "conversation_history": history,
        "message_count": len(history)
    }


@router.delete("/session/{session_id}")
def clear_session_memory(session_id: str):
    """Clear/reset the memory for a session"""
    clear_memory(session_id)
    return {
        "session_id": session_id,
        "message": "Session memory cleared successfully"
    }
