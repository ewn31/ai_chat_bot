"""
Database utility functions for managing users, counsellors, tickets, and messages.
Uses SQLite for data storage and retrieval.
Functions:
    - connect_db(): Connect to the SQLite database.
    - close_db(conn): Close the database connection.
    - init_db(): Initialize the database with the schema.
    - user_exist(user_id): Check if a user exists.
    - save_user(user_id): Save a new user.
    - update_user_handler(user_id, handler): Update user's handler.
    - update_user(user_id, field, data): Update specific user field.
    - get_user_count(): Get total number of users.
    - get_all_users(): Retrieve all users.
    - get_user_profile(user_id): Get a user's profile.
    - delete_user_profile(user_id): Delete a user's profile.
    - counsellor_exist(counsellor_id): Check if a counsellor exists.
    - save_counsellor(counsellor): Save a new counsellor.
    - get_counsellors_ids(): Get all counsellor IDs.
    - create_ticket(user_id, transcript): Create a support ticket.
    - get_ticket(ticket_id): Retrieve a ticket by ID.
    - update_ticket_status(ticket_id, status): Update ticket status.
    - get_open_tickets(): Get all open tickets.
    - get_memory(user_id): Retrieve messages for a user.
    - save_memory(message): Save a message to the database.
    - delete_memory(user_id): Delete all messages for a user.
    - delete_message(message_id): Delete a specific message by ID.
    - get_conversation_history(user_id): Get conversation history for a user.
    - clear_conversation_history(user_id): Clear conversation history for a user.
    - clear_all_data(): Clear all data in the database (for testing).
    - get_counsellor_channels(counsellor_id): Get channels for a counsellor.
    - get_counsellor_channel_id(counsellor_id, channel): Get channel ID for a counsellor and channel.
    - get_system_config(key, category): Get a system configuration value.
    - set_system_config(key, value, category): Set a system configuration value.
    - get_all_system_configs(category): Get all system configurations.
    - update_system_stats(): Update system statistics (users, messages, tickets).
"""
import datetime
import sqlite3
import os
import sys

# Add parent directory to path to allow imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.chat_data import get_chat_data 
import dotenv
import logging

dotenv.load_dotenv()

MODE = os.getenv("MODE")
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging_file = os.getenv('LOGGING_FILE', 'chatbot_log.log')
if logging_file:
    logging.basicConfig(filename=logging_file, level=getattr(logging, logging_level, logging.INFO))
else:
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO))
    #logging.info("Logging initialized without logging file.")

def connect_db():
    """
    Connect to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object.
    """
    logging.debug("Connecting to database")
    conn = sqlite3.connect('chatbot.db', timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    """
    Close the database connection.
    
    Args:
        conn (sqlite3.Connection): Database connection to close.
    """
    logging.debug("Closing database connection")
    conn.close()

def init_db():
    """
    Initialize the database with the schema from schema.sql file.
    
    Reads and executes the SQL schema file to create database tables.
    After initialization, applies any pending schema migrations.
    Prints confirmation message upon completion.
    """
    logging.info("Initializing database")
    cur = connect_db().cursor()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'schema.sql')
    
    try:
        with open(schema_path, encoding='utf-8', mode='r') as f:
            cur.executescript(f.read())
        logging.info("Database schema loaded successfully")
    except FileNotFoundError:
        logging.error(f"Schema file not found at: {schema_path}")
        print(f"Schema file not found. Please ensure 'schema.sql' exists at: {schema_path}")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        print("Error occurred while initializing the database:", e)
    finally:
        close_db(cur.connection)
    print("Initialized the database.")
    logging.info("Database initialization complete")
    
    # Apply any pending migrations
    try:
        from database.updates import apply_all_migrations
        print("\nChecking for schema updates...")
        apply_all_migrations()
    except Exception as e:
        logging.warning(f"Could not apply migrations: {e}")
        print(f"Warning: Could not apply migrations: {e}")

