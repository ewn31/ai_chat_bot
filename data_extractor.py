import os
import json
import logging
import dotenv
import router
from database import db

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging_file = os.getenv('LOGGING_FILE', 'chatbot_log.log')
if logging_file:
    logging.basicConfig(filename=logging_file, level=getattr(logging, logging_level, logging.INFO))
else:
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO))


def set_next_question(question_list:dict, current_qusetion:str):
    questions:list = list(question_list.keys())
    if current_qusetion == None:
        return questions[0]
    index_of_question = questions.index(current_qusetion)
    if (index_of_question + 1) == len(questions):
        return "Done"
    return questions[index_of_question + 1]

def message_builder(question_list:dict, question_title:str, language:str='en'):
    """Builds question message from an object of questions
    by selecting the question from the object

    Args:
        question_list (obj): An object of questions and their options
        question_title (str): The question to be processed
        language (str): Language code ('en' or 'fr'), defaults to 'en'

    Returns:
        tuple: question(str), object of options
    """
    question_dict:dict = question_list[question_title]

    # Extract question text based on language
    if isinstance(question_dict['question'], dict):
        question_text = question_dict['question'].get(language, question_dict['question'].get('en'))
    else:
        question_text = question_dict['question']

    # Check if options exist
    if "options" not in question_dict:
        return question_text, None

    # Extract options based on language
    question_options = question_dict["options"]
    if isinstance(question_options, dict):
        question_options = question_options.get(language, question_options.get('en'))

    # Build Whapi-compatible button message
    option_message = {
        'body': {'text': "Please select an option."},
        'action': {'buttons': []},
        'type': 'button'
    }

    # Convert each option to Whapi button format
    for idx, option in enumerate(question_options):
        button = {
            'type': 'quick_reply',
            'title': option,
            'id': f"{question_title}_{idx}"
        }
        option_message['action']['buttons'].append(button)

    return question_text, option_message
    
    

def load_question_list(question_file):
    try:
        with open(question_file, "r", encoding="utf-8") as question_json:
            questions = json.load(question_json)
            logging.info(f"Loaded questions from file:{question_file}")
            logging.debug(f"Loaded {questions} from {question_file}")
            return questions
    except FileNotFoundError as e:
        logging.error(f"Failed to load file {question_file} with error {str(e)}")      
    

def save_conversation(user, res, reciever=None):
    logging.info("saving conversation")
    logging.debug("user : %s, response to save: %s", user, res)
    print("Saving conversation...")
    print("User:", user)
    print("Response:", res)
    if res is None:
        logging.warning("No message to save for user: %s", user)
        return
    if 'sent' in res:
        res = res['message']
    status = db.save_memory(res, user, receiver_id=reciever)
    if not status:
        print("Error saving conversation to database.")
    else:
        print("Conversation saved successfully.")


def send_question(user_id, question, route, options=None):
    logging.debug(f"Sending question")
    res1 = router.route_message(route,user_id, question)
    if res1.get('error'):
        logging.error(f"Failed to send question: {res1.get('error')}")
        return False
    logging.debug("Sending question: {question} to user {user_id} succesful")
    save_conversation('ai_bot', res1, user_id)

    if options:
        res2 = router.route_message(route, user_id, options, "options")
        if res2.get('error'):
            logging.error(f"Failed to send options: {res2.get('error')}")
            return False
        logging.debug("Sending options: {options} to user {user_id} succesful")
        save_conversation('ai_bot', res2, user_id)
    return True


# ==================== VALIDATION FUNCTIONS ====================

def validate_number(response, constraints, language='en'):
    """
    Validate numeric input.

    Args:
        response (str): User's response
        constraints (dict): Validation constraints
        language (str): Language for error messages

    Returns:
        tuple: (is_valid: bool, error_message: str or None, sanitized_value: int or None)
    """
    try:
        value = int(response.strip())

        min_val = constraints.get('min_value')
        max_val = constraints.get('max_value')

        if min_val is not None and value < min_val:
            error_msg = constraints.get('error_message', {}).get(language, f"Value must be at least {min_val}")
            return False, error_msg, None

        if max_val is not None and value > max_val:
            error_msg = constraints.get('error_message', {}).get(language, f"Value must be at most {max_val}")
            return False, error_msg, None

        return True, None, str(value)

    except ValueError:
        error_msg = constraints.get('error_message', {}).get(
            language,
            "Please enter a valid number" if language == 'en' else "Veuillez entrer un nombre valide"
        )
        return False, error_msg, None


