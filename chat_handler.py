import os
import logging
from datetime import datetime
import database.db as db
import transcript
import users
import counsellors
import counsellors_select_algo
import chat_app
import ticket
import router
#import extract_data.extract_data_with_ai as extract_data
import dotenv
from ai_bot.ai_bot import get_response
from utils.summerizer import prepare_history_for_llm
from utils.chat_data import get_chat_data
from language_dectector.language_detector import detect_language
import data_extractor

dotenv.load_dotenv()

#incoming message are dictionaries
#Not all the incoming messages have the same structure

GREETINGS_EN = """Hello bestie, welcome to aunty queen connect. I’m your good friend MORIA and I’m here to listen to, and share truthful, judgment-free information about menstrual health with you.
Feel free to ask me anything. It’s private, safe, and always with care."""

GREETINGS_FR = """Bonjour mon ami, bienvenue à Aunty Queen Connect. Je suis votre bonne amie MORIA et je suis ici pour vous écouter et partager des 
informations véridiques et sans jugement sur l'avortement sûr et la santé reproductive avec vous."""

LANGUAGE_SELECTION_PROMPT = """Hello / Bonjour 👋

Please select your preferred language. / Veuillez sélectionner votre langue préférée:"""

ONBOARDING_INTRO_EN = """To provide you the best care, we need some information. This takes 2-3 minutes.

🔒 *Your privacy is protected* - all information is confidential. You can answer by selecting

the options or by typing your response."""

ONBOARDING_INTRO_FR = """Pour vous fournir les meilleurs soins, nous avons besoin de quelques informations. Cela prend 2-3 minutes.

🔒 *Votre vie privée est protégée* - toutes les informations sont confidentielles. Vous pouvez répondre en sélectionnant

les options ou en tapant votre réponse."""

INFORMATION_DEMAND_EN = """To provide you the best care, we need some information. This takes 2-3 minutes.

🔒 *Your privacy is protected* - all information is confidential.

Please reply with your answers, one per message:

1. Your age
2. Your gender (Male/Female/Other)
3. Number of children (or 0)
4. Your city/location
5. Any disabilities or health conditions (or 'none')
6. Are you on ARV medication? (Yes/No)
7. Are you displaced from home? (Yes/No)
8. Your occupation
9. Last menstrual period (if applicable, or 'skip')
10. Marital status (or 'skip')
11. Religious background (or 'skip')

💡 You can reply 'skip' to any question.

*Ready? Please send your age first.*"""

INFORMATION_DEMAND_FR = """Bonjour ! Pour vous fournir les meilleurs soins, nous avons besoin de quelques informations. Cela prend 2-3 minutes.

🔒 *Votre vie privée est protégée* - toutes les informations sont confidentielles.

Veuillez répondre avec vos réponses, une par message :

1. Votre âge
2. Votre genre (Homme/Femme/Autre)
3. Nombre d'enfants (ou 0)
4. Votre ville/localisation
5. Handicaps ou problèmes de santé (ou 'aucun')
6. Prenez-vous des ARV ? (Oui/Non)
7. Êtes-vous déplacé(e) ? (Oui/Non)
8. Votre profession
9. Dernières règles (si applicable, ou 'skip')
10. État civil (ou 'skip')
11. Religion (ou 'skip')

💡 Vous pouvez répondre 'skip' à toute question.

*Prêt(e) ? Envoyez d'abord votre âge.*"""

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