def user_exist(user_id):
    """
    Check if a user exists in the database.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        bool: True if user exists, False otherwise.
    """
    logging.debug(f"Checking if user exists: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    exists = cur.fetchone() is not None
    close_db(conn)
    logging.info(f"User {user_id} exists: {exists}")
    return True if exists else False

def save_user(user_id):
    """
    Save a new user to the database with default AI bot handler.
    
    Args:
        user_id (str): The unique identifier for the new user.
        
    Returns:
        bool: True if user was saved successfully.
    """
    logging.info(f"Attempting to save new user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, handler) VALUES (?, ?)", (user_id, "ai_bot"))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully saved user: {user_id} with handler: ai_bot")
    return True

def update_user_handler(user_id, handler):
    """
    Update the handler assigned to a user.
    
    Args:
        user_id (str): The unique identifier of the user.
        handler (str): The new handler to assign to the user.
        
    Returns:
        bool: True if handler was updated successfully.
    """
    logging.info(f"Updating handler for user {user_id} to: {handler}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET handler = ? WHERE id = ?", (handler, user_id))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully updated handler for user: {user_id}")
    return True

def update_user(user_id, field, data):
    """
    Update a specific field for a user.
    
    Args:
        user_id (str): The unique identifier of the user.
        field (str): The field to update ('handler' or 'profile_data').
        data (str): The new data for the specified field.
        
    Returns:
        bool: True if user was updated successfully.
        
    Raises:
        ValueError: If field name is not valid.
    """
    logging.debug(f"Attempting to update user {user_id}, field: {field}")
    conn = connect_db()
    cur = conn.cursor()
    if field not in ["handler", "auth_key", "gender", "age_range"]:
        logging.error(f"Invalid field name attempted: {field}")
        raise ValueError("Invalid field name")
    query = f"UPDATE users SET {field} = ? WHERE id = ?"
    cur.execute(query, (data, user_id))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully updated user {user_id}, field: {field}")
    return True

def get_user_count():
    """
    Get the total number of users in the database.
    
    Returns:
        int: Total count of users.
    """
    logging.debug("Retrieving total user count")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    close_db(conn)
    logging.info(f"Total user count: {count}")
    return count

def get_all_users():
    """
    Retrieve all users from the database.
    
    Returns:
        list: List of tuples containing user data.
    """
    logging.debug("Retrieving all users from database")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(users)} users from database")
    return users

def get_user_profile(user_id):
    """
    Get a user's profile data from the database.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        tuple or None: User profile data if found, None otherwise.
    """
    logging.debug(f"Retrieving profile for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    profile = cur.fetchone()
    close_db(conn)
    if profile:
        logging.info(f"Profile found for user: {user_id}")
    else:
        logging.warning(f"No profile found for user: {user_id}")
    return profile

def delete_user_profile(user_id):
    """
    Delete a user's profile from the database.
    
    Args:
        user_id (str): The unique identifier of the user to delete.
        
    Returns:
        bool: True if user was deleted successfully.
    """
    logging.info(f"Attempting to delete user profile: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully deleted user profile: {user_id}")
    return True

def counsellor_exist(counsellor):
    """
    Check if a counsellor exists in the database.
    
    Args:
        counsellor_id (str): The unique identifier of the counsellor.
        
    Returns:
        bool: True if counsellor exists, False otherwise.
    """
    logging.debug(f"Checking if counsellor exists: {counsellor}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM counsellors WHERE username = ?", (counsellor,))
    exists = cur.fetchone() is not None
    close_db(conn)
    logging.info(f"Counsellor {counsellor} exists: {exists}")
    return True if exists else False

def save_counsellor(counsellor):
    """
    Save a new counsellor to the database.
    
    Args:
        counsellor (dict): Dictionary containing counsellor data with keys:
                        'name', 'username' and 'email'.
                          
    Returns:
        bool: True if counsellor was saved successfully.
    """
    logging.info(f"Attempting to save new counsellor: {counsellor.get('name', 'Unknown')}")
    if not counsellor.get('username'):
        logging.error("Counsellor data missing 'username' key")
        return False
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO counsellors (name, username, email) VALUES (?, ?, ?)",
                (counsellor['name'], counsellor['username'], counsellor['email']))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully saved counsellor: {counsellor['username']}")
    return True

