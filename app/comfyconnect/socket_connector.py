
import uuid
import json
import urllib.request
import urllib.parse
from PIL import Image
from websocket import WebSocket # note: websocket-client (https://github.com/websocket-client/websocket-client)
import io
import requests
import time
import os
import subprocess
from typing import List
import sys
from core.config import Settings
import logging
from api.logger import logger_main
# Load settings from config.env
settings = Settings()
logger_main = logging.getLogger('logger_main')

APP_NAME = settings.APP_NAME
COMFY_URL = settings.COMFY_URL
SAVE_DIR = settings.SAVE_DIR
INSTANCE_IDENTIFIER = APP_NAME+'-'+str(uuid.uuid4()) # Unique identifier for this instance of the worker

class ComfyConnector:
    _instance = None
    _process = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ComfyConnector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.server_address = COMFY_URL
            self.client_id = INSTANCE_IDENTIFIER
            address = 'wss' if 'https' in self.server_address else 'ws'
            self.ws_address = f"{address}://{COMFY_URL.split('//')[-1]}/ws?clientId={self.client_id}"
            self.ws = WebSocket()
            self.connect()
            self.initialized = True

    # This method is used to connect to comfyui web server and create a WebSocket connection
    def connect(self):
        retry_attempts = 0
        retry_limit = 5  # Maximum number of retry attempts
        backoff_factor = 2  # Determines how much the wait time increases after each retry
        initial_wait_time = 1  # Initial wait time in seconds before the first retry

        while retry_attempts < retry_limit:
            try:
                logger_main.info(f"Checking web server is running in {self.server_address}...")
                response = requests.get(self.server_address)
                if response.status_code == 200:
                    self.ws.connect(self.ws_address)
                    logger_main.info(f"Comfyui Web server is running (status code 200). Now created connection with comfyui.")
                    return True
            except Exception as e:
                logger_main.info(f"API not running: {e}")
                retry_attempts += 1
                wait_time = initial_wait_time * (backoff_factor ** retry_attempts)
                logger_main.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        logger_main.info("Failed to connect after maximum retry attempts.")
        return False
        
    def get_image(self, filename, subfolder, folder_type): # This method is used to retrieve an image from the API server
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"{self.server_address}/view?{url_values}") as response:
            return response.read()
        
    def queue_prompt(self, prompt): # This method is used to queue a prompt for execution
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        headers = {'Content-Type': 'application/json'}  # Set Content-Type header
        req = urllib.request.Request(f"{self.server_address}/prompt", data=data, headers=headers)
        return json.loads(urllib.request.urlopen(req).read())
            
    def get_history(self, prompt_id): # This method is used to retrieve the history of a prompt from the API server
        with urllib.request.urlopen(f"{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())
        
    
    def generate_images(self, payload): # This method is used to generate images from a prompt and is the main method of this class
        try:
            if not self.ws.connected: # Check if the WebSocket is connected to the API server and reconnect if necessary
                print("WebSocket is not connected. Reconnecting...")
                self.ws.connect(self.ws_address)
            prompt_id = self.queue_prompt(payload)['prompt_id']
            while True:
                out = self.ws.recv() # Wait for a message from the API server
                if isinstance(out, str): # Check if the message is a string
                    message = json.loads(out) # Parse the message as JSON
                    if message['type'] == 'executing': # Check if the message is an 'executing' message
                        data = message['data'] # Extract the data from the message
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break
            address = self.find_output_node(payload) # Find the SaveImage node; workflow MUST contain only one SaveImage node
            history = self.get_history(prompt_id)[prompt_id]
            filenames = eval(f"history['outputs']{address}")['images']  # Extract all images
            images = []
            for img_info in filenames:
                filename = img_info['filename']
                subfolder = img_info['subfolder']
                folder_type = img_info['type']
                image_data = self.get_image(filename, subfolder, folder_type)
                image_file = io.BytesIO(image_data)
                image = Image.open(image_file)
                images.append(image)
            return images
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_no = exc_traceback.tb_lineno
            error_message = f'Unhandled error at line {line_no}: {str(e)}'
            print("generate_images - ", error_message)


    def upload_image(self, filepath, subfolder=None, folder_type=None, overwrite=False): # This method is used to upload an image to the API server for use in img2img or controlnet
        try: 
            url = f"{self.server_address}/upload/image"
            files = {'image': open(filepath, 'rb')}
            data = {
                'overwrite': str(overwrite).lower()
            }
            if subfolder:
                data['subfolder'] = subfolder
            if folder_type:
                data['type'] = folder_type
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_no = exc_traceback.tb_lineno
            error_message = f'upload_image - Unhandled error at line {line_no}: {str(e)}'

    @staticmethod
    def find_output_node(json_object): # This method is used to find the node containing the SaveImage class in a prompt
        for key, value in json_object.items():
            if isinstance(value, dict):
                if value.get("class_type") == "SaveImage":
                    return f"['{key}']"  # Return the key containing the SaveImage class
                result = ComfyConnector.find_output_node(value)
                if result:
                    return result
        return None
    
    @staticmethod
    def load_payload(path):
        with open(path, 'r') as file:
            return json.load(file)

    @staticmethod
    def replace_key_value(json_object, target_key, new_value, title="Input Image", class_type_list=None, exclude=True):
        for key, value in json_object.items():
            # Check if the current value is a dictionary and apply the logic recursively
            if isinstance(value, dict):
                metadata = value.get('_meta', {})
                node_title = metadata.get('title', "")

                # Proceed only if the node title matches the specified title
                if node_title == title:
                    import pdb;pdb.set_trace()

                    class_type = value.get('class_type') 

                    # Determine whether to apply the logic based on exclude and class_type_list
                    should_apply_logic = (
                        ((exclude and (class_type_list is None or class_type not in class_type_list)) or
                        (not exclude and (class_type_list is not None and class_type in class_type_list)))
                    )

                    # Apply the logic to replace the target key with the new value if conditions are met
                    if should_apply_logic and target_key in value:
                        value[target_key] = new_value

                # Recurse vertically into nested dictionaries with the same title
                ComfyConnector.replace_key_value(value, target_key, new_value, title, class_type_list, exclude)

            # Recurse sideways into lists with the same title
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        ComfyConnector.replace_key_value(item, target_key, new_value, title, class_type_list, exclude)

    def replace_key_value_in_node(json_object, target_key, new_value, target_title):
        """
        Recursively search for dictionaries within `json_object` that have a title matching `target_title`
        and replace the value of `target_key` with `new_value` in those dictionaries.

        Args:
        json_object (dict): The JSON object to search through.
        target_key (str): The key whose value should be replaced.
        new_value: The new value to set for the target key.
        target_title (str): The title of the node where replacement should occur.
        """

        # Check if the current object is a dictionary
        if isinstance(json_object, dict):
            # Check if this dictionary represents the targeted node by title
            if '_meta' in json_object and 'title' in json_object['_meta'] and json_object['_meta']['title'] == target_title:
                # If the target key is in this node, replace its value
                if target_key in json_object['inputs']:
                    json_object['inputs'][target_key] = new_value

            # Recursively search in values of the dictionary
            for key, value in json_object.items():
                ComfyConnector.replace_key_value_in_node(value, target_key, new_value, target_title)

        # If the current object is a list, iterate over its items
        elif isinstance(json_object, list):
            for item in json_object:
                ComfyConnector.replace_key_value_in_node(item, target_key, new_value, target_title)