def validate_text(response, constraints, language='en'):
    """
    Validate text input.

    Args:
        response (str): User's response
        constraints (dict): Validation constraints
        language (str): Language for error messages

    Returns:
        tuple: (is_valid: bool, error_message: str or None, sanitized_value: str or None)
    """
    import re

    text = response.strip()

    # Check minimum length
    min_len = constraints.get('min_length')
    if min_len and len(text) < min_len:
        error_msg = constraints.get('error_message', {}).get(
            language,
            f"Text must be at least {min_len} characters" if language == 'en' else f"Le texte doit contenir au moins {min_len} caractères"
        )
        return False, error_msg, None

    # Check maximum length
    max_len = constraints.get('max_length')
    if max_len and len(text) > max_len:
        error_msg = constraints.get('error_message', {}).get(
            language,
            f"Text must be at most {max_len} characters" if language == 'en' else f"Le texte ne doit pas dépasser {max_len} caractères"
        )
        return False, error_msg, None

    # Check pattern
    pattern = constraints.get('pattern')
    if pattern and not re.match(pattern, text):
        error_msg = constraints.get('error_message', {}).get(
            language,
            "Invalid format" if language == 'en' else "Format invalide"
        )
        return False, error_msg, None

    return True, None, text


def validate_choice(response, question, constraints, language='en'):
    """
    Validate choice/option selection.

    Args:
        response (str): User's response
        question (dict): Question definition with options
        constraints (dict): Validation constraints
        language (str): Language for error messages

    Returns:
        tuple: (is_valid: bool, error_message: str or None, sanitized_value: str or None)
    """
    response_lower = response.strip().lower()

    # Get valid options for this language
    options = question.get('options', {})
    if isinstance(options, dict):
        valid_options_current_lang = [opt.lower() for opt in options.get(language, [])]
        valid_options_all_lang = []
        for lang_opts in options.values():
            if isinstance(lang_opts, list):
                valid_options_all_lang.extend([opt.lower() for opt in lang_opts])
    else:
        valid_options_current_lang = [opt.lower() for opt in options]
        valid_options_all_lang = valid_options_current_lang

    # Check if response matches any valid option
    if response_lower in valid_options_current_lang or response_lower in valid_options_all_lang:
        return True, None, response.strip()

    # If text input is allowed, validate as text
    if constraints.get('allow_text_input', False):
        text_type = constraints.get('text_type', 'text')

        if text_type == 'number':
            return validate_number(response, constraints, language)
        elif text_type == 'text':
            # Use text validation with constraints
            text_constraints = {
                'min_length': constraints.get('min_length', 1),
                'max_length': constraints.get('max_length', 200),
                'pattern': constraints.get('pattern'),
                'error_message': constraints.get('error_message')
            }
            return validate_text(response, text_constraints, language)

    # If we get here, the response is invalid
    error_msg = constraints.get('error_message', {}).get(
        language,
        "Please select one of the options" if language == 'en' else "Veuillez sélectionner l'une des options"
    )
    return False, error_msg, None


def validate_user_response(response, question_key, questions_obj, language='en'):
    """
    Validate user response against question constraints.

    Args:
        response (str): User's response text
        question_key (str): The question identifier
        questions_obj (dict): All questions with their constraints
        language (str): Language code ('en' or 'fr')

    Returns:
        tuple: (is_valid: bool, error_message: str or None, sanitized_value: any)
    """
    if not response or not response.strip():
        # Empty response - check if required
        question = questions_obj.get(question_key, {})
        constraints = question.get('constraints', {})

        if constraints.get('required', False):
            error_msg = {
                'en': "This question is required. Please provide an answer.",
                'fr': "Cette question est obligatoire. Veuillez fournir une réponse."
            }
            return False, error_msg.get(language, error_msg['en']), None
        else:
            # Empty response is okay for optional questions
            return True, None, None

    question = questions_obj.get(question_key)
    if not question:
        available_keys = list(questions_obj.keys()) if questions_obj else []
        logging.error(f"Question key '{question_key}' not found in questions object. Available keys: {available_keys}")
        error_msg = {
            'en': "An error occurred. Please try again.",
            'fr': "Une erreur s'est produite. Veuillez réessayer."
        }
        return False, error_msg.get(language, error_msg['en']), None

    constraints = question.get('constraints', {})

    # If no constraints defined, accept any response
    if not constraints:
        return True, None, response.strip()

    # Validate based on type
    constraint_type = constraints.get('type', 'text')

    try:
        if constraint_type == 'number':
            return validate_number(response, constraints, language)
        elif constraint_type == 'text':
            return validate_text(response, constraints, language)
        elif constraint_type == 'choice':
            return validate_choice(response, question, constraints, language)
        else:
            logging.warning(f"Unknown constraint type: {constraint_type}")
            return True, None, response.strip()
    except Exception as e:
        logging.error(f"Validation error for question '{question_key}': {str(e)}")
        error_msg = {
            'en': "An error occurred while validating your response. Please try again.",
            'fr': "Une erreur s'est produite lors de la validation de votre réponse. Veuillez réessayer."
        }
        return False, error_msg.get(language, error_msg['en']), None