def get_counsellors():
    """
    Get all counsellor usernames from the database.
    
    Returns:
        list: List of counsellors usernames.
    """
    logging.debug("Retrieving all counsellor IDs")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM counsellors")
    usernames = [row[0] for row in cur.fetchall()]
    close_db(conn)
    logging.info(f"Retrieved {len(usernames)} counsellors usernames")
    return usernames

def get_counsellor(counsellor):
    """
    Get a counsellor's details by their ID.
    
    Args:
        counsellor (str): The username of the counsellor.
        
    Returns:
        dictionary or None: Counsellor data if found, None otherwise.
    """
    logging.debug(f"Retrieving counsellor details for: {counsellor}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM counsellors WHERE username = ?", (counsellor,))
    counsellor = cur.fetchone()
    close_db(conn)
    if counsellor:
        logging.info(f"Counsellor found: {counsellor}")
    else:
        logging.warning(f"No counsellor found with ID: {counsellor}")
    return counsellor

def get_counsellors_details():
    """Get all the counsellors in the database

    Returns:
        dict: A dictionary containing all counsellors.
    """
    logging.debug("Retrieving all counsellors")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM counsellors")
    counsellors = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(counsellors)} counsellors")
    return counsellors

def update_counsellor(counsellor, field, data):
    """Updates a field in a counsellor

    Args:
        counsellor (str): The username of the counsellor to update.
        field (str): The field to update (e.g., 'name', 'email').
        data (str): The new value for the field.
    
    Returns:
        status(bool):The status of the operation
    """
    logging.info(f"Attempting to update counsellor {counsellor}, field: {field}")
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE counsellors SET {field} = ? WHERE username = ?", (data, counsellor))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully updated counsellor {counsellor}, field: {field}")
        return True
    except Exception as e:
        logging.error(f"Error updating counsellor {counsellor}: {e}")
        close_db(conn)
        return False

def delete_counsellor(username):
    """Delete a counsellor from the database

    Args:
        username (str): The id of the counsellor to be deleted
    
    Return:
        bool: Status of the delete
    """
    logging.info(f"Attempting to delete counsellor: {username}")
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM counsellors WHERE username = ?", (username,))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully deleted counsellor: {username}")
        return True
    except Exception as e:
        logging.error(f"Error deleting counsellor {username}: {e}")
        return False

def create_ticket(user_id, ticket_id, transcript):
    """
    Create a new support ticket for a user.
    
    Args:
        user_id (str): The unique identifier of the user creating the ticket.
        ticket_id (str): The unique identifier of the ticket.
        transcript (str): The conversation transcript for the ticket.
        
    Returns:
        int: The ID of the newly created ticket.
    """
    logging.info(f"Creating ticket {ticket_id} for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tickets (id, user, transcript, status) VALUES (?, ?, ?, ?)",
                (ticket_id, user_id, transcript, "open"))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully created ticket: {ticket_id}")
    return ticket_id

def get_ticket(ticket_id):
    """
    Retrieve a ticket by its ID.
    
    Args:
        ticket_id (int): The unique identifier of the ticket.
        
    Returns:
        tuple or None: Ticket data if found, None otherwise.
    """
    logging.debug(f"Retrieving ticket: {ticket_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cur.fetchone()
    close_db(conn)
    if ticket:
        logging.info(f"Ticket found: {ticket_id}")
        return ticket
    else:
        logging.warning(f"No ticket found with ID: {ticket_id}")
        return None

def update_ticket_status(ticket_id, status):
    """
    Update the status of a ticket.
    
    Args:
        ticket_id (int): The unique identifier of the ticket.
        status (str): The new status ('open', 'in_progress', or 'closed').
        
    Returns:
        bool: True if ticket status was updated successfully.
        
    Raises:
        ValueError: If status is not valid.
    """
    logging.info(f"Updating ticket {ticket_id} status to: {status}")
    if status not in ["open", "in_progress", "closed"]:
        logging.error(f"Invalid status attempted: {status}")
        raise ValueError("Invalid status. Must be 'open', 'in_progress', or 'closed'.")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    if status == "closed":
        cur.execute("UPDATE tickets SET closed_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully updated ticket {ticket_id} status to: {status}")
    return True

def get_open_tickets():
    """
    Get all tickets with 'open' status.
    
    Returns:
        list: List of tuples containing open ticket data.
    """
    logging.debug("Retrieving all open tickets")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE status = 'open'")
    tickets = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(tickets)} open tickets")
    return tickets

