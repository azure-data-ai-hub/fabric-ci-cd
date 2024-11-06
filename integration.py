import requests
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Azure AD and Microsoft Fabric API configuration for source subscription
source_client_id = os.getenv('SOURCE_AZURE_CLIENT_ID')
source_client_secret = os.getenv('SOURCE_AZURE_CLIENT_SECRET')
source_tenant_id = os.getenv('SOURCE_AZURE_TENANT_ID')
source_authority_url = f'https://login.microsoftonline.com/{source_tenant_id}'
source_resource_url = 'https://analysis.windows.net/powerbi/api'
source_api_url = 'https://api.fabric.microsoft.com/v1'

# Azure AD and Microsoft Fabric API configuration for target subscription
target_client_id = os.getenv('TARGET_AZURE_CLIENT_ID')
target_client_secret = os.getenv('TARGET_AZURE_CLIENT_SECRET')
target_tenant_id = os.getenv('TARGET_AZURE_TENANT_ID')
target_authority_url = f'https://login.microsoftonline.com/{target_tenant_id}'
target_resource_url = 'https://analysis.windows.net/powerbi/api'
target_api_url = 'https://api.fabric.microsoft.com/v1'

# Source and target workspace IDs
source_workspace_id = os.getenv('SOURCE_WORKSPACE_ID')
target_workspace_id = os.getenv('TARGET_WORKSPACE_ID')

def get_access_token(authority_url, client_id, client_secret, resource_url):
    url = f'{authority_url}/oauth2/v2.0/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': resource_url + '/.default'
    }

    logging.info(f"Requesting access token from {url}")
    logging.debug(f"Request headers: {headers}")
    logging.debug(f"Request body: {data}")

    response = requests.post(url, headers=headers, data=data)
    logging.info(f"Access token response status code: {response.status_code}")

    if response.status_code != 200:
        logging.error(f"Failed to obtain access token: {response.text}")
        response.raise_for_status()

    access_token = response.json().get('access_token')
    if not access_token:
        logging.error("Access token not found in the response.")
        raise ValueError("Access token not found in the response.")

    logging.info("Access token obtained successfully.")
    return access_token

def extract_data_from_response(response_data, obj_type):
    if isinstance(response_data, dict):
        if 'value' in response_data:
            return response_data['value']
        elif obj_type in response_data:
            return response_data[obj_type]
        else:
            return [response_data]
    elif isinstance(response_data, list):
        return response_data
    else:
        logging.error(f"Unexpected response format for {obj_type}: {response_data}")
        return []

def get_workspace_objects(workspace_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    objects = {}

    endpoints = {
        'datasets': f'{source_api_url}/workspaces/{workspace_id}/datasets',
        'reports': f'{source_api_url}/workspaces/{workspace_id}/reports',
        'dashboards': f'{source_api_url}/workspaces/{workspace_id}/dashboards',
        'dataflows': f'{source_api_url}/workspaces/{workspace_id}/dataflows',
        'pipelines': f'{source_api_url}/workspaces/{workspace_id}/pipelines',
        'lakehouses': f'{source_api_url}/workspaces/{workspace_id}/lakehouses',
        'data_warehouses': f'{source_api_url}/workspaces/{workspace_id}/datawarehouses',
    }

    for obj_type, url in endpoints.items():
        logging.info(f"Fetching {obj_type} from {url}")
        response = requests.get(url, headers=headers)
        logging.info(f"Response status code for {obj_type}: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            logging.debug(f"Response data for {obj_type}: {json.dumps(response_data, indent=2)}")
            data = extract_data_from_response(response_data, obj_type)
            objects[obj_type] = data
            logging.info(f"Retrieved {len(data)} {obj_type}")
        elif response.status_code == 404:
            logging.warning(f"{obj_type.capitalize()} not found in workspace {workspace_id}.")
            objects[obj_type] = []
        else:
            logging.error(f"Error retrieving {obj_type}: {response.status_code} - {response.text}")
            objects[obj_type] = []

    return objects

def save_objects_to_files(objects):
    for obj_type, obj_list in objects.items():
        file_name = f'{obj_type}.json'
        with open(file_name, 'w') as f:
            json.dump(obj_list, f, indent=4)
        logging.info(f"Saved {len(obj_list)} {obj_type} to {file_name}")

# Get existing objects in target workspace
def get_existing_objects(workspace_id, access_token, object_type):
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(f'{target_api_url}/workspaces/{workspace_id}/{object_type}', headers=headers)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logging.info(f"Resource not found: {http_err}")
        else:
            logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return []
    
# Update existing object in target workspace
def update_existing_object(workspace_id, access_token, object_type, object_id, data):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.patch(f'{target_api_url}/workspaces/{workspace_id}/{object_type}/{object_id}', headers=headers, data=json.dumps(data))
    response.raise_for_status()

# Create new object in target workspace
def create_new_object(workspace_id, access_token, object_type, data):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    try:
        response = requests.post(f'{target_api_url}/workspaces/{workspace_id}/{object_type}', headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logging.error(f"Resource not found while creating {object_type}: {http_err}")
        else:
            logging.error(f"HTTP error occurred while creating {object_type}: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred while creating {object_type}: {err}")

# Merge objects in target workspace
def merge_objects_in_target_workspace(file_path, object_type, access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    try:
        with open(file_path, 'r') as f:
            objects = json.load(f)
            
            existing_objects = get_existing_objects(target_workspace_id, access_token, object_type)
            existing_object_names = {obj['name']: obj['id'] for obj in existing_objects if 'name' in obj and 'id' in obj}
            
            for obj in objects:
                if not isinstance(obj, dict):
                    logging.error("Invalid object format, expected a dictionary")
                    continue
                
                if 'name' not in obj:
                    logging.error("Object missing 'name' key")
                    continue
                
                if obj['name'] in existing_object_names:
                    update_existing_object(target_workspace_id, access_token, object_type, existing_object_names[obj['name']], obj)
                else:
                    create_new_object(target_workspace_id, access_token, object_type, obj)
    except FileNotFoundError as e:
        logging.error(f"File not found error: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from file {file_path}: {e}")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            logging.error(f"Resource not found while merging {object_type}: {http_err}")
        else:
            logging.error(f"HTTP error occurred while merging {object_type}: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred while merging {object_type}: {err}")
        
# Main function
def main():

    # Authenticate and get access token for source subscription
    source_access_token = get_access_token(
    source_authority_url,
    source_client_id,
    source_client_secret,
    source_resource_url
    )

    # Authenticate and get access token for target subscription
    target_access_token = get_access_token(
        target_authority_url,
        target_client_id,
        target_client_secret,
        target_resource_url
    )

    # Get objects from source workspace
    logging.info(f"Retrieving objects from source workspace {source_workspace_id}")
    objects = get_workspace_objects(source_workspace_id, source_access_token)
    save_objects_to_files(objects)
    logging.info("Object retrieval and saving completed.")

if __name__ == '__main__':
    main()
