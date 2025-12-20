import os
import logging
import json
import re
import ast
from langchain_together import Together
import dotenv

print("Starting extract_data_with_ai.py")

dotenv.load_dotenv()

POSSIBLE_LOGGING_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

if os.getenv('LOGGING_LEVEL').upper() not in POSSIBLE_LOGGING_LEVELS:
    print(f"Invalid LOGGING_LEVEL. Please set LOGGING_LEVEL to one of {POSSIBLE_LOGGING_LEVELS}.")
    exit(1)
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging_file = os.getenv('LOGGING_FILE', 'chat_bot_log.log')

if logging_file:
    logging.basicConfig(filename=logging_file, level=getattr(logging, logging_level, logging.INFO))
else:
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO), format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

together_api_key = os.getenv("TOGETHER_API_KEY")

os.environ["TOGETHER_API_KEY"] = together_api_key

script_dir = os.path.dirname(os.path.abspath(__file__))
extract_json_file_path = os.path.join(script_dir, 'extract_data.json')

llm_model = os.getenv("LLM", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")

llm = Together(
    model=llm_model,
    temperature=0.0,  # deterministic extraction
    max_tokens=512,   # Limit response length
    top_p=1.0         # Use full probability mass for deterministic output
)

logger.debug("")

def extract_data_with_ai(chat_api_response):
    """Extracts relevant data from WhatsApp API response using AI

    Args:
        chat_api_response (dict) or str: The WhatsApp API response containing chat data
        
    Returns:
        dict: Extracted structured data
        """
    logger.debug("User response from api:%s", chat_api_response)
    
    #print("Extracting data with AI...")
    
    user_response = None
    
    if isinstance(chat_api_response, dict):
        if chat_api_response['text']:
            user_response = chat_api_response.get('text', {}).get('body', '')
            if user_response == "":
                logger.warning("The user message is an empty string")
                return
    else:
        user_response = str(chat_api_response)
    with open(extract_json_file_path) as json_data_file:
        data_info = json.loads(json_data_file.read())
        #print(data_info)
        # Hardened prompt: explicit schema, formatting rules, normalization and validation
        prompt = f"""
    You are a strict data-extraction assistant. Your only job is to extract the requested fields
    from the user's text and return a single valid JSON object. Do NOT output any explanation,
    markdown, code fences, or commentary. Output must be valid JSON that can be parsed by json.loads.

    USER TEXT:
    {json.dumps(user_response)}

    DATA SCHEMA (fields to extract):
    {json.dumps(data_info, indent=2)}

    RESPONSE RULES (must follow exactly):
    1) Output exactly one JSON object and nothing else.
    2) The JSON keys must exactly match the field names in the DATA SCHEMA's top-level 'data' keys.
    3) For fields that cannot be extracted, use null (JSON null).
    4) For boolean values use true/false (JSON booleans). For lists use JSON arrays.
    5) Normalize enumerations to lowercase strings that match the schema enums (e.g., 'male', 'female', 'other').
    6) Dates should use ISO 8601 date format (YYYY-MM-DD) or null if unknown.
    7) Do not include any extra keys beyond the schema fields.

    OUTPUT EXAMPLE (exact format):
    {{
      "age": 27,
      "gender": null,
      "disabilities": ["none"],
      "hiv_status": "negative",
      "location": "buea",
      "last_menstrual_date": null,
      "marital_status": "single"
    }}

    IMPORTANT: After producing the JSON, validate it internally: ensure it is parseable as JSON and contains only the schema keys. If you cannot produce valid JSON, output a JSON object where every key has value null.

    Now extract the data and respond with ONLY the JSON object.
    """
        logger.debug("Prompt: %s", prompt)
        #print(prompt)
        # Retry logic: attempt extraction multiple times if parsing fails
        max_attempts = 3
        attempt = 1

        # Try to extract JSON safely from the response
        def parse_json_from_response(text):
            # 1) Try direct parse
            try:
                return json.loads(text)
            except Exception:
                pass

            # 2) Look for JSON inside markdown/code fences
            fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL | re.IGNORECASE)
            if fence_match:
                candidate = fence_match.group(1)
                try:
                    return json.loads(candidate)
                except Exception:
                    pass

            # 3) Find the first {...} object-like substring and attempt to fix common issues
            obj_matches = re.findall(r'\{[\s\S]*?\}', text)
            for m in obj_matches:
                candidate = m
                # Replace single quotes with double quotes when safe
                # but avoid replacing inside already-quoted strings — do a simple heuristic
                # First try direct parse
                # Try JSON first
                try:
                    return json.loads(candidate)
                except Exception:
                    pass

                # If the LLM returned a Python-style literal (single quotes, None, True/False),
                # ast.literal_eval can safely evaluate it into Python objects.
                try:
                    parsed_py = ast.literal_eval(candidate)
                    if isinstance(parsed_py, dict):
                        return parsed_py
                except Exception:
                    pass

                # Try quick normalization: replace single quotes with double quotes and convert Python null/booleans
                cand2 = candidate.replace("'", '"')
                cand2 = re.sub(r"\bNone\b", 'null', cand2)
                cand2 = re.sub(r"\bTrue\b", 'true', cand2)
                cand2 = re.sub(r"\bFalse\b", 'false', cand2)
                try:
                    return json.loads(cand2)
                except Exception:
                    # Try removing trailing commas
                    cand3 = re.sub(r',\s*}', '}', cand2)
                    cand3 = re.sub(r',\s*\]', ']', cand3)
                    try:
                        return json.loads(cand3)
                    except Exception:
                        continue

            return None

        response = None
        parsed = None

        while attempt <= max_attempts:
            try:
                # Use the original hardened prompt on first attempt, subsequent attempts use a short corrective prompt
                if attempt == 1:
                    response = llm.invoke(prompt)
                else:
                    corrective = (
                        "The previous response was not valid JSON.\n"
                        "Please extract the requested fields from the USER TEXT and respond ONLY with a single valid JSON object.\n"
                        "Use null for missing values and do NOT include any explanation or markdown.\n"
                        "DATA SCHEMA: " + json.dumps(data_info) + "\n"
                        "USER TEXT: " + json.dumps(user_response)
                    )
                    response = llm.invoke(corrective)

                logger.debug("Raw LLM response (attempt %d): %s", attempt, response)
            except Exception as e:
                logger.error("An Error occured when invoking the LLM on attempt %d: %s", attempt, e)
                print("\n❌ Error invoking LLM:", e)
                # If LLM failed (network/etc), break and return fallback
                break

            #print(response)
            logger.debug("LLM response: %s", response)  

            parsed = parse_json_from_response(response)
            if parsed is not None:
                # Validate parsed contains only schema keys
                try:
                    schema_keys = list(data_info.get('data', {}).keys())
                    parsed_keys = list(parsed.keys()) if isinstance(parsed, dict) else []
                    if set(parsed_keys).issubset(set(schema_keys)):
                        return parsed
                    else:
                        logger.warning('Parsed JSON contains unexpected keys: %s', parsed_keys)
                except Exception as e:
                    logger.debug('Error validating parsed keys: %s', e)

            # If parsing failed or validation failed, prepare for retry
            logger.info('Attempt %d failed to produce valid JSON, retrying...', attempt)
            attempt += 1

        # All attempts exhausted — return a safe fallback: all schema keys null
        logger.warning('All attempts to parse LLM response failed; returning fallback with nulls')
        fallback = {k: None for k in data_info.get('data', {}).keys()}
        print('\n⚠ Returning fallback extracted data with null values')
        logger.debug("Fallback data: %s", fallback)
        return fallback


if __name__ == "__main__":
    print("EXTRACT DATA WITH AI")
    test_query = "I am 27 years old and I am nurse. I am single and have no disabilities. I don't have hiv and I live in buea"    
    data = extract_data_with_ai(test_query)
    print(type(data))
    if isinstance(data, dict):
        print(json.dumps(data, indent=2))
    else:
        print(data)
