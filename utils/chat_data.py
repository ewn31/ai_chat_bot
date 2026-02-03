"""This module is used to get chats from the platform and extract user ids from the chats"""
import argparse
import json
import sys
import os
import csv
from enum import Enum
from datetime import datetime, date
import requests
#from dotenv import load_dotenv


#load_dotenv()  # Load environment variables from a .env file

#url = 'https://gate.whapi.cloud'
#token = 'qqzjkILSTfrV3eLZdeiDE5DrRftgk0EB'

url = os.getenv('API_URL') or 'https://gate.whapi.cloud'
token = os.getenv('API_TOKEN') or 'qqzjkILSTfrV3eLZdeiDE5DrRftgk0EB'
NUMBER_OF_DAYS = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31  ]
class Months(Enum):
    JAN = 0
    FEB = 1
    MAR = 2
    APR = 3
    MAY = 4
    JUN = 5
    JLY = 6
    AUG = 7
    SEP = 8
    OCT = 9
    NOV = 10
    DEC = 11
SYSTEM_START_MONTH = 3
INITIAL_TIME = 1746403200
COUNTS = 500

#FROM = 1746057600
#TO = 1746403200

def getChats(count, intial_time, to):
    """Gets chats from the platform

    Returns:
        List: List of chat objects
    """
    try:
        res = requests.get(url + f'/messages/list?count={count}&time_from={intial_time}&time_to={to}', headers={'Authorization': 'Bearer ' + token})
        if res.ok:
            return res.json()['messages']
    except requests.exceptions.RequestException as e:
        print('Error: ', e)

def getUserIdsFromChats(chats):
    """Gets the ids of users who have used the platforms

    Args:
        chats (List): List of chats objects

    Returns:
        List: A list user ids
    """
    if type(chats) == 'NoneType':
        print('List is empty')
    else:
        user_ids = []
        for chat in chats:
            print(chat)
            user_ids.append(chat['chat_id'])
        return list(set(user_ids))
    
def get_users_data(chats):
    
    """ Get the chat data
    
    Args:
        chats (list): A list of chat objects
        
    Returns:
        list: A list of chat objects with the following fields
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
    data = []
    if chats is None:
        print('List is empty')
        return data
    for chat in chats:
        #print(chat)
        data_item = {}
        data_item['id'] =  chat['chat_id']
        keys_to_extract = ['status', 'from', 'type', 'source', 'timestamp',]
        for key in keys_to_extract:
            if key in chat:
                data_item[key] = chat[key]
            else:
                if key == 'timestamp':
                    data_item[key] = 0
                else:
                    data_item[key] = ""
        if 'type' in chat:
            type_of_chat = chat['type']
            if type_of_chat == 'text':
                data_item['body'] = chat[type_of_chat]['body']
            elif type_of_chat == 'document':
                data_item['body'] = chat[type_of_chat]['filename']
            elif type_of_chat == 'reply':
                data_item['body'] = chat[type_of_chat]['buttons_reply']['title']
            elif type_of_chat == 'interactive':
                data_item['body'] = chat[type_of_chat]['body']
        #print(data_item)
        data.append(data_item)
    #print(data)
    return data

def get_chat_data(chat):
    """ Get the chat data
    
    Args:
        chat (dict): A chat object
        
    Returns:
        dict: A chat object with the following fields
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
    data_item = {}
    # Safely extract chat_id with fallback
    if 'chat_id' in chat:
        data_item['id'] = chat['chat_id']
    elif 'from' in chat:
        # Use 'from' as fallback for id
        data_item['id'] = chat['from']
    else:
        # Generate a placeholder id
        data_item['id'] = f"unknown_{chat.get('timestamp', 'no_timestamp')}"
    if "from_me" in chat:
        if chat['from_me']:
            data_item['from'] = 'ai_bot'
            data_item['to'] = data_item['id']
        else:
            data_item['from'] = data_item['id']
    elif "from" in chat:
        data_item['from'] = chat['from']
    if "to" in chat:
        data_item['to'] = chat['to']
    keys_to_extract = ['status', 'type', 'source', 'timestamp',]
    for key in keys_to_extract:
        if key in chat:
            data_item[key] = chat[key]
        else:
            if key == 'timestamp':
                data_item[key] = 0
            else:
                data_item[key] = ""
    if 'type' in chat:
        type_of_chat = chat['type']
        if type_of_chat == 'text':
            data_item['body'] = chat[type_of_chat]['body']
            # Check if this is a button message with an 'id' field
            if 'id' in chat:
                data_item['button_id'] = chat['id']
        elif type_of_chat == 'document':
            data_item['body'] = chat[type_of_chat]['filename']
        elif type_of_chat == 'reply':
            # Extract both button title and button ID
            buttons_reply = chat[type_of_chat].get('buttons_reply', {})
            data_item['body'] = buttons_reply.get('title', '')
            # Store button ID separately so it doesn't conflict with chat_id
            # if 'id' in buttons_reply:
            #     data_item['button_id'] = buttons_reply['id']
        elif type_of_chat == 'interactive':
            data_item['body'] = chat[type_of_chat]['body']
    return data_item