def get_tickets():
    """
    Get all tickets from the database.
    
    Returns:
        list: List of tuples containing all ticket data.
    """
    logging.debug("Retrieving all tickets")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets")
    tickets = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(tickets)} total tickets")
    return tickets

def assign_ticket_handler(ticket_id, handler):
    """
    Assign a handler to a support ticket.
    
    Args:
        ticket_id (int): The unique identifier of the ticket.
        handler (str): The handler to assign to the ticket.
        
    Returns:
        bool: True if handler was assigned successfully.
    """
    logging.info(f"Assigning handler {handler} to ticket: {ticket_id}")
    conn = connect_db()
    cur = conn.cursor()
    #cur.execute("UPDATE users SET handler = ? WHERE id = (SELECT user FROM tickets WHERE id = ?)", (handler, ticket_id))
    if MODE == "no_counsellor":
        cur.execute("UPDATE users SET handler = 'counsellor' WHERE id = (SELECT user FROM tickets WHERE id = ?)", (ticket_id,))
        logging.debug(f"Mode: no_counsellor - Updated user handler to 'counsellor' for ticket {ticket_id}")
    if MODE == "single_counsellor":
        cur.execute("UPDATE counsellors SET current_ticket = ? WHERE id = ?", (ticket_id, handler))
        logging.debug(f"Mode: single_counsellor - Assigned ticket {ticket_id} to counsellor {handler}")
    else:
        cur.execute("UPDATE tickets SET handler = ? WHERE id = ?", (handler, ticket_id))
        cur.execute("UPDATE tickets SET status = 'in_progress' WHERE id = ?", (ticket_id,))
        #cur.execute("UPDATE tickets SET assigned_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
        cur.execute("INSERT INTO tickets_assignment (ticket_id, counsellor_id, assigned_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (ticket_id, handler))
        logging.debug(f"Mode: multi_counsellor - Assigned handler {handler} to ticket {ticket_id}")
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully assigned handler to ticket: {ticket_id}")
    return True

def get_memory(user_id):
    """
    Retrieve all messages for a specific user.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        list: List of tuples containing message data where user is sender or recipient.
    """
    logging.debug(f"Retrieving memory for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM messages WHERE _from = ? OR _to = ? OR id = ?", (user_id, user_id, user_id))
    result = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(result)} messages for user: {user_id}")
    return result

def save_memory(message, user_id, receiver_id=None):
    """
    Save a message to the database.
    
    Args:
        message (dict): Dictionary containing message data with keys:
                       'from', 'to', 'type', 'content', 'source', 'timestamp'.
        user_id(str): The unique identifier of the recipient (optional).
                       
    Returns:
        bool: True if message was saved successfully.
    """
    try:
        if isinstance(message, str):
            logging.warning("Received message as string, converting to dict")
            data = {
                "id": user_id if user_id else "unknown",
                "from": user_id if user_id else "unknown",
                "to": receiver_id if receiver_id else "ai_bot",
                "type": "text",
                "body": message,
                "source": "unknown",
                "timestamp": datetime.datetime.now().timestamp()
            }
            logging.debug(f"Converted string message to dict: {message}")
        else:
            logging.debug(f"Received message as dict: {message}")
            logging.debug("Formatting message for database insertion")
            data = get_chat_data(message)
            print(data)
        if 'to' not in data or not data['to']:
            data['to'] = receiver_id if receiver_id else "ai_bot"
        logging.debug(f"Saving message from: {data.get('from', 'unknown')}, message_data: {data}")
        print(f"Saving message from: {data.get('from', 'unknown')}, message_data: {data}")
        conn = connect_db()
        cur = conn.cursor()
        # Note: 'id' is auto-generated (SERIAL PRIMARY KEY), so we don't insert it
        cur.execute("INSERT INTO messages (_from, _to, _type, content, source, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (data['from'], data['to'], data['type'], data['body'], data['source'], data['timestamp']))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully saved message from: {data['from']}")
        return True
    except sqlite3.OperationalError as e:
        logging.error(f"Database locked error when saving message: {e}")
        print(f"Database is locked. Please close any other programs accessing the database.")
        return False
    except Exception as e:
        logging.error(f"Error saving message: {e}")
        return False

