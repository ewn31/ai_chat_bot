import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from chat_handler import incoming_messages
import counsellors
import database.db as db
import logging
from counsellor_handler import create_counsellor

load_dotenv()  # Load environment variables from a .env file

app = Flask(__name__)

# Configure logging
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logger = logging.getLogger(__name__)

       

# The Webhook link to your server is set in the dashboard. For this script it is important that the link is in the format: {link to server}/hook.
@app.route('/hook/messages', methods=['POST'])
def handle_new_messages():
    
    try:
        print('Webhook requests: ', request.json)
        messages = request.json.get('messages', [])
        #events = request.json.get('event')
        
        for message in messages:
            print(message)
            # Ignore messages from the bot itself
            if message.get('from_me'):
                continue

            response_type = message.get('type', {}).strip().lower()
            print(response_type)
            user_id = message.get('chat_id')

            if response_type == 'text':
                user_response = message.get('text', {}).get('body', '').strip().lower()
                print(user_response)
                #handler(bots, user_response, user_id)
                incoming_messages(user_id, message)
            #To do complete handling of other message types
            elif response_type == 'reply':
                reply = message.get('reply')
                print('reply-object: ', reply.get('type')=='buttons_reply')
                if reply.get('type') == 'buttons_reply':
                    buttons_reply = reply.get('buttons_reply')
                    button_id = buttons_reply.get('id')
                    button_title = buttons_reply.get('title', '')

                    print('button_id:', button_id)
                    print('button_title:', button_title)

                    # Create a properly formatted message object for incoming_messages
                    # Include both the button ID and the button text
                    # button_message = {
                    #      'type': 'text',
                    #      'text': {
                    #          'body': button_title  # The visible text on the button
                    #      },
                    #      'id': button_id  # The button ID for identification
                    # }
                    incoming_messages(user_id, message)
            elif response_type == 'unknown':
                continue
            else:
                user_response = None
                #handler(bots, user_response, user_id)
        return 'Ok', 200
    
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    print("webhook request: ", request.json)
    # Process the webhook request here
    webhook_data = (request.json).get('data')
    message = {}
    if webhook_data.get('text'):
        message['type'] = 'text'
        message['text'] = {'body': webhook_data['text']}
    else:
        print("Unsupported message type from webhook:", webhook_data)
        return 'Unsupported message type', 400
    user_id = webhook_data.get('sender_id')
    message['from'] = user_id
    message['timestamp'] = webhook_data['created_at']
    message['source'] = 'chat_app'
    reciever_id = webhook_data.get('room').split('_')[1]
    message['to'] = reciever_id
    incoming_messages(user_id, message, reciever_id)
    return 'Webhook received', 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'


# =============================================================================
# COUNSELLOR CRUD API ENDPOINTS
# =============================================================================

