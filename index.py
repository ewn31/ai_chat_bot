import os
from flask import Flask, request
from dotenv import load_dotenv
from chat_handler import incoming_messages

load_dotenv()  # Load environment variables from a .env file

app = Flask(__name__)

       

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
                reply =  message.get('reply')
                print('reply-object: ', reply.get('type')=='buttons_reply' )
                if reply.get('type') == 'buttons_reply':
                    buttons_reply = reply.get('buttons_reply')
                    button_id = buttons_reply.get('id')
                    print('button_id: ',button_id)
                    _, user_response = button_id.split(':')
                    print(user_response)
                    #handler(bots, user_response, user_id)
            elif response_type == 'unknown':
                continue
            else:
                user_response = None
                #handler(bots, user_response, user_id)
        return 'Ok', 200
    
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')), debug=True)