def delete_memory(user_id):
    """
    Delete all messages associated with a user.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        bool: True if messages were deleted successfully.
    """
    logging.info(f"Deleting all messages for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE from = ? OR to = ?", (user_id, user_id))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully deleted messages for user: {user_id}")
    return True

def delete_message(message_id):
    """
    Delete a specific message by its ID.
    
    Args:
        message_id (int): The unique identifier of the message to delete.
        
    Returns:
        bool: True if message was deleted successfully.
    """
    logging.info(f"Deleting message: {message_id}")
    conn =  connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully deleted message: {message_id}")
    return True

def get_conversation_history(user_id):
    """
    Get conversation history for a specific user.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        list: List of tuples containing (message, timestamp) ordered by timestamp.
    """
    logging.debug(f"Retrieving conversation history for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT message, timestamp FROM conversations WHERE user = ? ORDER BY timestamp", (user_id,))
    history = cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(history)} conversation entries for user: {user_id}")
    return history

def clear_conversation_history(user_id):
    """
    Clear all conversation history for a specific user.
    
    Args:
        user_id (str): The unique identifier of the user.
        
    Returns:
        bool: True if conversation history was cleared successfully.
    """
    logging.info(f"Clearing conversation history for user: {user_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM conversations WHERE user = ?", (user_id,))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully cleared conversation history for user: {user_id}")
    return True

def clear_all_data():
    """
    Clear all data in the database for testing purposes.
    
    Removes the entire database file and reinitializes it with the schema.
    
    Returns:
        bool: True if database was cleared and reinitialized successfully.
    """
    logging.warning("Clearing all database data - this is irreversible!")
    if os.path.exists('chatbot.db'):
        os.remove('chatbot.db')
        logging.info("Database file removed")
    init_db()
    logging.info("Database reinitialized with schema")
    return True

def add_counsellor_channel(counsellor_id, channel, channel_id, auth_key=None, order=None):
    """add a channel to a counsellor

    Args:
        counsellor_id (str): the counsellor's id 
        channel (str): channel's name
        channel_id (str): channels' id used for sending messages
        auth_key(str): auth key for the channel, default none
        order (int): the rank of the channel, default none
    
    Returns:
        bool: True if channel was added successfully.
    
    To do: 
        Add checks to make sure that channels that belong to the
        counsellor do not have the same rank(priority)

    """
    logging.info(f"Adding channel {channel} to counsellor: {id}")
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO channels (counsellor_id, channel, channel_id, auth_key, order) VALUES (?, ?, ?, ?, ?)",(counsellor_id, channel, channel_id, auth_key, order))
        conn.commit()
        logging.info(f"Successfully added channel {channel} to counsellor {counsellor_id}")
        return True
    except Exception as e:
        logging.error(f"Error adding channel to counsellor {counsellor_id}: {e}")
        return False

def get_counsellor_channels(counsellor_id):
    """
    Get the channels associated with a counsellor.
    
    Args:
        counsellor_id (str): The unique identifier of the counsellor.
        
    Returns:
        list: List of channels empty list if no channels found.
    """
    logging.debug(f"Retrieving channels for counsellor: {counsellor_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels WHERE counsellor_id = ?", (counsellor_id,))
    channels =  cur.fetchall()
    close_db(conn)
    logging.info(f"Retrieved {len(channels)} channels for counsellor: {counsellor_id}")
    return channels if channels else []

