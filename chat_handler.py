import os
import logging
from datetime import datetime
import database.db as db
import transcript
import users
import counsellors
import counsellors_select_algo
import chat_app
import messages
import ticket
import router
import dotenv
from ai_bot.ai_bot import get_response
from utils.summerizer import prepare_history_for_llm
from utils.chat_data import get_chat_data
from language_dectector.language_detector import detect_language

dotenv.load_dotenv()

GREEETINGS_EN = """Hello bestie, welcome to aunty queen connect. I’m your good friend AWAA and I’m here to listen to, and share truthful, judgment-free information about safe abortion and reproductive health with you.
Feel free to ask me anything. It’s private, safe, and always with care."""

GREETINGS_FR = "Bienvenue! Comment puis-je vous aider aujourd'hui?"

MODE = os.getenv('MODE')
print(f"MODE: {MODE}")
POSSIBLE_LOGGING_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
if MODE not in ["no_counsellor", "single_counsellor", "multi_counsellors_wp", "multi_counsellors_wp_web"]:
    print("Invalid MODE. Please set MODE to 'no_counsellor', 'single_counsellor', or 'multi_counsellor'.")
    exit(1)
if os.getenv('LOGGING_LEVEL').upper() not in POSSIBLE_LOGGING_LEVELS:
    print(f"Invalid LOGGING_LEVEL. Please set LOGGING_LEVEL to one of {POSSIBLE_LOGGING_LEVELS}.")
    exit(1)
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging_file = os.getenv('LOGGING_FILE', 'chat_bot_log.log')
logging_format = '%(asctime)s - %(levelname)s - %(message)s'
if logging_file:
    logging.basicConfig(filename=logging_file, level=getattr(logging, logging_level, logging.INFO), format=logging_format)
else:
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO), format=logging_format)

def incoming_messages(user, message):
    """Handle incoming messages from users or counsellors.

    Args:
        user (str): The user ID.
        message (dict): The incoming message dictionary.
    """
    logging.info("Handling incoming message")
    logging.debug("Message from: %s, Message: %s", user, message)
    #if MODE == "no_counsellor":
    logging.debug('mode: %s', MODE)
    logging.debug('User: %s, Message: %s', user, message)
    logging.debug("Checking if message is from a first-time user...")
    if first_time_user(user):
        logging.info("First time user detected: %s", user)
        register_user(user)
        logging.info("User %s registered successfully.", user)
        save_conversation(user, message)
        language = detect_language(get_chat_data(message)['body'])
        logging.info("Detected language for user %s: %s", user, language)
        logging.info("Sending welcome message to user: %s", user)
        if language == 'fr':
            send_message(user, GREETINGS_FR)
        else:
            send_message(user, GREEETINGS_EN)
        return
    logging.info("Saving conversation for user: %s", user)
    save_conversation(user, message)
    user_profile = get_user_profile(user)
    if user_profile and user_profile['handler'] == "counsellor":
        if MODE == "no_counsellor":
            logging.info("User %s is assigned to a counsellor, skipping AI response", user)
            return
        elif MODE == "single_counsellor":
            pass
        elif MODE == "multi_counsellors_wp":
            pass
        elif MODE == "multi_counsellors_wp_web":
            logging.info("Handling multi-counsellor mode")
            # In this mode, we might want to route the message to a specific counsellor
            handler_agent = get_handler_agent(user)
            room_slug = f'wa_{user}_{handler_agent}'
            auth_token = users.get_user_profile(user)['auth_key']
            #checking if room exist
            if chat_app.room_exist(room_slug, auth_token):
                response = chat_app.send_message(room_slug, message, auth_token)
                return
            else:
                logging.warn("No room exist to send message")
        else:   
            print("Invalid MODE. Please set MODE to 'no_counsellor', 'single_counsellor', or 'multi_counsellor'.")
            return
    user_message = get_chat_data(message)['body']
    ai_response = get_ai_response(user, user_message)
    if ai_response is None:
        pass
    if ai_response == "Escalating to a counsellor...":
        #user_transcript = get_transcript(user)
        escalate_to_counsellor(user)
    else:
        print(f"AI response to {user}: {ai_response}")
        send_message(user, ai_response)
        #save_conversation("ai_bot", ai_response)         

def is_counsellor(user):
    logging.info("Checking if user: %s is a councellor", user)
    #counsellors.get_counsellors()
    return user in counsellors.get_counsellors()

def first_time_user(user):
    logging.info("Checking if user is in the database")
    return not db.user_exist(user)

def register_user(user):
    logging.info("saving user: %s", user)
    status = db.save_user(user)
    if status:
        logging.info("User: %s, saved sucesfully", user)
    else:
        logging.error("Failed to save user: %s", user)