def export_data_to_csv(chat_data, filename=None):
    """Exports data to a csv file

    Args:
        data (list): a list of chats
    """
    if not filename:
        filename = 'chat_bot_data.csv'
    
    file_exist = os.path.exists(filename)
    with open(filename, 'a' , encoding='utf-8', newline='') as csv_file:
        fields = ['id', 'from', 'type', 'source', 'status', 'body', 'timestamp']
        csv_writer =  csv.DictWriter(csv_file, fieldnames=fields)
        if not file_exist:
            csv_writer.writeheader()
        for item in chat_data:
            csv_writer.writerow(item)
        print('Writing Data Done')
    

if __name__ == '__main__':
    import argparse
    import re

    parser = argparse.ArgumentParser(description='Get chats from the platform and extract user data from the chats'
                                        ' and export to a csv file')
    parser.add_argument('--count', "-c", type=int, default=COUNTS, help='Number of chats to get', required=False)
    parser.add_argument('--start', "-s", type=str,  help='From timestamp. Should be in the format YYYY-MM-DD HH:MM', default=date.fromtimestamp(INITIAL_TIME).strftime('%Y-%m-%d %H:%M'))
    parser.add_argument('--stop', "-e", type=str,  help='To timestamp. Should be in the format YYYY-MM-DD HH:MM', default=date.fromtimestamp(0).strftime('%Y-%m-%d'))
    parser.add_argument('--export', "-x", type=str,  help='Filename to export data to', default='chat_bot_data.csv', required=False)

    args = parser.parse_args()

    count = args.count
    
    if count <= 0:
        print('Error: Count should be greater than 0')
        sys.exit(1)
    
    start_time = args.start
    if not start_time:
        start_time = input('Start time (YYYY-MM-DD HH:MM): ').strip()
        
    if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', start_time):
        print('Error: Start time should be in the format YYYY-MM-DD HH:MM')
        sys.exit(1)
    
    stop_time = args.stop
    if not stop_time:
        stop_time = input('Stop time (YYYY-MM-DD HH:MM): ').strip()
    if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', stop_time):
        print('Error: Stop time should be in the format YYYY-MM-DD HH:MM')
        sys.exit(1)
    
    export_filename = args.export
    
    #start_month = int(re.search(r'\-(\d{2})\-', start_time).group(1))
    #end_month = int(re.search(r'\-(\d{2})\-', stop_time).group(1))
    from_timestamp = int(datetime.strptime(start_time, '%Y-%m-%d %H:%M').timestamp())
    to_timestamp = int(datetime.strptime(stop_time, '%Y-%m-%d %H:%M').timestamp())
    
    #verify if from_timestamp is less than to_timestamp
    if from_timestamp >= to_timestamp:
        print('Error: From timestamp should be less than To timestamp')
        sys.exit(1)
    
    stop = 0
    print(f'Exporting data to {export_filename}')
    
    while from_timestamp < to_timestamp:
        if to_timestamp - from_timestamp < 86400:
            stop = to_timestamp
        else:
            stop = from_timestamp + 86400
        print(f'Getting chats from {datetime.fromtimestamp(from_timestamp).strftime("%a %d %b %Y, %I:%M%p")} to {datetime.fromtimestamp(stop).strftime("%a %d %b %Y, %I:%M%p")}')
        chats = getChats(COUNTS, from_timestamp, stop)
        data = get_users_data(chats)
        export_data_to_csv(data, filename=export_filename)
        from_timestamp = stop

    print('Done')