def get_counsellor_channel_id(counsellor_username, channel):
    """
    Get the channel ID for a specific counsellor and channel combination.
    
    Args:
        counsellor_username (str): The unique username of the counsellor.
        channel (str): The name of the channel.
        
    Returns:
        str or None: Channel ID if found, None otherwise.
    """
    logging.debug(f"Retrieving channel ID for counsellor {counsellor_username}, channel: {channel}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT channel_id FROM channels WHERE counsellor_username = ? AND channel = ?", (counsellor_username, channel))
    channel_id = cur.fetchone()
    close_db(conn)
    if channel_id:
        logging.info(f"Found channel ID for counsellor {counsellor_username}, channel {channel}")
    else:
        logging.warning(f"No channel ID found for counsellor {counsellor_username}, channel {channel}")
    return channel_id[0] if channel_id else None

def get_counsellor_token(counsellor_username, channel):
    """Get the authorisation token for a counsellor

    Args:
        counsellor_username (str): the username of the counsellor
        channel (str): the channel whose auth key is needed
        
    Returns:
        str or None: auth_key if found, None otherwise
    """
    logging.debug('Retrieving counsellor: %s authorisation key for channel: %s', counsellor_username, channel)
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT auth_key FROM channels where counsellor_username = ? AND channel = ?", (counsellor_username, channel))
    auth_key =  cur.fetchone()
    close_db(conn)
    if auth_key:
        logging.info("Auth key: %s found for counsellor_username: %s on channel: %s", auth_key, counsellor_username, channel)
    else:
        logging.warning("Auth key not found for counsellor: %s on channel: %s", counsellor_username, channel)
    return auth_key[0] if auth_key else None

def delete_counsellor_channel(counsellor_username, channel):
    """Delete a channel associated with a counsellor

    Args:
        counsellor_username (str): the username of the counsellor
        channel (str): the channel to be deleted
    
    Returns:
        bool: True if channel was deleted successfully
    """
    logging.info(f"Deleting channel {channel} for counsellor: {counsellor_username}")
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM channels WHERE counsellor_username = ? AND channel = ?", (counsellor_username, channel))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully deleted channel {channel} for counsellor: {counsellor_username}")
        return True
    except Exception as e:
        logging.error(f"Error deleting channel {channel} for counsellor {counsellor_username}: {e}")
        return False

def delete_all_counsellor_channels(counsellor_username):
    """Delete all channels associated with a counsellor

    Args:
        counsellor_username (str): the username of the counsellor
    
    Returns:
        bool: True if channels were deleted successfully
    """
    logging.info(f"Deleting all channels for counsellor: {counsellor_username}")
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM channels WHERE counsellor_username = ?", (counsellor_username,))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully deleted all channels for counsellor: {counsellor_username}")
        return True
    except Exception as e:
        logging.error(f"Error deleting channels for counsellor {counsellor_username}: {e}")
        return False

def update_counsellor_channel(counsellor_username, channel, field, data):
    """Updates a field in a counsellor's channel

    Args:
        counsellor_username (str): The username of the counsellor.
        channel (str): The channel to update.
        field (str): The field to update (e.g., 'auth_key', 'order').
        data (str): The new value for the field.
    
    Returns:
        status(bool):The status of the operation
    """
    logging.info(f"Attempting to update channel {channel} for counsellor {counsellor_username}, field: {field}")
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE channels SET {field} = ? WHERE counsellor_username = ? AND channel = ?", (data, counsellor_username, channel))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully updated channel {channel} for counsellor {counsellor_username}, field: {field}")
        return True
    except Exception as e:
        logging.error(f"Error updating channel {channel} for counsellor {counsellor_username}: {e}")
        close_db(conn)
        return False

# =============================================================================
# SYSTEM METADATA FUNCTIONS
# =============================================================================

def get_system_config(key, category='config'):
    """
    Get a system configuration value by key.
    
    Args:
        key (str): The configuration key to retrieve.
        category (str): The category of the config (default: 'config').
        
    Returns:
        The configuration value converted to appropriate type, or None if not found.
    """
    logging.debug(f"Retrieving system config: {category}.{key}")
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT value, data_type FROM system_metadata WHERE category = ? AND key = ?",
            (category, key)
        )
        result = cur.fetchone()
        
        if not result:
            logging.warning(f"System config not found: {category}.{key}")
            return None
        
        value, data_type = result
        
        # Convert value to appropriate type
        if data_type == 'int':
            return int(value) if value else 0
        elif data_type == 'bool':
            return value.lower() == 'true' if value else False
        elif data_type == 'json':
            import json
            return json.loads(value) if value else None
        else:  # string
            return value
            
    except Exception as e:
        logging.error(f"Error retrieving system config {category}.{key}: {e}")
        return None
    finally:
        close_db(conn)


