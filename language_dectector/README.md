# Language Detector Integration Example

This example shows how to integrate the language detector into your AI chatbot.

## Installation

```bash
pip install langdetect
```

## Basic Usage

### 1. Simple Language Detection

```python
from language_dectector.language_detector import detect_language

# Detect language of user message
user_message = "What is abortion?"
language = detect_language(user_message)
print(f"Detected language: {language}")  # Output: en
```

### 2. Detection with Confidence

```python
from language_dectector.language_detector import detect_language_with_confidence

user_message = "¿Qué es el aborto?"
language, confidence = detect_language_with_confidence(user_message)
print(f"Language: {language}, Confidence: {confidence:.2%}")
# Output: Language: es, Confidence: 100.00%
```

### 3. Check if Text is in Specific Language

```python
from language_dectector.language_detector import is_language

user_message = "Hello, how are you?"
if is_language(user_message, "en", threshold=0.9):
    print("This is English!")
else:
    print("This is not English or confidence too low")
```

### 4. Get Full Language Name

```python
from language_dectector.language_detector import detect_language, get_language_name

user_message = "Bonjour"
lang_code = detect_language(user_message)
lang_name = get_language_name(lang_code)
print(f"User is speaking {lang_name}")  # Output: User is speaking French
```

---

## Integration with Chat Handler

Here's how to integrate language detection into your existing `chat_handler.py`:

```python
# In chat_handler.py

from language_dectector.language_detector import (
    detect_language, 
    detect_language_with_confidence,
    get_language_name
)
import logging

logger = logging.getLogger(__name__)


def incoming_messages(data):
    """
    Process incoming messages with language detection.
    """
    # ... existing code ...
    
    user_message = data.get('message', '')
    user_id = data.get('user_id', '')
    
    # Detect language
    language, confidence = detect_language_with_confidence(user_message)
    language_name = get_language_name(language)
    
    logger.info(f"User {user_id} - Language: {language_name} ({language}) - Confidence: {confidence:.2%}")
    
    # Handle non-English messages (optional)
    if language != 'en' and confidence > 0.9:
        logger.warning(f"User {user_id} sent message in {language_name}, but chatbot only supports English")
        # You could return a multilingual error message here
        # return {
        #     "response": "I'm sorry, I currently only support English. / Lo siento, actualmente solo admito inglés.",
        #     "language": language
        # }
    
    # Continue with normal processing
    # ... rest of your code ...
```

---

## Integration with AI Bot

Enhance your `ai_bot.py` to handle multilingual queries:

```python
# In ai_bot.py

from language_dectector.language_detector import detect_language, get_language_name

def get_response(user_query, history=None):
    """
    Get a response from the chatbot with language detection.
    """
    # Detect language
    detected_lang = detect_language(user_query)
    lang_name = get_language_name(detected_lang)
    
    # Log the detected language
    print(f"User query language: {lang_name} ({detected_lang})")
    
    # If not English, you can:
    # 1. Translate the query (requires translation API)
    # 2. Return a multilingual "unsupported language" message
    # 3. Use a multilingual model
    
    if detected_lang != 'en':
        return (
            f"I apologize, but I currently only support English. "
            f"It appears you're writing in {lang_name}. "
            f"Please try asking your question in English."
        )
    
    # Continue with normal RAG processing for English
    intent, confidence = detect_intent(user_query)
    # ... rest of your code ...
```

---

## Store Language in Database

Update your database schema to track user language preferences:

```python
# In database/db.py

def save_message_with_language(user_id, message, language):
    """
    Save message with detected language to database.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (user_id, message, language, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, message, language, datetime.now()))
    
    conn.commit()
    conn.close()
```

Add language column to your messages table:

```sql
-- In database/schema.sql
ALTER TABLE messages ADD COLUMN language TEXT DEFAULT 'en';
```

---

## Advanced: Multilingual Response Routing

Create different responses based on detected language:

```python
from language_dectector.language_detector import detect_language

MULTILINGUAL_RESPONSES = {
    'en': "I'm here to help with your questions about reproductive health.",
    'es': "Estoy aquí para ayudarte con tus preguntas sobre salud reproductiva.",
    'fr': "Je suis là pour vous aider avec vos questions sur la santé reproductive.",
    'sw': "Niko hapa kukusaidia na maswali yako kuhusu afya ya uzazi.",
    'ar': "أنا هنا لمساعدتك في أسئلتك حول الصحة الإنجابية.",
}

def get_greeting(user_message):
    """
    Return a greeting in the user's language.
    """
    lang = detect_language(user_message)
    return MULTILINGUAL_RESPONSES.get(lang, MULTILINGUAL_RESPONSES['en'])
```