@app.route('/api/counsellors', methods=['GET'])
def get_all_counsellors():
    """Get all counsellors with their details."""
    try:
        counsellors_data = db.get_counsellors_details()
        
        # Convert to list of dictionaries
        counsellors_list = []
        for counsellor in counsellors_data:
            counsellors_list.append({
                'id': counsellor[0],
                'name': counsellor[1],
                'username': counsellor[2],
                'password': counsellor[3],  # You may want to exclude this in production
                'email': counsellor[4],
                'phone': counsellor[5],
                'channels': counsellor[6],
                'current_ticket': counsellor[7]
            })
        
        logger.info(f"Retrieved {len(counsellors_list)} counsellors")
        return jsonify({
            'success': True,
            'count': len(counsellors_list),
            'counsellors': counsellors_list
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving counsellors: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/counsellors/<username>', methods=['GET'])
def get_counsellor(username):
    """Get a specific counsellor by username."""
    try:
        counsellor = db.get_counsellor(username)
        
        if not counsellor:
            return jsonify({
                'success': False,
                'error': f'Counsellor with username "{username}" not found'
            }), 404
        
        counsellor_data = {
            'id': counsellor[0],
            'name': counsellor[1],
            'username': counsellor[2],
            'password': counsellor[3],  # You may want to exclude this in production
            'email': counsellor[4],
            'phone': counsellor[5],
            'channels': counsellor[6],
            'current_ticket': counsellor[7]
        }
        
        logger.info(f"Retrieved counsellor: {username}")
        return jsonify({
            'success': True,
            'counsellor': counsellor_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving counsellor {username}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/counsellors', methods=['POST'])
def create_counsellor_endpoint():
    """Create a new counsellor."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        required_fields = ['username', 'email']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Extract data
        username = data['username']
        email = data['email']
        name = data.get('name', username)  # Default to username if name not provided
        password = data.get('password', '')
        phone = data.get('phone')
        whatsapp = data.get('whatsapp')
        
        # Normalize WhatsApp number if provided
        if whatsapp:
            whatsapp = whatsapp.strip()
            # Remove @s.whatsapp.net if present
            if '@s.whatsapp.net' in whatsapp:
                whatsapp = whatsapp.replace('@s.whatsapp.net', '')
        
        # Use counsellor_handler's create_counsellor function
        # This handles: DB insertion, channel addition, chat app provisioning, magic link sending
        try:
            create_counsellor(username, password, email, name=name, whatsapp_number=whatsapp)
            
            logger.info(f"Successfully created counsellor: {username}")
            return jsonify({
                'success': True,
                'message': f'Counsellor "{username}" created successfully',
                'counsellor': {
                    'username': username,
                    'email': email,
                    'name': name,
                    'whatsapp': whatsapp if whatsapp else None
                }
            }), 201
            
        except Exception as e:
            logger.error(f"Error in create_counsellor function: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to create counsellor: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"Error creating counsellor: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/counsellors/<username>', methods=['PUT', 'PATCH'])
def update_counsellor(username):
    """Update a counsellor's information."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if counsellor exists
        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({
                'success': False,
                'error': f'Counsellor with username "{username}" not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = ['name', 'email', 'phone', 'password']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data:
                if db.update_counsellor(username, field, data[field]):
                    updated_fields.append(field)
                else:
                    logger.warning(f"Failed to update field {field} for counsellor {username}")
        
        if updated_fields:
            logger.info(f"Updated counsellor {username}: {', '.join(updated_fields)}")
            return jsonify({
                'success': True,
                'message': f'Counsellor "{username}" updated successfully',
                'updated_fields': updated_fields
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
    
    except Exception as e:
        logger.error(f"Error updating counsellor {username}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/counsellors/<username>', methods=['DELETE'])
def delete_counsellor(username):
    """Delete a counsellor."""
    try:
        # Check if counsellor exists
        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({
                'success': False,
                'error': f'Counsellor with username "{username}" not found'
            }), 404
        
        # Delete counsellor
        if counsellors.remove_counsellor(username):
            logger.info(f"Successfully deleted counsellor: {username}")
            return jsonify({
                'success': True,
                'message': f'Counsellor "{username}" deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete counsellor'
            }), 500
    
    except Exception as e:
        logger.error(f"Error deleting counsellor {username}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/counsellors/<username>/channels', methods=['POST'])
def add_counsellor_channel(username):
    """Add a channel to a counsellor."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['channel', 'channel_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Check if counsellor exists
        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({
                'success': False,
                'error': f'Counsellor with username "{username}" not found'
            }), 404
        
        # Add channel
        if counsellors.add_channel(
            username,
            data['channel'],
            data['channel_id'],
            data.get('auth_key'),
            data.get('order')
        ):
            logger.info(f"Successfully added channel {data['channel']} to counsellor {username}")
            return jsonify({
                'success': True,
                'message': f'Channel "{data["channel"]}" added to counsellor "{username}"'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add channel'
            }), 500
    
    except Exception as e:
        logger.error(f"Error adding channel to counsellor {username}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')), debug=True)