def set_system_config(key, value, category='config'):
    """
    Set a system configuration value.
    
    Args:
        key (str): The configuration key to set.
        value: The value to set (will be converted to string).
        category (str): The category of the config (default: 'config').
        
    Returns:
        bool: True if successful, False otherwise.
    """
    logging.debug(f"Setting system config: {category}.{key} = {value}")
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Convert value to string based on type
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
        else:
            str_value = str(value)
        
        cur.execute(
            """UPDATE system_metadata 
               SET value = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE category = ? AND key = ? AND is_editable = 1""",
            (str_value, category, key)
        )
        conn.commit()
        
        if cur.rowcount == 0:
            logging.warning(f"System config {category}.{key} not found or not editable")
            return False
        
        logging.info(f"System config updated: {category}.{key} = {value}")
        return True
        
    except Exception as e:
        logging.error(f"Error setting system config {category}.{key}: {e}")
        conn.rollback()
        return False
    finally:
        close_db(conn)


def get_all_system_configs(category=None):
    """
    Get all system configuration values, optionally filtered by category.
    
    Args:
        category (str, optional): Filter by category. If None, returns all.
        
    Returns:
        dict: Dictionary of configuration values organized by category and key.
    """
    logging.debug(f"Retrieving all system configs" + (f" for category: {category}" if category else ""))
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        if category:
            cur.execute(
                """SELECT category, key, value, data_type, description, is_editable, updated_at 
                   FROM system_metadata WHERE category = ? ORDER BY category, key""",
                (category,)
            )
        else:
            cur.execute(
                """SELECT category, key, value, data_type, description, is_editable, updated_at 
                   FROM system_metadata ORDER BY category, key"""
            )
        
        rows = cur.fetchall()
        
        # Organize by category
        configs = {}
        for row in rows:
            cat, key, value, data_type, description, is_editable, updated_at = row
            
            if cat not in configs:
                configs[cat] = {}
            
            # Convert value to appropriate type
            if data_type == 'int':
                typed_value = int(value) if value else 0
            elif data_type == 'bool':
                typed_value = value.lower() == 'true' if value else False
            elif data_type == 'json':
                import json
                typed_value = json.loads(value) if value else None
            else:
                typed_value = value
            
            configs[cat][key] = {
                'value': typed_value,
                'data_type': data_type,
                'description': description,
                'is_editable': bool(is_editable),
                'updated_at': updated_at
            }
        
        logging.info(f"Retrieved {len(rows)} system config entries")
        return configs
        
    except Exception as e:
        logging.error(f"Error retrieving system configs: {e}")
        return {}
    finally:
        close_db(conn)


def update_system_stats():
    """
    Update system statistics (total users, messages, active tickets).
    Should be called periodically or after significant data changes.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    logging.debug("Updating system statistics")
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Count total users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        # Count total messages
        cur.execute("SELECT COUNT(*) FROM messages")
        total_messages = cur.fetchone()[0]
        
        # Count active tickets
        cur.execute("SELECT COUNT(*) FROM tickets WHERE status != 'closed'")
        active_tickets = cur.fetchone()[0]
        
        # Update stats in system_metadata
        stats_to_update = [
            ('stats', 'total_users', str(total_users)),
            ('stats', 'total_messages', str(total_messages)),
            ('stats', 'active_tickets', str(active_tickets))
        ]
        
        for category, key, value in stats_to_update:
            cur.execute(
                """UPDATE system_metadata 
                   SET value = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE category = ? AND key = ?""",
                (value, category, key)
            )
        
        conn.commit()
        logging.info(f"System stats updated: users={total_users}, messages={total_messages}, tickets={active_tickets}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating system stats: {e}")
        conn.rollback()
        return False
    finally:
        close_db(conn)


if __name__ == "__main__":
    init_db()
    print("Database initialized.")