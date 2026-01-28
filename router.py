
"""
Message Routing Module

This module handles the routing of messages to different API endpoints based on 
configuration settings. It provides functionality to dynamically route messages 
to various services using route configurations stored in a JSON file.

The module reads route configurations from 'routes.json' which contains API URLs,
authentication tokens, timeouts, and endpoint specifications for different services.

Functions:
    route_message(route_name, message): Route a message to the configured API endpoint

Configuration:
    Requires 'routes.json' file with route configurations containing:
    - API_URL: Base URL for the API
    - TOKEN: Authentication token for the API
    - timeout: Request timeout in seconds (default: 10)
    - endpoint: Specific endpoint path (default: 'messages/text')

Dependencies:
    json: For parsing route configuration files
    requests: For making HTTP API calls

Todo:
    - Handle other message types like images, files, etc.
    - Add support for different authentication methods
    - Implement retry logic for failed requests
"""

import json
import time
import random
import requests
import logging
import os
import dotenv
from requests_toolbelt import MultipartEncoder

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging_file = os.getenv('LOGGING_FILE', 'chatbot_log.log')
if logging_file:
    logging.basicConfig(filename=logging_file, level=getattr(logging, logging_level, logging.INFO))
else:
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO))


def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=60, backoff_factor=2):
    """
    Retry a function with exponential backoff.
    
    Args:
        func (callable): Function to retry
        max_retries (int): Maximum number of retry attempts (default: 3)
        base_delay (float): Base delay in seconds (default: 1)
        max_delay (float): Maximum delay in seconds (default: 60)
        backoff_factor (float): Multiplier for exponential backoff (default: 2)
        
    Returns:
        The result of the function call or raises the last exception
    """
    logging.debug(f"Starting retry logic with max_retries={max_retries}, base_delay={base_delay}")
    for attempt in range(max_retries + 1):
        try:
            logging.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
            result = func()
            if attempt > 0:
                logging.info(f"Request succeeded on attempt {attempt + 1}")
            return result
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if attempt == max_retries:
                logging.error(f"All retry attempts exhausted. Last error: {str(e)}")
                raise e
            
            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            jitter = random.uniform(0, 0.1) * delay  # Add up to 10% jitter
            total_delay = delay + jitter
            
            logging.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
            logging.info(f"Retrying in {total_delay:.2f} seconds...")
            print(f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
            print(f"Retrying in {total_delay:.2f} seconds...")
            time.sleep(total_delay)
    
    # This should never be reached due to the raise in the loop
    logging.critical("Reached unreachable code in retry_with_backoff")
    raise Exception("Max retries exceeded")


def route_message(route_name, user_id, message, message_type="text", max_retries=3):
    """
    Route a message to the appropriate API endpoint based on the route configuration.

    Args:
        route_name (str): The name of the route to use.
        message (str): The message to send to the API.
        user_id (str): The recipient user ID.
        max_retries (int): Maximum number of retry attempts (default: 3).

    Returns:
        dict: The JSON response from the API or an error message.
    """
    logging.info(f"Routing message to {route_name} for user {user_id}")
    logging.debug(f"Message type: {message_type}, Max retries: {max_retries}")
    
    try:
        logging.debug("Loading routes configuration from routes.json")
        with open("routes.json", encoding='utf-8', mode='r') as file:
            configurations = json.load(file)
            logging.debug(f"Loaded {len(configurations)} route configurations")

            # To Do handle other messages like images, files, etc.
            # Access specific keys in the config
            if route_name not in configurations:
                logging.error(f"Route {route_name} not found in configuration")
                return {"error": f"Route {route_name} not found in configuration."}
                
            config = configurations[route_name]
            logging.debug(f"Found configuration for route: {route_name}")
            
            api_url = config.get('api_url')
            token = config.get('api_token')
            timeout = config.get('timeout', 10)
            endpoint = config.get('endpoint')[message_type] if 'endpoint' in config and message_type in config['endpoint'] else 'messages/text'

            logging.debug(f"API URL: {api_url}, Endpoint: {endpoint}, Timeout: {timeout}")

            headers = {
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json'
            }
            

            url = f"{api_url}/{endpoint}"
            if message_type == 'text':
                payload = {'body': message}
            elif message_type == 'media' or message_type == 'image' or message_type == 'file':
                # Split the media path and MIME type for image
                image_path, mime_type = payload.pop('media').split(';')
        
                with open(image_path, 'rb') as image_file:
                    # Create a MultipartEncoder for the file upload
                    m = MultipartEncoder(
                        fields={
                            **payload,
                            'media': (image_path, image_file, mime_type)
                        }
                    )
                    headers['Content-Type'] = m.content_type
            elif message_type == 'options':
                payload = {
                    'body': message['body'],
                    'action': message['action'],
                    'type': message.get('type', 'button')
                }
            payload['to'] = user_id
            
            logging.debug(f"Prepared request to {url}")
            logging.debug(f"Payload: {payload}")

            # Define the request function for retry logic
            def make_request():
                logging.debug(f"Making POST request to {url}")
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                # Raise an exception for bad status codes (4xx, 5xx)
                response.raise_for_status()
                logging.info(f"Request successful. Status code: {response.status_code}")
                return response.json()

            # Use retry logic for the request
            try:
                result = retry_with_backoff(make_request, max_retries=max_retries)
                logging.info(f"Message successfully routed to {route_name} for user {user_id}")
                return result
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed after {max_retries + 1} attempts: {str(e)}"
                logging.error(error_msg)
                return {"error": error_msg}

    except FileNotFoundError:
        error_msg = f"Configuration file for {route_name} not found."
        logging.error(error_msg)
        return {"error": error_msg}
    except json.JSONDecodeError:
        error_msg = f"Error decoding JSON configuration for {route_name}."
        logging.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error routing message to {route_name}: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

if __name__ == "__main__":
    # check if config file is loaded correctly
    logging.info("Testing routes.json configuration loading")
    try:
        with open("routes.json", encoding='utf-8', mode='r') as file:
            configurations = json.load(file)
            print("Loaded configurations:", configurations)
            logging.info(f"Successfully loaded {len(configurations)} route configurations")
            for route_name in configurations:
                logging.debug(f"Available route: {route_name}")
    except Exception as e:
        error_msg = f"Error loading configurations: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
