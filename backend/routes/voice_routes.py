from fastapi import APIRouter, UploadFile, File
import shutil
from voice.stt import transcribe_audio
from ai.agent import run_agent
from utils.language import detect_language, translate_to_english, translate_from_english, get_language_name
from services.performance_monitor import PerformanceMonitor, LatencyTracker, performance_context
import re
import time
import uuid

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = transcribe_audio(file_path)

    return {"transcription": text}


@router.post("/agent")
async def voice_agent(
    file: UploadFile = File(...), 
    session_id: str = "default_user",
    return_in_original_language: bool = True
):
    """
    Complete voice assistant endpoint with performance monitoring:
    1. Transcribe audio to text (Whisper supports Tamil)
    2. Detect language (English, Hindi, Tamil)
    3. Translate to English if needed
    4. Process through AI agent
    5. Translate response back to user's language
    6. Return complete result with performance metrics
    """
    
    # Create performance tracker
    request_id = f"voice_{uuid.uuid4().hex[:8]}"
    tracker = PerformanceMonitor.create_tracker(request_id)
    
    # Add metadata
    tracker.add_metadata("session_id", session_id)
    tracker.add_metadata("file_size_bytes", file.size if hasattr(file, 'size') else 0)
    tracker.add_metadata("return_in_original_language", return_in_original_language)
    
    # Save uploaded audio file
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    with performance_context("stt_processing", tracker) as stt_timer:
        transcribed_text = transcribe_audio(file_path)
    
    tracker.add_metadata("transcribed_text_length", len(transcribed_text))
    
    # Step 2: Detect language and translate
    with performance_context("language_detection", tracker):
        lang = detect_language(transcribed_text)
        lang_name = get_language_name(lang)
    
    tracker.add_metadata("detected_language", lang)
    
    with performance_context("translation_to_english", tracker) as translation_timer:
        # Don't translate time-only inputs
        time_only_pattern = r'^\s*\d{1,2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?|:\d{2}\s*(?:AM|PM|am|pm)?)\s*$'
        if re.match(time_only_pattern, transcribed_text, re.IGNORECASE):
            english_text = transcribed_text
        else:
            english_text = translate_to_english(transcribed_text, lang)
    
    tracker.add_metadata("english_text_length", len(english_text))
    
    # Step 4: Process through AI agent
    with performance_context("llm_reasoning", tracker) as llm_timer:
        agent_result = run_agent(english_text, session_id=session_id)
    
    tracker.add_metadata("agent_action", agent_result.get("action", "unknown"))
    
    translated_response = None
    with performance_context("translation_from_english", tracker):
        if return_in_original_language and lang != "en":
            # Extract message from result
            message = agent_result.get("message") or agent_result.get("error")
            if message:
                translated_response = translate_from_english(message, lang)
                # Update result with translated message
                if "message" in agent_result:
                    agent_result["message_translated"] = translated_response
                elif "error" in agent_result:
                    agent_result["error_translated"] = translated_response
    
    # Log performance
    performance_summary = tracker.log_performance()
    
    # Log voice pipeline specific metrics
    PerformanceMonitor.log_voice_pipeline_performance(
        request_id=request_id,
        stt_duration=tracker.timings.get("stt_processing", {}).get("duration_ms", 0),
        translation_duration=(
            tracker.timings.get("translation_to_english", {}).get("duration_ms", 0) +
            tracker.timings.get("translation_from_english", {}).get("duration_ms", 0)
        ),
        llm_duration=tracker.timings.get("llm_reasoning", {}).get("duration_ms", 0),
        total_duration=performance_summary["total_duration_ms"],
        metadata={
            "session_id": session_id,
            "language": lang,
            "file_size": tracker.metadata.get("file_size_bytes", 0)
        }
    )
    
    response = {
        "request_id": request_id,
        "session_id": session_id,
        "transcription": transcribed_text,
        "detected_language": lang,
        "language_name": lang_name,
        "translated_text": english_text,
        "agent_result": agent_result,
        "response_translated": translated_response,
        "performance": {
            "total_duration_ms": performance_summary["total_duration_ms"],
            "component_timings": {
                "stt_processing_ms": tracker.timings.get("stt_processing", {}).get("duration_ms", 0),
                "language_detection_ms": tracker.timings.get("language_detection", {}).get("duration_ms", 0),
                "translation_ms": (
                    tracker.timings.get("translation_to_english", {}).get("duration_ms", 0) +
                    tracker.timings.get("translation_from_english", {}).get("duration_ms", 0)
                ),
                "llm_reasoning_ms": tracker.timings.get("llm_reasoning", {}).get("duration_ms", 0)
            },
            "within_target_latency": performance_summary["total_duration_ms"] <= 450,
            "target_latency_ms": 450
        }
    }
    
    return response