def get_handler_agent(user):
    logging.info("Getting handler for a ticket")
    ticket_owner = user
    ticket_id = f'00T{ticket_owner}'
    logging.debug("Ticket_id: %s, User: %s", ticket_id, ticket_owner)
    user_ticket = db.get_ticket(ticket_id)
    logging.debug("Ticket: %s", user_ticket)
    if user_ticket:
        handler_id = user_ticket['handler']  # Assuming handler is the 4th field in the ticket tuple
        return handler_id
    return None

def get_user_profile(user):
    logging.info("Getting user info")
    user_profile = db.get_user_profile(user)
    logging.debug("User profile: %s", user_profile)
    return user_profile

def get_ai_response(user, message):
    logging.info("Getting message from db")
    memories = db.get_memory(user)
    logging.debug("User messages: %s", memories )
    msgs = [(memory['_from'], memory['content']) for memory in memories]
    logging.info("Preparing history for llm")
    history =  prepare_history_for_llm(msgs)
    logging.debug("Prepared history: %s", history)
    logging.info("Getting response from llm")
    llm_response =  get_response(message, history)
    logging.debug("response fromm llm: %s", llm_response)
    return llm_response
    

def send_message(user, message):
    if MODE == "no_counsellor":
        logging.info("Sending message to user")
        logging.debug("User: %s, Message: %s", user, message)
        response = router.route_message("test_route", user, message)
        print(f"Response from router: {response}")
        if "error" in response:
            print(f"Error sending message to {user}: {response['error']}")
        else:
            if response['sent']:
                logging.info("Message sent successfully to user: %s", user)
                save_conversation("ai_bot", response['message'])

def notify_counsellor(counsellor_id, ticket_id):
    logging.info("Notifying counsellor %s about ticket %s", counsellor_id, ticket_id)
    # Implement notification logic here (e.g., send email or message)
    pass

def escalate_to_counsellor(user):
    #change user handler to counsellor
    logging.info("Escalating user %s to counsellor", user)
    users.update_user_handler(user, "counsellor")
    #create a new ticket
    ticket_id = ticket.create_ticket(user)
    #get a counsellor
    counsellor_id = counsellors_select_algo.round_robin()
    #assign a counsellor
    if ticket.assign_handler(ticket_id, counsellor_id):
        logging.info("Counsellor assigned successfully to ticket: %s", ticket_id)
    else:
       logging.error("Failed to assign counsellor to ticket: %s", ticket_id)
    #notify counsellor
    user_token = chat_app.create_user_token(user)
    if db.update_user(user, "auth_key", user_token):
        logging.info("User token updated successfully for user: %s", user)
    else:
        logging.error("Failed to update user token for user: %s", user)    
    #return ticket id
    room_slug = chat_app.create_room(user, counsellor_id, user_token)
    chat_app.join_room(user, room_slug, user_token)
    # counsellor joins room
    counsellor_token = counsellors.get_token(counsellor_id, "chat_app")
    chat_app.join_room(counsellor_id, room_slug, counsellor_token)
    # send notification to counsellor
    logging.debug("Getting transcript for ticket id: %s to send to counsellor", ticket_id)
    ts = ticket.get_ticket(ticket_id)['transcript']
    logging.debug('transcript: %s', ts)
    try:
        chat_app.send_message(room_slug, ts, user_token)
        logging.info("Transcript sent to counsellor: %s", counsellor_id)
    except Exception as e:
        logging.error('Failed to send transcript')
    return ticket_id

def save_conversation(user, res):
    logging.info("saving conversation")
    logging.debug("user : %s, response to save: %s", user, res)
    print("Saving conversation...")
    print("User:", user)
    print("Response:", res)
    if res is None:
        logging.warning("No message to save for user: %s", user)
        return
    status = db.save_memory(res, user_id=user)
    if not status:
        print("Error saving conversation to database.")
    else:
        print("Conversation saved successfully.")

def get_transcript(user):
    logging.info("Generating transcript for user %s", user)
    ts = transcript.generate_transcript(user)
    logging.debug("transcript: %s", ts)
    return ts


if __name__ == "__main__":
    # Example usage
    #print("Starting...")
    #incoming_messages("user123", "Hello, I need help with my anxiety.")
    #escalate_to_counsellor('237672372043@s.whatsapp.net')
    chat_app.send_message("wa_237672372043@s.whatsapp.net_test_counsellor", "Hello!", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3RfY291bnNlbGxvciIsImV4cCI6MTc2NDM2MDQ3OSwiaWF0IjoxNzYxNzY4NDc5LCJ0eXBlIjoiYXBpX2tleSJ9.cKuZ1sOBoTybEiv17F-Cxj1LzQVee2cPDQfU21Zgrrc")