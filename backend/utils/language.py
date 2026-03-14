from langdetect import detect
from deep_translator import GoogleTranslator


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "es": "Spanish",
    "fr": "French"
}


def detect_language(text: str):
    """
    Detect language with special handling for Tamil and Hindi
    """
    try:
        detected = detect(text)
        
        # Handle misdetections
        if detected in ["id", "ms"]:
            detected = "hi"
        
        # but we'll add validation
        if detected == "ta":
            if any('\u0B80' <= char <= '\u0BFF' for char in text):
                return "ta"
        
        return detected
    except:
        return "unknown"


def is_tamil(text: str):
    """Check if text contains Tamil characters"""
    return any('\u0B80' <= char <= '\u0BFF' for char in text)


def is_hindi(text: str):
    """Check if text contains Hindi/Devanagari characters"""
    return any('\u0900' <= char <= '\u097F' for char in text)


def get_language_name(lang_code: str):
    """Get human-readable language name"""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code.upper())


def translate_to_english(text: str, source_lang: str):
    """
    Translate text to English with special handling for Tamil and Hindi
    """
    
    # Handle misdetected Hindi
    if source_lang in ["id", "ms"]:
        source_lang = "hi"
    
    # Already English
    if source_lang == "en":
        return text
    
    # Handle Tamil explicitly
    if source_lang == "ta" or is_tamil(text):
        try:
            translated = GoogleTranslator(
                source="ta",
                target="en"
            ).translate(text)
            return translated
        except Exception as e:
            print(f"Tamil translation error: {e}")
            return text
    
    # Handle Hindi explicitly
    if source_lang == "hi" or is_hindi(text):
        try:
            translated = GoogleTranslator(
                source="hi",
                target="en"
            ).translate(text)
            return translated
        except Exception as e:
            print(f"Hindi translation error: {e}")
            return text
    
    # Handle other languages
    try:
        translated = GoogleTranslator(
            source=source_lang,
            target="en"
        ).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error ({source_lang} -> en): {e}")
        return text


def translate_from_english(text: str, target_lang: str):
    """
    Translate English text to target language with Tamil and Hindi support
    """
    
    if target_lang == "en":
        return text
    
    # Handle Tamil explicitly
    if target_lang == "ta":
        try:
            translated = GoogleTranslator(
                source="en",
                target="ta"
            ).translate(text)
            return translated
        except Exception as e:
            print(f"English to Tamil translation error: {e}")
            return text
    
    # Handle Hindi explicitly
    if target_lang == "hi":
        try:
            translated = GoogleTranslator(
                source="en",
                target="hi"
            ).translate(text)
            return translated
        except Exception as e:
            print(f"English to Hindi translation error: {e}")
            return text
    
    # Handle other languages
    try:
        translated = GoogleTranslator(
            source="en",
            target=target_lang
        ).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error (en -> {target_lang}): {e}")
        return text


def translate_bidirectional(text: str, source_lang: str, target_lang: str):
    """
    Translate between any two supported languages
    """
    if source_lang == target_lang:
        return text
    
    try:
        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error ({source_lang} -> {target_lang}): {e}")
        return text
