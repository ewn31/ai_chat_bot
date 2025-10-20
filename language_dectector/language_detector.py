"""
Language Detector Module for AI Chatbot

This module provides language detection functionality using the langdetect library.
It can detect the language of user messages to enable multilingual support.

Usage:
    from language_detector import detect_language, detect_language_with_confidence
    
    text = "Hello, how are you?"
    lang = detect_language(text)  # Returns 'en'
    
    lang, confidence = detect_language_with_confidence(text)  # Returns ('en', 0.999)
"""

from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import logging

# Set seed for consistent results (langdetect uses randomization)
DetectorFactory.seed = 0

# Configure logging
logger = logging.getLogger(__name__)


def detect_language(text, default='en'):
    """
    Detect the language of the given text.
    
    Args:
        text (str): Text to detect language from
        default (str): Default language code to return if detection fails
        
    Returns:
        str: ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'sw')
        
    Examples:
        >>> detect_language("Hello, how are you?")
        'en'
        >>> detect_language("Hola, ¿cómo estás?")
        'es'
        >>> detect_language("Habari yako?")
        'sw'
    """
    try:
        # Handle empty or very short text
        if not text or len(text.strip()) < 3:
            logger.warning(f"Text too short for detection: '{text}'. Returning default: {default}")
            return default
        
        # Detect language
        lang = detect(text)
        logger.debug(f"Detected language '{lang}' for text: '{text[:50]}...'")
        return lang
        
    except LangDetectException as e:
        logger.warning(f"Language detection failed for text: '{text[:50]}...'. Error: {e}. Returning default: {default}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}. Returning default: {default}")
        return default


def detect_language_with_confidence(text, default='en'):
    """
    Detect the language of the given text with confidence scores.
    
    Args:
        text (str): Text to detect language from
        default (str): Default language code to return if detection fails
        
    Returns:
        tuple: (language_code, confidence) where confidence is between 0 and 1
        
    Examples:
        >>> detect_language_with_confidence("Hello, how are you?")
        ('en', 0.9999)
        >>> detect_language_with_confidence("Hola")
        ('es', 0.8571)
    """
    try:
        # Handle empty or very short text
        if not text or len(text.strip()) < 3:
            logger.warning(f"Text too short for detection: '{text}'. Returning default: {default}")
            return (default, 0.0)
        
        # Detect languages with probabilities
        langs = detect_langs(text)
        
        if langs:
            # Get the most probable language
            top_lang = langs[0]
            lang_code = top_lang.lang
            confidence = top_lang.prob
            
            logger.debug(f"Detected language '{lang_code}' with confidence {confidence:.4f} for text: '{text[:50]}...'")
            return (lang_code, confidence)
        else:
            logger.warning(f"No language detected for text: '{text[:50]}...'. Returning default: {default}")
            return (default, 0.0)
            
    except LangDetectException as e:
        logger.warning(f"Language detection failed for text: '{text[:50]}...'. Error: {e}. Returning default: {default}")
        return (default, 0.0)
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}. Returning default: {default}")
        return (default, 0.0)


def get_all_language_probabilities(text):
    """
    Get probabilities for all detected languages.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        list: List of tuples [(lang_code, probability), ...] sorted by probability
        
    Examples:
        >>> get_all_language_probabilities("Hello comment allez-vous")
        [('en', 0.7142), ('fr', 0.2857)]
    """
    try:
        if not text or len(text.strip()) < 3:
            return []
        
        langs = detect_langs(text)
        result = [(lang.lang, lang.prob) for lang in langs]
        
        logger.debug(f"Language probabilities for '{text[:50]}...': {result}")
        return result
        
    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def is_language(text, expected_lang, threshold=0.9):
    """
    Check if text is in the expected language with a confidence threshold.
    
    Args:
        text (str): Text to check
        expected_lang (str): Expected language code (e.g., 'en', 'es', 'sw')
        threshold (float): Minimum confidence level (0.0 to 1.0)
        
    Returns:
        bool: True if text is in expected language with sufficient confidence
        
    Examples:
        >>> is_language("Hello, how are you?", "en")
        True
        >>> is_language("Hello", "es")
        False
    """
    try:
        lang, confidence = detect_language_with_confidence(text)
        is_match = (lang == expected_lang and confidence >= threshold)
        
        logger.debug(f"Language check: expected='{expected_lang}', detected='{lang}', "
                    f"confidence={confidence:.4f}, threshold={threshold}, match={is_match}")
        return is_match
        
    except Exception as e:
        logger.error(f"Error in language check: {e}")
        return False