def incoming_messages(user, message, reciever_id=None):
    """Handle incoming messages from users or counsellors.

    Args:
        user (str): The user ID.
        message (dict): The incoming message dictionary.
    """
    logging.info("Handling incoming message")
    logging.debug("Message from: %s, Message: %s", user, message)
    #if MODE == "no_counsellor":
    msg_type = message['type']
    logging.debug("Incoming message type: %s", msg_type)
    if not is_counsellor(user):
        logging.debug('mode: %s', MODE)
        logging.debug('User: %s, Message: %s', user, message)
        logging.debug("Checking if message is from a first-time user...")
        if first_time_user(user):
            logging.info("First time user detected: %s", user)
            register_user(user)
            logging.info("User %s registered successfully.", user)
            save_conversation(user, message)
            logging.debug("Changing user %s handler to language_selector", user)
            if users.update_user_handler(user, "language_selector"):
                logging.info("User %s handler changed to language_selector successfully.", user)
            # Send language selection buttons
            send_language_selection(user)
            return
        logging.info("Saving conversation for user: %s", user)
        save_conversation(user, message)
        user_profile = get_user_profile(user)
        if user_profile and user_profile['handler'] == "language_selector":
            # Check if language has been set
            user_language = user_profile.get('language')
            logging.debug("Current user language: %s", user_language)

            # Process button/text replies to set or update language
            selected_language = user_language or 'en'  # Default to English or keep existing

            # Check for button reply first (always process, even if language already set)
            if msg_type == 'reply':
                category, option = get_button_category_and_options(message)
                if category == 'lang':
                    selected_language = option
                    users.update_user(user, 'language', selected_language)
                    logging.info("Language selected via button: %s", option)
                    user_language = selected_language
            elif not user_language:
                # Only process text-based language selection if language not already set
                logging.info("User %s has not set language yet.", user)
                logging.info("Processing language selection for user: %s", user)
                if msg_type == 'text':
                    last_msg = db.get_last_memory(user)
                    if last_msg:
                        last_msg_content = last_msg['content'].lower()
                        #Case where user types language instead of using buttons
                        if last_msg_content in LANGUAGE_SELECTION_PROMPT.lower():
                            # This is the language selection message
                            msg = get_chat_data(message)['body'].lower()
                            #check if user replied with language name in current message
                            if 'français' in msg or 'francais' in msg or msg == 'fr':
                                selected_language = 'fr'
                                users.update_user(user, 'language', selected_language)
                                logging.info("Language selected via text (French): %s", msg)
                            elif 'english' in msg or 'english' in msg or msg == 'en':
                                logging.info("Language selected via text (English): %s", msg)
                                selected_language = 'en'
                                users.update_user(user, 'language', selected_language)
                            #else try to detect language
                            else:
                                detected_lang = detect_language(msg, default='en')
                                users.update_user(user, 'language', detected_lang)
                                selected_language = detected_lang
                                logging.info("Language detected from message: %s", detected_lang)    
                        # Check if user replied with language name in previous message
                        elif 'français' in last_msg_content or 'francais' in last_msg_content or last_msg_content == 'fr':
                            selected_language = 'fr'
                            logging.info("Language selected via text in previous message (French): %s", last_msg_content)
                            users.update_user(user, 'language', selected_language)
                        elif 'english' in last_msg_content or last_msg_content == 'en':
                            selected_language = 'en'
                            logging.info("Language selected via text in previous message (English): %s", last_msg_content)
                            users.update_user(user, 'language', selected_language)
                    else:
                        logging.warning("No previous message found for user %s to determine language selection.", user)
                        msg = get_chat_data(message)['body'].lower()
                        detected_lang = detect_language(msg, default='en')
                        selected_language = detected_lang
                        users.update_user(user, 'language', selected_language)
                        logging.info("Language detected from message: %s", selected_language)
                # Store selected language
                #users.update_user(user, "language", selected_language)
                
                user_language = selected_language
                # Send welcome message in selected language
            if user_language == 'fr':
                logging.info("Sending French welcome messages to user: %s", user)
                send_message(user, GREETINGS_FR)
                logging.info("Sending French onboarding intro to user: %s", user)
                send_message(user, ONBOARDING_INTRO_FR)
            else:
                logging.info("Sending English welcome messages to user: %s", user)
                send_message(user, GREETINGS_EN)
                logging.info("Sending English onboarding intro to user: %s", user)
                send_message(user, ONBOARDING_INTRO_EN)

            # Update handler to onboarding for both languages
            logging.info("Setting handler to onboarding for user: %s", user)
            users.update_user_handler(user, "onboarding")

            current_question = user_profile['onboarding_level']
            # Load questions object (needed for sending questions)
            questions_obj = data_extractor.load_question_list("user_data.json")

            if not current_question:
                # Initialize onboarding - set first question
                logging.debug("Initializing onboarding for user: %s", user)
                question_titles = list(questions_obj.keys())
                current_question = question_titles[0]
                logging.info("First onboarding question for user %s: %s", user, current_question)
                logging.debug("Current onboarding question for user %s: %s", user, current_question)
            question_status = send_onboarding_question(questions_obj, current_question, user_language, user)
            if not question_status:
                logging.error("Failed to send onboarding question to user %s", user)
            return
        
        elif user_profile and user_profile['handler'] == "onboarding":
            RESEND_MSG = """Sorry the option you selected is not valid. Please select a valid option
            
            """
            
            def resend_question(current_question, questions_obj, user_lang, user):
                send_message(user, RESEND_MSG)
                question_to_send, options_to_send = data_extractor.message_builder(questions_obj, current_question, user_lang)
                route = os.getenv('DEFAULT_ROUTE', 'test_route')
                res_status = data_extractor.send_question(user, question_to_send, route, options_to_send)
                if res_status:
                    logging.info("Resent question: %s because user: %s did not select an appropriate option", question_to_send, user)
                    return
                else:
                    logging.error("Failed to resend question: %s because user: %s did not select an appropriate option", question_to_send, user)
                    return
            
            user_lang = user_profile['language']
            
            questions_obj = data_extractor.load_question_list('user_data.json')
            #Extract user answer and save to db
            # Map question keys to database fields
            field_mapping = {
                    'age': 'age',
                    'gender': 'gender',
                    'children': 'number_of_children',
                    'location': 'location',
                    'disabilities': 'disability',
                    'arv_medication': 'arv',
                    'displaced': 'internally_displaced',
                    'occupation': 'occupation',
                    'last_menstrual_period': 'last_menstrual_flow',
                    'marital_status': 'marital_status',
                    'religious_background': 'religious_background'
            }
            #Note set next question only after user has answered the current question
            current_question = user_profile.get('onboarding_level')

            # If no current question is set, initialize to first question
            if not current_question:
                logging.warning("No onboarding_level set for user %s, initializing to first question", user)
                question_titles = list(questions_obj.keys())
                current_question = question_titles[0]
                users.update_user(user, "onboarding_level", current_question)
                logging.info("Initialized onboarding_level to: %s for user %s", current_question, user)

            logging.debug("Current onboarding question for user %s: %s", user, current_question)

            #case where user responds with button
            if msg_type == 'reply':
                question_category, selected_option = extract_data_from_reply(message)
                if current_question == question_category:
                    db_field = field_mapping.get(current_question)
                    if db_field:
                        # Don't save if user skipped or preferred not to say
                        skip_values = ['skip', 'passer', 'prefer not to say', 'préfère ne pas dire']
                        if selected_option.lower() not in skip_values:
                            users.update_user(user, db_field, selected_option)
                            logging.info("Saved %s = %s for user %s", db_field, selected_option, user)
                        else:
                            logging.info("User %s skipped question: %s", user, current_question)
                else:
                    resend_question(current_question, questions_obj, user_lang, user)
                    return  # Don't proceed to next question if wrong button was clicked

            elif msg_type == 'text':
                # Handle text response with validation
                user_response = get_chat_data(message)['body']
                logging.debug("Processing text response for question %s: %s", current_question, user_response)

                # Validate the response
                is_valid, error_msg, sanitized_value = data_extractor.validate_user_response(
                    user_response,
                    current_question,
                    questions_obj,
                    user_lang
                )

                if is_valid:
                    # Save the validated response
                    db_field = field_mapping.get(current_question)
                    if db_field and sanitized_value:
                        # Check if user is skipping
                        skip_values = ['skip', 'passer', 'prefer not to say', 'préfère ne pas dire']
                        if sanitized_value.lower() not in skip_values:
                            users.update_user(user, db_field, sanitized_value)
                            logging.info("Saved %s = %s for user %s (from text input)", db_field, sanitized_value, user)
                        else:
                            logging.info("User %s skipped question: %s", user, current_question)
                    elif not sanitized_value:
                        # Empty response for optional question
                        logging.info("User %s provided empty response for optional question: %s", user, current_question)
                else:
                    # Validation failed - send error message and resend question
                    logging.warning("Invalid response from user %s for question %s: %s", user, current_question, error_msg)
                    send_message(user, error_msg)
                    resend_question(current_question, questions_obj, user_lang, user)
                    return  # Don't proceed to next question
            else:
                resend_question(current_question, questions_obj, user_lang, user)
            next_question = data_extractor.set_next_question(questions_obj, current_question)
            
            if next_question == 'Done':
                logging.info("Onboarding complete for user: %s", user)
                users.update_user_handler(user, "ai_bot")
                # Send completion message in user's language
                completion_msg = {
                    'en': "Your information is safe and confidential. How can we help you?",
                    'fr': "Vos informations sont sûres et confidentielles. Comment pouvons-nous vous aider ?"
                }
                send_message(user, completion_msg.get(user_lang, completion_msg['en']))
                return

            # Update to next question and send it
            users.update_user(user, "onboarding_level", next_question)
            logging.debug("Updated onboarding level to: %s for user: %s", next_question, user)

            # Send the next question
            question_status = send_onboarding_question(questions_obj, next_question, user_lang, user)
            if not question_status:
                logging.error("Failed to send next onboarding question %s to user %s", next_question, user)
            return       
                
        elif user_profile and user_profile['handler'] == "counsellor":
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
                if auth_token is None:
                    logging.info("Auth token not found for user %s, generating a new one", user)
                    try:
                        fresh_token = chat_app.create_user_token(user)  
                    except Exception as e:
                        logging.error("Failed to create user token for user %s: %s", user, e)
                        return
                    users.update_user(user, "auth_key", fresh_token)
                    auth_token = users.get_user_profile(user)['auth_key']
                #checking if room exist
                #if chat_app.room_exist(room_slug, auth_token):
                msg_body = get_chat_data(message)['body']
                response = chat_app.send_message(room_slug, msg_body, auth_token)
                if response.get("error"):
                    logging.error("Failed to send message to room %s: %s", room_slug, response['error'])
                return
                #else:
                    #logging.warn("No room exist to send message")
            else:   
                print("Invalid MODE. Please set MODE to 'no_counsellor', 'single_counsellor', or 'multi_counsellor'.")
                return
        
        elif user_profile and user_profile['handler'] == 'ai_bot':
            user_message = get_chat_data(message)['body']
            ai_response = get_ai_response(user, user_message, user_profile['language'])
            if ai_response is None:
                logging.error('Failed to get response from ai_bot for user: %s, request:%s', user, user_message)
                send_message(user, "We are experiencing some dificulties. Try again soon")
            if ai_response == "Escalating to a counsellor...":
                #user_transcript = get_transcript(user)
                escalate_to_counsellor(user)
                notify_user_counsellor_assigned(user, user_profile['language'])
                send_message(user, "Due to the sensitive nature of your message, you have been connected to a counsellor. They will be with you shortly.")
            else:
                print(f"AI response to {user}: {ai_response}")
                send_message(user, ai_response)
                #save_conversation("ai_bot", ai_response)
    
        else:
            logging.error("Failed to retrieve user and their handler")  
    
    else:
        msg = get_chat_data(message)['body']
        send_message(user, msg, reciever_id)
        

