import requests
import json
import os
import logging

# Azure AD and Microsoft Fabric API configuration for source subscription
source_client_id = os.getenv('SOURCE_AZURE_CLIENT_ID')
source_client_secret = os.getenv('SOURCE_AZURE_CLIENT_SECRET')
source_tenant_id = os.getenv('SOURCE_AZURE_TENANT_ID')
source_authority_url = f'https://login.microsoftonline.com/{source_tenant_id}'
source_resource_url = 'https://fabric.microsoft.com'
source_api_url = 'https://api.fabric.microsoft.com/v1.0'

# Azure AD and Microsoft Fabric API configuration for target subscription
target_client_id = os.getenv('TARGET_AZURE_CLIENT_ID')
target_client_secret = os.getenv('TARGET_AZURE_CLIENT_SECRET')
target_tenant_id = os.getenv('TARGET_AZURE_TENANT_ID')
target_authority_url = f'https://login.microsoftonline.com/{target_tenant_id}'
target_resource_url = 'https://fabric.microsoft.com'
target_api_url = 'https://api.fabric.microsoft.com/v1.0'

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

    logging.info(f"Request URL: {url}")
    logging.info(f"Request Headers: {headers}")
    logging.info(f"Request Body: {data}")

    response = requests.post(url, headers=headers, data=data)
    logging.info(f"Response Status Code: {response.status_code}")
    logging.info(f"Response Body: {response.text}")

    response.raise_for_status()
    return response.json()['access_token']
    
# Get objects from source workspace
def get_workspace_objects(workspace_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    datasets = requests.get(f'{source_api_url}/workspaces/{workspace_id}/datasets', headers=headers).json()['value']
    reports = requests.get(f'{source_api_url}/workspaces/{workspace_id}/reports', headers=headers).json()['value']
    dashboards = requests.get(f'{source_api_url}/workspaces/{workspace_id}/dashboards', headers=headers).json()['value']
    dataflows = requests.get(f'{source_api_url}/workspaces/{workspace_id}/dataflows', headers=headers).json()['value']
    pipelines = requests.get(f'{source_api_url}/workspaces/{workspace_id}/pipelines', headers=headers).json()['value']
    lakehouses = requests.get(f'{source_api_url}/workspaces/{workspace_id}/lakehouses', headers=headers).json()['value']
    data_warehouses = requests.get(f'{source_api_url}/workspaces/{workspace_id}/datawarehouses', headers=headers).json()['value']
    return datasets, reports, dashboards, dataflows, pipelines, lakehouses, data_warehouses

# Save objects to JSON files
def save_objects_to_files(datasets, reports, dashboards, dataflows, pipelines, lakehouses, data_warehouses):
    with open('datasets.json', 'w') as f:
        json.dump(datasets, f, indent=4)
    with open('reports.json', 'w') as f:
        json.dump(reports, f, indent=4)
    with open('dashboards.json', 'w') as f:
        json.dump(dashboards, f, indent=4)
    with open('dataflows.json', 'w') as f:
        json.dump(dataflows, f, indent=4)
    with open('pipelines.json', 'w') as f:
        json.dump(pipelines, f, indent=4)
    with open('lakehouses.json', 'w') as f:
        json.dump(lakehouses, f, indent=4)
    with open('data_warehouses.json', 'w') as f:
        json.dump(data_warehouses, f, indent=4)

# Get existing objects in target workspace
def get_existing_objects(workspace_id, access_token, object_type):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{target_api_url}/workspaces/{workspace_id}/{object_type}', headers=headers)
    response.raise_for_status()
    return response.json()['value']

# Update existing object in target workspace
def update_existing_object(workspace_id, access_token, object_type, object_id, data):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.patch(f'{target_api_url}/workspaces/{workspace_id}/{object_type}/{object_id}', headers=headers, data=json.dumps(data))
    response.raise_for_status()

# Create new object in target workspace
def create_new_object(workspace_id, access_token, object_type, data):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.post(f'{target_api_url}/workspaces/{workspace_id}/{object_type}', headers=headers, data=json.dumps(data))
    response.raise_for_status()

# Merge objects in target workspace
def merge_objects_in_target_workspace(file_path, object_type, access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    with open(file_path, 'r') as f:
        objects = json.load(f)
        existing_objects = get_existing_objects(target_workspace_id, access_token, object_type)
        existing_object_names = {obj['name']: obj['id'] for obj in existing_objects}
        for obj in objects:
            if obj['name'] in existing_object_names:
                update_existing_object(target_workspace_id, access_token, object_type, existing_object_names[obj['name']], obj)
            else:
                create_new_object(target_workspace_id, access_token, object_type, obj)

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

    datasets, reports, dashboards, dataflows, pipelines, lakehouses, data_warehouses = get_workspace_objects(source_workspace_id, source_access_token)
    save_objects_to_files(datasets, reports, dashboards, dataflows, pipelines, lakehouses, data_warehouses)
    merge_objects_in_target_workspace('datasets.json', 'datasets', target_access_token)
    merge_objects_in_target_workspace('reports.json', 'reports', target_access_token)
    merge_objects_in_target_workspace('dashboards.json', 'dashboards', target_access_token)
    merge_objects_in_target_workspace('dataflows.json', 'dataflows', target_access_token)
    merge_objects_in_target_workspace('pipelines.json', 'pipelines', target_access_token)
    merge_objects_in_target_workspace('lakehouses.json', 'lakehouses', target_access_token)
    merge_objects_in_target_workspace('data_warehouses.json', 'datawarehouses', target_access_token)

if __name__ == '__main__':
    main()
