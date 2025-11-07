import logging
import os
import requests
import dotenv

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

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000/api"


def create_user_token(user_id):
    """Create a user token for authentication."""
    logger.info(f"Creating token for user {user_id}")
    if not user_id:
        raise ValueError("User ID cannot be empty")
    if not isinstance(user_id, str):
        raise TypeError("User ID must be a string")
    
    url = f"{BASE_URL}/auth/generate-key"
    logger.debug(f"Request URL: {url}")
    logger.debug(f"User ID: {user_id}")
    body = {"username": user_id, "expires_in_days": 60}
    logger.debug(f"Request body: {body}")
    try:
        response = requests.post(url, json=body)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        raise
    logger.info("Token created successfully")
    logger.debug(f"Response: {response}")
    if response.status_code == 201:
        return response.json().get("api_key")
    else:
        raise Exception(f"Failed to create token: {response.text}")

def create_room(user_id, counsellor_id, auth_token):
    "Create chat room for user and counsellor"
    logger.info(f"Creating chat room for user {user_id} and counsellor {counsellor_id}")
    if not user_id or not counsellor_id:
        raise ValueError("User ID and Counsellor ID cannot be empty")
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    logger.debug(f"Headers: {headers}")
    url = f"{BASE_URL}/rooms"
    logger.debug(f"Request URL: {url}")
    logger.debug(f"User ID: {user_id}, Counsellor ID: {counsellor_id}")
    body = {"slug": f"wa_{user_id}_{counsellor_id}", "is_private": True }
    logger.debug(f"Request body: {body}")
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        raise
    logger.info("Chat room created successfully")
    logger.debug(f"Response: {response}")
    if response.status_code == 201:
        return response.json().get("slug")
    else:
        raise Exception(f"Failed to create chat room: {response.text}")

def join_room(user_id, room_slug, auth_token):
    """Join a chat room."""
    logger.info(f"User {user_id} joining room {room_slug}")
    if not user_id or not room_slug:
        raise ValueError("User ID and Room Slug cannot be empty")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    logger.debug(f"Headers: {headers}")
    url = f"{BASE_URL}/rooms/{room_slug}/join"
    logger.debug(f"Request URL: {url}")
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        raise
    logger.info("User joined room successfully")
    logger.debug(f"Response: {response}")
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to join room: {response.text}")

#modify to check only for rooms for a specific user
def room_exist(slug, auth_token):
    """Checks if room exists

    Args:
        slug (str): the slug of the room
        auth_token (str): api auth key
    
    Returns
        bool: True if it exist, False otherwise
    """
    
    logger.info("Checking if room with slug: %s exists", slug)
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    logger.debug("Headers: %s", headers)
    url = f"{BASE_URL}/rooms"
    logger.debug("Request URL: %s", url)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("An Error occured: %s", e)
        raise
    
    logger.info("Rooms retrieved succesfully with response from chat app")
    logger.debug("Response: %s", response)
    
    if response.status_code == 200:
        rooms_dict = response.json()
        rooms = [room['slug'] for room in rooms_dict['rooms']]
        logger.debug("Room slugs: %s", rooms)
        return slug in rooms
    else:
        raise Exception(f"failed to check if room exists")
    
    
def send_message(room_slug, message, auth_token):
    """Send a message to a chat room."""
    logger.info(f"Sending message to room {room_slug}")
    if not room_slug or not message:
        raise ValueError("Room Slug and Message cannot be empty")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    logger.debug(f"Headers: {headers}")
    url = f"{BASE_URL}/rooms/{room_slug}/messages"
    logger.debug(f"Request URL: {url}")
    
    body = {"text": message}
    logger.debug(f"Request body: {body}")
    
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        raise
    logger.info("Message sent successfully")
    logger.debug(f"Response: {response}")
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to send message: {response.text}")
    
def generate_admin_key():
    """Generates an admin key for the chat app"""
    logger.info("Generating admin key")
    SUPER_SECRET  = os.getenv("SUPER_ADMIN_SECRET", "test-super-secret-123")
    url = f"{BASE_URL}/admin/generate-key"
    logger.debug(f"Request URL: {url}")
    headers = {
        "Content-Type": "application/json",
        "X-Super-Admin-Secret": SUPER_SECRET
    }
    json = {
        "name": "Ai Chat Bot Admin platform",
        "expires_in_days": 365
    }
    
    try:
        response = requests.post(url, json=json, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        raise
    
    logger.info("Admin key generated successfully")
    logger.debug(f"Response: {response}")
    
    if response.status_code == 200:
        return response.json().get("api_key")
    else:
        raise Exception(f"Failed to generate admin key: {response.text}")
    
def provision_counsellor_account(username, email, admin_key):
    """Provisions a counsellor account in the chat app

    Args:
        username (str): The username of the counsellor
        email (str): The email of the counsellor
        admin_key (str): The admin api key for authentication

    Returns:
        str: The magic link for the counsellor account.
    """
    logger.info(f"Provisioning counsellor account for {username}")
    if not username or not email:
        raise ValueError("Username and Email cannot be empty")
    
    headers = {
        "X-Admin-API-Key": admin_key,
        "Content-Type": "application/json"
    }
    logger.debug(f"Headers: {headers}")
    url = f"{BASE_URL}/admin/provision-user"
    logger.debug(f"Request URL: {url}")
    
    body = {"username": username, "email": email}
    logger.debug(f"Request body: {body}")
    
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error occurred: {e}")
        return f'Error: {e}'
    
    logger.info("Counsellor account provisioned successfully")
    logger.debug(f"Response: {response}")
    
    if response.status_code == 200:
        return response.json().get("magic_link")
    else:
        return None