def is_counsellor(user):
    logging.info("Checking if user: %s is a councellor", user)
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
    # Convert sqlite3.Row to dict for easier access
    if user_profile:
        return dict(user_profile)
    return user_profile

def get_ai_response(user, message, language):
    logging.info("Getting message from db")
    memories = db.get_memory(user)
    logging.debug("User messages: %s", memories )
    msgs = [(memory['_from'], memory['content']) for memory in memories]
    logging.info("Preparing history for llm")
    history =  prepare_history_for_llm(msgs)
    logging.debug("Prepared history: %s", history)
    logging.info("Getting response from llm")
    llm_response =  get_response(message, language, history)
    logging.debug("response fromm llm: %s", llm_response)
    return llm_response
    

def send_message(user, message, sender='ai_bot'):
    default_route = os.getenv('DEFAULT_ROUTE', 'test_route')
    if MODE == "no_counsellor":
        logging.info("Sending message to user")
        logging.debug("User: %s, Message: %s", user, message)
        response = router.route_message(default_route, user, message)
        print(f"Response from router: {response}")
        if "error" in response:
            print(f"Error sending message to {user}: {response['error']}")
        else:
            #check if message was sent
            #handles endpoints for text messages with 'sent' field
            if response['sent']:
                logging.info("Message sent successfully to user: %s", user)
                save_conversation(sender, response['message'])
    elif MODE in ["multi_counsellors_wp", "multi_counsellors_wp_web"]:
        logging.info("Sending message to user in multi-counsellor mode")
        logging.debug("User: %s, Message: %s", user, message)
        response = router.route_message(default_route, user, message)
        print(f"Response from router: {response}")
        if "error" in response:
            logging.error("Error sending message to %s: %s", user, response['error'])
        else:
            logging.info("Message sent successfully to user: %s", user)
            save_conversation(sender, response, user)