def get_language_name(lang_code):
    """
    Get the full language name from ISO 639-1 code.
    
    Args:
        lang_code (str): ISO 639-1 language code
        
    Returns:
        str: Full language name
        
    Examples:
        >>> get_language_name('en')
        'English'
        >>> get_language_name('es')
        'Spanish'
    """
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'sw': 'Swahili',
        'ar': 'Arabic',
        'zh-cn': 'Chinese (Simplified)',
        'zh-tw': 'Chinese (Traditional)',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ru': 'Russian',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'ur': 'Urdu',
        'id': 'Indonesian',
        'nl': 'Dutch',
        'pl': 'Polish',
        'tr': 'Turkish',
        'vi': 'Vietnamese',
        'th': 'Thai',
        'el': 'Greek',
        'he': 'Hebrew',
        'fa': 'Persian',
    }
    
    return language_names.get(lang_code, lang_code.upper())


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Language Detection Examples")
    print("=" * 60)
    
    # Test cases with various languages
    test_texts = [
        ("Hello, how are you?", "English"),
        ("Hola, ¿cómo estás?", "Spanish"),
        ("Bonjour, comment ça va?", "French"),
        ("Hallo, wie geht es dir?", "German"),
        ("Habari yako? Unafanya nini?", "Swahili"),
        ("مرحبا، كيف حالك؟", "Arabic"),
        ("Ciao, come stai?", "Italian"),
        ("Olá, como você está?", "Portuguese"),
        ("你好，你好吗？", "Chinese"),
        ("こんにちは、お元気ですか？", "Japanese"),
        ("What is abortion?", "English (Medical)"),
        ("Je voudrais des informations sur l'avortement", "French (Medical)"),
    ]
    
    print("\n1. Basic Language Detection:")
    print("-" * 60)
    for text, expected in test_texts:
        lang = detect_language(text)
        lang_name = get_language_name(lang)
        print(f"Text: {text[:40]:<40} | Detected: {lang_name} ({lang})")
    
    print("\n2. Language Detection with Confidence:")
    print("-" * 60)
    for text, expected in test_texts[:5]:  # First 5 examples
        lang, confidence = detect_language_with_confidence(text)
        lang_name = get_language_name(lang)
        print(f"Text: {text[:40]:<40} | {lang_name} ({lang}) - {confidence:.2%}")
    
    print("\n3. All Language Probabilities:")
    print("-" * 60)
    mixed_text = "Hello bonjour hola"
    probs = get_all_language_probabilities(mixed_text)
    print(f"Text: '{mixed_text}'")
    for lang, prob in probs:
        print(f"  - {get_language_name(lang)} ({lang}): {prob:.2%}")
    
    print("\n4. Language Validation:")
    print("-" * 60)
    validation_tests = [
        ("Hello, how are you?", "en", True),
        ("Hola, ¿cómo estás?", "en", False),
        ("What is safe abortion?", "en", True),
        ("Qu'est-ce que l'avortement?", "fr", True),
    ]
    for text, expected_lang, should_match in validation_tests:
        is_match = is_language(text, expected_lang)
        status = "✓" if is_match == should_match else "✗"
        print(f"{status} Text: {text[:35]:<35} | Expected: {expected_lang} | Match: {is_match}")
    
    print("\n5. Edge Cases:")
    print("-" * 60)
    edge_cases = [
        "",           # Empty string
        "hi",         # Very short
        "123",        # Numbers only
        "???",        # Special characters
        "a b c",      # Single letters
    ]
    for text in edge_cases:
        lang = detect_language(text)
        print(f"Text: '{text}' -> Detected: {lang}")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
