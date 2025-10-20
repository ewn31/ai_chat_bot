"""
Improved version of chat_data functions with better error handling
"""

def get_chat_data_improved(chat):
    """
    Improved version of get_chat_data with better error handling.
    
    Args:
        chat (dict): A chat object from WhatsApp API
        
    Returns:
        dict: A standardized chat object with the following fields:
        {
            id: string,
            from: string,
            source: string,
            status: string,
            type: string,
            body: string,
            timestamp: number
        }
    """
    # Initialize data item with default values
    data_item = {
        'id': '',
        'status': '',
        'from': '',
        'type': '',
        'source': '',
        'timestamp': 0,
        'body': ''
    }
    
    # Safely extract chat_id with fallback
    if 'chat_id' in chat:
        data_item['id'] = chat['chat_id']
    elif 'from' in chat:
        # Use 'from' as fallback for id
        data_item['id'] = chat['from']
    else:
        # Generate a placeholder id
        data_item['id'] = f"unknown_{chat.get('timestamp', 'no_timestamp')}"
    
    # Extract standard fields safely
    keys_to_extract = ['status', 'from', 'type', 'source', 'timestamp']
    for key in keys_to_extract:
        if key in chat:
            data_item[key] = chat[key]
    
    # Extract message body based on type
    if 'type' in chat:
        message_type = chat['type']
        data_item['body'] = extract_message_body(chat, message_type)
    
    return data_item

def extract_message_body(chat, message_type):
    """
    Extract message body based on message type.
    
    Args:
        chat (dict): The chat object
        message_type (str): The type of message
        
    Returns:
        str: The extracted message body
    """
    try:
        if message_type == 'text' and 'text' in chat:
            return chat['text'].get('body', '')
            
        elif message_type == 'document' and 'document' in chat:
            return chat['document'].get('filename', 'document')
            
        elif message_type == 'reply' and 'reply' in chat:
            if 'buttons_reply' in chat['reply']:
                return chat['reply']['buttons_reply'].get('title', '')
            return 'reply message'
            
        elif message_type == 'interactive' and 'interactive' in chat:
            return chat['interactive'].get('body', 'interactive message')
            
        elif message_type == 'image' and 'image' in chat:
            caption = chat['image'].get('caption', '')
            return caption if caption else 'image message'
            
        elif message_type == 'audio' and 'audio' in chat:
            duration = chat['audio'].get('duration', 0)
            return f'audio message ({duration}s)' if duration else 'audio message'
            
        elif message_type == 'video' and 'video' in chat:
            caption = chat['video'].get('caption', '')
            return caption if caption else 'video message'
            
        elif message_type == 'location' and 'location' in chat:
            return 'location shared'
            
        elif message_type == 'contact' and 'contact' in chat:
            name = chat['contact'].get('name', {}).get('formatted_name', '')
            return f'contact: {name}' if name else 'contact shared'
            
        else:
            return f'{message_type} message'
            
    except (KeyError, TypeError, AttributeError) as e:
        # If anything goes wrong, return a safe default
        return f'{message_type} message (parse error)'

def get_users_data_improved(chats):
    """
    Improved version of get_users_data with better error handling.
    
    Args:
        chats (list): A list of chat objects from WhatsApp API
        
    Returns:
        list: A list of standardized chat objects
    """
    data = []
    
    if chats is None:
        print('Chat list is None')
        return data
        
    if not isinstance(chats, list):
        print(f'Expected list, got {type(chats)}')
        return data
    
    for i, chat in enumerate(chats):
        try:
            if not isinstance(chat, dict):
                print(f'Skipping non-dict item at index {i}: {type(chat)}')
                continue
                
            processed_chat = get_chat_data_improved(chat)
            data.append(processed_chat)
            
        except Exception as e:
            print(f'Error processing chat at index {i}: {str(e)}')
            # Optionally, you can still add a minimal data item:
            # data.append({
            #     'id': f'error_{i}',
            #     'status': 'error',
            #     'from': '',
            #     'type': 'error',
            #     'source': '',
            #     'timestamp': 0,
            #     'body': f'Processing error: {str(e)}'
            # })
    
    return data

def validate_chat_structure(chat):
    """
    Validate that a chat object has the minimum required structure.
    
    Args:
        chat (dict): Chat object to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(chat, dict):
        return False, f"Chat must be a dictionary, got {type(chat)}"
    
    # Check for at least one identifier
    if not any(key in chat for key in ['chat_id', 'from', 'id']):
        return False, "Chat must have at least one of: 'chat_id', 'from', or 'id'"
    
    # Check for timestamp (optional but recommended)
    if 'timestamp' in chat and not isinstance(chat['timestamp'], (int, float)):
        return False, "Timestamp must be a number"
    
    return True, "Valid"

# Test the improved functions
if __name__ == "__main__":
    # Test data including problematic cases
    test_cases = [
        # Normal case
        {
            "chat_id": "1234567890@c.us",
            "from": "1234567890@c.us",
            "type": "text",
            "text": {"body": "Hello world"},
            "timestamp": 1696291200,
            "status": "received",
            "source": "whatsapp"
        },
        
        # Missing chat_id
        {
            "from": "1234567890@c.us",
            "type": "text",
            "text": {"body": "No chat_id"},
            "timestamp": 1696291200
        },
        
        # Missing everything except timestamp
        {
            "timestamp": 1696291200
        },
        
        # Completely empty
        {},
        
        # Audio message
        {
            "chat_id": "audio_user@c.us",
            "type": "audio",
            "audio": {"duration": 30},
            "timestamp": 1696291200
        }
    ]
    
    print("Testing improved functions:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input: {test_case}")
        
        # Validate
        is_valid, message = validate_chat_structure(test_case)
        print(f"Validation: {message}")
        
        # Process
        try:
            result = get_chat_data_improved(test_case)
            print(f"Output: {result}")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n{'='*50}")
    print("Testing batch processing:")
    
    results = get_users_data_improved(test_cases)
    print(f"Processed {len(results)} out of {len(test_cases)} items")
    
    for result in results:
        print(f"- {result['type']} from {result['id']}: {result['body'][:30]}...")