def notify_counsellor(user, counsellor_id, ticket_id):
    logging.info("Notifying counsellor %s about ticket %s", counsellor_id, ticket_id)
    # Implement notification logic here (e.g., send email or message)
    if MODE == "no_counsellor":
        counsellor_wa_id = db.get_counsellor_channel_id(counsellor_id, "whatsapp")
        send_message(counsellor_wa_id, f"New ticket assigned: {ticket_id} from user: {user}. Please attend to it as soon as possible.")
    elif MODE == "multi_counsellors_wp":
        user_token = chat_app.create_user_token(user)
        if db.update_user(user, "auth_key", user_token):
            logging.info("User token updated successfully for user: %s", user)
        else:
            logging.error("Failed to update user token for user: %s", user)    
        #return ticket id
        room_slug = chat_app.create_room(user, counsellor_id, user_token)
        #When user creates a room the automatically are made a member of that room
        #chat_app.join_room(user, room_slug, user_token)
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
            logging.error('Failed to send transcript: %s', e)


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
    notify_counsellor(user, counsellor_id, ticket_id)
    return ticket_id

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

def notify_user_counsellor_assigned(user, language):
    logging.info("Notifying user %s about assigned counsellor", user)
    if language == 'fr':
        msg = "Un conseiller vous a été attribué. Vous pouvez maintenant discuter avec eux."
    else:
        msg = "A counsellor has been assigned to you. You can now chat with them."
    send_message(user, msg)

