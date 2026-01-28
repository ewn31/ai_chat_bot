import os
import json
import logging
import dotenv
import router

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
        'body': {'text': question_text},
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
    

def send_question(user_id, question, options):
    logging.debug(f"Sending question")
    res1 = router.route_message('default_route',user_id, question)
    if res1['error']:
        logging.error(f"Failed to send question: {res1['error']}")
        return False
    logging.debug("Sending question: {question} to user {user_id} succesful")
    
    if options:
        res2 = router.route_message("default_route", user_id, options, "options")
        if res2['error']:
            logging.error(f"Failed to send question: {res1['error']}")
            return False
        logging.debug("Sending options: {options} to user {user_id} succesful")
    
    return True
