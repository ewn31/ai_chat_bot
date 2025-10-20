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
    if field not in ["handler", "profile_data"]:
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

def counsellor_exist(counsellor_id):
    """
    Check if a counsellor exists in the database.
    
    Args:
        counsellor_id (str): The unique identifier of the counsellor.
        
    Returns:
        bool: True if counsellor exists, False otherwise.
    """
    logging.debug(f"Checking if counsellor exists: {counsellor_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM counsellors WHERE id = ?", (counsellor_id,))
    exists = cur.fetchone() is not None
    close_db(conn)
    logging.info(f"Counsellor {counsellor_id} exists: {exists}")
    return True if exists else False

def save_counsellor(counsellor):
    """
    Save a new counsellor to the database.
    
    Args:
        counsellor (dict): Dictionary containing counsellor data with keys:
                        'name', and 'email'.
                          
    Returns:
        bool: True if counsellor was saved successfully.
    """
    logging.info(f"Attempting to save new counsellor: {counsellor.get('name', 'Unknown')}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO counsellors (name, email) VALUES (?, ?)",
                (counsellor['name'], counsellor['email']))
    conn.commit()
    close_db(conn)
    logging.info(f"Successfully saved counsellor: {counsellor['name']}")
    return True

def get_counsellors_ids():
    """
    Get all counsellor IDs from the database.
    
    Returns:
        list: List of counsellor IDs.
    """
    logging.debug("Retrieving all counsellor IDs")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM counsellors")
    ids = [row[0] for row in cur.fetchall()]
    close_db(conn)
    logging.info(f"Retrieved {len(ids)} counsellor IDs")
    return ids

def get_counsellor(counsellor_id):
    """
    Get a counsellor's details by their ID.
    
    Args:
        counsellor_id (str): The unique identifier of the counsellor.
        
    Returns:
        tuple or None: Counsellor data if found, None otherwise.
    """
    logging.debug(f"Retrieving counsellor details for: {counsellor_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM counsellors WHERE id = ?", (counsellor_id,))
    counsellor = cur.fetchone()
    close_db(conn)
    if counsellor:
        logging.info(f"Counsellor found: {counsellor_id}")
    else:
        logging.warning(f"No counsellor found with ID: {counsellor_id}")
    return counsellor

def get_counsellors():
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
        counsellor (str): The ID of the counsellor to update.
        field (str): The field to update (e.g., 'name', 'email').
        data (str): The new value for the field.
    
    Returns:
        status(bool):The status of the operation
    """
    logging.info(f"Attempting to update counsellor {counsellor}, field: {field}")
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE counsellors SET {field} = ? WHERE id = ?", (data, counsellor))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully updated counsellor {counsellor}, field: {field}")
        return True
    except Exception as e:
        logging.error(f"Error updating counsellor {counsellor}: {e}")
        close_db(conn)
        return False

def delete_counsellor(counsellor_id):
    """Delete a counsellor from the database

    Args:
        counsellor_id (str): The id of the counsellor to be deleted
    
    Return:
        bool: Status of the delete
    """
    logging.info(f"Attempting to delete counsellor: {counsellor_id}")
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM counsellors WHERE id = ?", (counsellor_id,))
        conn.commit()
        close_db(conn)
        logging.info(f"Successfully deleted counsellor: {counsellor_id}")
        return True
    except Exception as e:
        logging.error(f"Error deleting counsellor {counsellor_id}: {e}")
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
    else:
        logging.warning(f"No ticket found with ID: {ticket_id}")
    return ticket

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
        cur.execute("UPDATE tickets SET assigned_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
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

def save_memory(message, user_id=None):
    """
    Save a message to the database.
    
    Args:
        message (dict): Dictionary containing message data with keys:
                       'from', 'to', 'type', 'content', 'source', 'timestamp'.
                       
    Returns:
        bool: True if message was saved successfully.
    """
    try:
        if isinstance(message, str):
            logging.warning("Received message as string, converting to dict")
            data = {
                "id": user_id if user_id else "unknown",
                "from": user_id if user_id else "unknown",
                "to": "bot",
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
            data['to'] = 'ai_bot'
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

def add_counsellor_channel(id, channel, channel_id, order):
    """add a channel to a counsellor

    Args:
        id (str): counsellors' id
        channel (str): channel's name
        channel_id (str): channels' id used for sending messages
        order (int): the rank of the channel
    
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
        cur.execute("INSERT INTO channels (counsellor_id, channel, channel_id, order) VALUES (?, ?, ?, ?)",(id, channel, channel_id, order))
        conn.commit()
        logging.info(f"Successfully added channel {channel} to counsellor {id}")
        return True
    except Exception as e:
        logging.error(f"Error adding channel to counsellor {id}: {e}")
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

def get_counsellor_channel_id(counsellor_id, channel):
    """
    Get the channel ID for a specific counsellor and channel combination.
    
    Args:
        counsellor_id (str): The unique identifier of the counsellor.
        channel (str): The name of the channel.
        
    Returns:
        str or None: Channel ID if found, None otherwise.
    """
    logging.debug(f"Retrieving channel ID for counsellor {counsellor_id}, channel: {channel}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT channel_id FROM channels WHERE counsellor_id = ? AND channel = ?", (counsellor_id, channel))
    channel_id = cur.fetchone()
    close_db(conn)
    if channel_id:
        logging.info(f"Found channel ID for counsellor {counsellor_id}, channel {channel}")
    else:
        logging.warning(f"No channel ID found for counsellor {counsellor_id}, channel {channel}")
    return channel_id[0] if channel_id else None

if __name__ == "__main__":
    init_db()
    print("Database initialized.")