def get_transcript(user):
    logging.info("Generating transcript for user %s", user)
    ts = transcript.generate_transcript(user)
    logging.debug("transcript: %s", ts)
    return ts

def process_extracted_data(user, data):
    logging.info("Processing extracted data for user %s: %s", user, data)
    # Implement any processing logic needed for the extracted data
    # For example, saving to database or updating user profile
    for key, value in data.items():
        if value == "none" or value == "":
            continue
        print(f"Updating user {user} data: {key} = {value}")
        #db.update_user(user, key, value)

def send_language_selection(user):
    """Send language selection buttons to user."""
    logging.info("Sending language selection to user: %s", user)

    # Create Whapi-compatible button message
    language_options = {
        'body': {'text': LANGUAGE_SELECTION_PROMPT},
        'action': {
            'buttons': [
                {
                    'type': 'quick_reply',
                    'title': 'English 🇬🇧',
                    'id': 'lang_en'
                },
                {
                    'type': 'quick_reply',
                    'title': 'Français 🇫🇷',
                    'id': 'lang_fr'
                }
            ]
        },
        'type': 'button'
    }

    default_route = os.getenv('DEFAULT_ROUTE', 'test_route')
    response = router.route_message(default_route, user, language_options, "options")

    if "error" in response:
        logging.error("Error sending language selection to %s: %s", user, response['error'])
        # Fallback to text message
        #send_message(user, LANGUAGE_SELECTION_PROMPT + "\n\nReply 'English' or 'Français'")
    else:
        logging.info("Language selection sent successfully to user: %s", user)
        save_conversation('ai_bot', response['message'])

    return response

def get_button_category_and_options(message):
    msg_type = message['type']
    if msg_type == 'reply':
        if message[msg_type]['type'] == 'buttons_reply':
            _ , reply_info = (message[msg_type]['buttons_reply']['id']).split(':')
            category, option = reply_info.split('_')
            return category, option
    else:
        return

def send_onboarding_question(questions_obj, current_question, user_language, user):
    question, options = data_extractor.message_builder(questions_obj, current_question, user_language)

    logging.info("Sending onboarding question to user %s: %s", user, current_question)
    route = os.getenv('DEFAULT_ROUTE', 'test_route')
    res_status = data_extractor.send_question(user, question, route, options)
    if not res_status:
        logging.error("Failed to send onboarding question and options %s to user %s", current_question, user)
        return False
    else:
        users.update_user(user, "onboarding_level", current_question)
        #logging.info("Initialized onboarding for user %s with first question: %s", user, current_question)
        logging.info("Onboarding question %s sent successfully to user %s", current_question, user)
    return True

def extract_data_from_reply(message):
    msg_type = message['type']
    if msg_type == 'reply':
        if message[msg_type]['type'] == 'buttons_reply':
            _ , reply_info = (message[msg_type]['buttons_reply']['id']).split(':')
            # Use rsplit with maxsplit=1 to handle question keys with underscores (e.g., arv_medication)
            category, option_number = reply_info.rsplit('_', 1)
            option = message[msg_type]['buttons_reply']['title']
            return category, option
    else:
        return

if __name__ == "__main__":
    # Example usage
    print("Starting...")
    #incoming_messages("user123", "Hello, I need help with my anxiety.")
    #escalate_to_counsellor('23778452599@s.whatsapp.net')
    #chat_app.send_message("wa_237672372043@s.whatsapp.net_test_counsellor", "Hello!", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3RfY291bnNlbGxvciIsImV4cCI6MTc2NDM2MDQ3OSwiaWF0IjoxNzYxNzY4NDc5LCJ0eXBlIjoiYXBpX2tleSJ9.cKuZ1sOBoTybEiv17F-Cxj1LzQVee2cPDQfU21Zgrrc")