---

## Supported Languages

The `langdetect` library supports 55+ languages including:

### Common Languages:
- **English** (en)
- **Spanish** (es)
- **French** (fr)
- **Portuguese** (pt)
- **German** (de)
- **Italian** (it)
- **Russian** (ru)
- **Arabic** (ar)
- **Chinese** (zh-cn, zh-tw)
- **Japanese** (ja)
- **Korean** (ko)
- **Hindi** (hi)
- **Swahili** (sw)
- **Indonesian** (id)
- **Turkish** (tr)
- **Vietnamese** (vi)
- **Thai** (th)

And many more!

---

## Best Practices

### 1. **Handle Short Messages**
```python
# Short messages may not be detected accurately
user_msg = "hi"
lang = detect_language(user_msg, default='en')  # Uses default for short text
```

### 2. **Use Confidence Thresholds**
```python
lang, confidence = detect_language_with_confidence(user_msg)

if confidence < 0.7:
    # Low confidence, might be mixed language or ambiguous
    logger.warning(f"Low confidence ({confidence:.2%}) for language detection")
```

### 3. **Cache Language Preference**
```python
# Store user's language preference after first detection
user_languages = {}

def get_user_language(user_id, message):
    if user_id in user_languages:
        return user_languages[user_id]
    
    lang = detect_language(message)
    user_languages[user_id] = lang
    return lang
```

### 4. **Handle Mixed Languages**
```python
from language_dectector.language_detector import get_all_language_probabilities

# For messages with multiple languages
probs = get_all_language_probabilities(user_message)
if len(probs) > 1 and probs[1][1] > 0.3:  # Second language > 30%
    logger.info(f"Mixed language detected: {probs}")
```

---

## Testing

Test the language detector with your chatbot:

```python
# test_language_integration.py
from language_dectector.language_detector import detect_language, detect_language_with_confidence

test_queries = [
    "What is abortion?",
    "¿Qué es el aborto?",
    "Qu'est-ce que l'avortement?",
    "Was ist Abtreibung?",
    "Habari kuhusu utoaji mimba?",
]

print("Testing Language Detection Integration:\n")
for query in test_queries:
    lang, conf = detect_language_with_confidence(query)
    print(f"Query: {query}")
    print(f"  Detected: {lang} (confidence: {conf:.2%})\n")
```

---

## Performance Considerations

- **Speed:** Language detection is very fast (~1-5ms per message)
- **Memory:** Minimal memory footprint
- **Accuracy:** 95-99% accurate for messages > 10 words
- **Thread-safe:** Can be used in multi-threaded applications

---

## Troubleshooting

### Issue: Inconsistent results for short text
**Solution:** Set a seed for deterministic results (already configured in module)

### Issue: Wrong language detected
**Solution:** Use confidence threshold and require minimum text length

### Issue: Mixed language content
**Solution:** Use `get_all_language_probabilities()` to see all detected languages

---

## Next Steps

1. ✅ Language detector is installed and working
2. 🔄 Integrate into `chat_handler.py` to log detected languages
3. 🔄 Add language column to database
4. 🔄 Create multilingual error messages
5. 🔄 Consider translation API integration (Google Translate, DeepL)
6. 🔄 Implement language-specific routing (if needed)

---

## Full Example: Complete Integration

```python
# complete_example.py

from language_dectector.language_detector import (
    detect_language_with_confidence,
    get_language_name,
    is_language
)
from ai_bot.ai_bot import get_response
import database.db as db

def process_user_message(user_id, message):
    """
    Complete message processing with language detection.
    """
    # Step 1: Detect language
    lang, confidence = detect_language_with_confidence(message)
    lang_name = get_language_name(lang)
    
    print(f"User {user_id}: {message}")
    print(f"Detected: {lang_name} ({lang}) - {confidence:.2%}")
    
    # Step 2: Check if English (or supported language)
    if not is_language(message, 'en', threshold=0.8):
        return {
            'response': f"I'm sorry, I currently only support English. You appear to be writing in {lang_name}.",
            'language': lang,
            'supported': False
        }
    
    # Step 3: Get AI response (English only)
    response = get_response(message)
    
    # Step 4: Save to database with language
    db.save_message_with_language(user_id, message, lang)
    
    return {
        'response': response,
        'language': lang,
        'supported': True
    }

# Test it
if __name__ == "__main__":
    result = process_user_message(
        user_id="test123",
        message="What is safe abortion?"
    )
    print(f"\nResponse: {result['response']}")
```

---

**Happy Coding! 🚀**
