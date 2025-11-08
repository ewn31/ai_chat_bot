import os
import logging
import counsellors
import database.db as db
import chat_app
import router
import requests
import dotenv

dotenv.load_dotenv()

default_route = os.getenv('DEFAULT_ROUTE', 'default_whatsapp')

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

BASE_URL = os.getenv('CHAT_APP_URL_API', 'http://localhost:5000/api')

def create_counsellor(username, password, email, name=None, whatsapp_number=None):
    logger.info(f"Creating counsellor with username: {username}, email: {email}")
    # Use username as name if name not provided
    if not name:
        name = username
    if counsellors.add_counsellor({"username":username, "email":email, "password":password, "name":name}):
        logger.info(f"Counsellor {username} added successfully.")
        if whatsapp_number:
            logger.info(f"Adding WhatsApp channel {whatsapp_number} to counsellor {username}.")
            whatsapp_id = f"{whatsapp_number}@s.whatsapp.net"
            if counsellors.add_channel(username, "whatsapp", whatsapp_id):
                logger.info(f"WhatsApp channel {whatsapp_number} added successfully to counsellor {username}.")
            else:
                logger.error(f"Failed to add WhatsApp channel {whatsapp_number} to counsellor {username}.")
        #add counsellor to chat app backend
        logger.info("Adding counsellor to chat app backend via API.")
        logger.info("Checking if admin token is set.")
        # Get the admin API key
        admin_key = db.get_system_config('chat_app_admin_api_key')
        if admin_key == "" or admin_key == "test_admin_key_12345" or admin_key is None:
            logger.info("Admin API key not set or is default. Generating new admin API key.")
            try:
                admin_key = chat_app.generate_admin_key()
                # Store the new admin key in the database
                if db.set_system_config('chat_app_admin_api_key', admin_key, category='config'):
                    logger.info("New admin API key generated and stored successfully.")
                else:
                    raise Exception("Failed to store new admin API key in the database.")
            except Exception as e:
                logger.error(f"Failed to generate and store new admin API key: {e}")
        logger.info("Admin API key is set. Proceeding to add counsellor via API.")
        try:
            magic_link = chat_app.provision_counsellor_account(username, email, admin_key)
            if magic_link:
                if "Error" in magic_link:
                    logging.error('Failed to provision counsellor account: ' + magic_link)
                    if whatsapp_number:
                        logger.error("Failed to provision counsellor account; sending error via WhatsApp.")
                        res = router.route_message(default_route, f'{whatsapp_number}@s.whatsapp.net', f"Good day, your are now a counsellor for the abortion ai chat app.")
                    return
                logging.debug(f"Magic link generated: {magic_link}")
                msg = f"Counsellor {username} added to chat app. click on this link: {magic_link} to access the account Note: The link will expire in 7 days."
                if whatsapp_number:
                    logger.info("Preparing to send magic link via WhatsApp.")
                    res = router.route_message(default_route, f'{whatsapp_number}@s.whatsapp.net', msg)
                    if res['error']:
                        logger.error(f"Failed to send magic link via WhatsApp: {res['error']}")
                    else:
                        logger.info("Magic link sent to counsellor via WhatsApp")
                else:
                    logger.info("No WhatsApp number provided; sending magic link via email.")
                    logger.warning("Email sending functionality is not implemented yet.")
                    #TODO
                    #send email with magic link
        except Exception as e:
            logger.error(f"Failed to add counsellor {username} via API: {e}")
            return

    
if __name__ == "__main__":
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description="Create a counsellor account and provision it on the chat app.")
    parser.add_argument('--username', '-u', help='Counsellor username', required=False)
    parser.add_argument('--name', '-n', help='Counsellor full name (defaults to username if not provided)', required=False)
    parser.add_argument('--email', '-e', help='Counsellor email', required=False)
    parser.add_argument('--password', '-p', help='Counsellor password (if omitted you will be prompted)', required=False)
    parser.add_argument('--whatsapp', '-w', help='Optional WhatsApp number (digits only, without domain)', required=False)
    parser.add_argument('--quiet', action='store_true', help='Suppress success/failure messages to stdout')

    args = parser.parse_args()

    # Collect required values interactively if not provided
    username = args.username
    if not username:
        username = input('Counsellor username: ').strip()

    name = args.name
    if not name:
        name_input = input(f'Counsellor full name (press Enter to use "{username}"): ').strip()
        name = name_input if name_input else username

    email = args.email
    if not email:
        email = input('Counsellor email: ').strip()

    password = args.password
    if not password:
        # Prompt securely for password
        password = getpass.getpass('Counsellor password: ')
        confirm = getpass.getpass('Confirm password: ')
        if password != confirm:
            print('Error: passwords do not match')
            exit(2)

    whatsapp = args.whatsapp
    if whatsapp:
        # Normalize whatsapp number to expected form if user provided full id accidentally
        whatsapp = whatsapp.strip()
        if whatsapp.endswith('@s.whatsapp.net'):
            # strip domain
            whatsapp = whatsapp.replace('@s.whatsapp.net', '')

    # Basic validation
    if not username or not email or not password:
        print('username, email and password are required')
        exit(3)

    try:
        create_counsellor(username, password, email, name=name, whatsapp_number=whatsapp)
        if not args.quiet:
            print(f"Counsellor '{username}' creation initiated. Check logs for details.")
        # Update todo: mark creation as completed in logs only
        exit(0)
    except Exception as e:
        logger.error(f"Failed to create counsellor via CLI: {e}")
        if not args.quiet:
            print(f"Failed to create counsellor: {e}")
        exit(1)



