import os
import logging
import json
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
    temperature=0.7,  # Higher temp for more natural, varied responses
    max_tokens=512,   # Limit response length
    top_p=0.9         # Nucleus sampling for better quality
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
    
    print("Extracting data with AI...")
    
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
        print(data_info)
        prompt = f"""I want you to extract data from this text: {user_response}.
        data to be extracted from text: {data_info}. Output a json containing only the
        data fields and the extracted value. If a value for a data field cannot be extracted put none as 
        a value for that field. Please only respond with the json and nothing else.
        """
        logger.debug("Prompt: %s", prompt)
        print(prompt)
        try:
            response = llm.invoke(prompt)
            logger.debug(response)
        except Exception as e:
            logger.error("An Error occured when invoking the LLM%s:", e)
            response = "Sorry could not process your request"
        print(response)
        return json.loads(response)


if __name__ == "__main__":
    print("EXTRACT DATA WITH AI")
    test_query = "I am 27 years old and I am nurse. I am single and have no disabilities. I don't have hiv and I live in buea"    
    data = extract_data_with_ai(test_query)
    print(type(data))
    print(json.loads(data))
