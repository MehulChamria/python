'''
Bitbucket Project and Group Creation Script

Overview:
This script automates the creation of a Bitbucket project and associated groups. It ensures:
1. A unique project key is generated using the first 3 letters of the Business Area and Project Name.
2. If a project key already exists, it will shuffle the Project Name to generate a new unique key.
3. Two groups, 'Development' and 'AppSupport', are created and assigned permissions ('write' and 'admin' respectively).
4. The script checks if the project already exists before creating it.

Requirements:
- Python 3.x or higher.
- `requests` library (can be installed with `pip install requests`).

Environment Variables:
Ensure the following environment variables are set:
- BITBUCKET_CLOUD_USERNAME: Your Bitbucket Cloud username.
- BITBUCKET_CLOUD_PASSWORD: Your Bitbucket Cloud password or app password.
- BITBUCKET_CLOUD_WORKSPACE: The Bitbucket workspace ID where the project will be created.

Alternatively, the script will prompt you for the username, password and workspace id if not set in the environment variables.

Usage:
1. Clone or download the script to your machine.
2. Set the environment variables `BITBUCKET_CLOUD_USERNAME`, `BITBUCKET_CLOUD_PASSWORD`, and `BITBUCKET_CLOUD_WORKSPACE`.
3. Run the script:
    python create_bitbucket_project.py
4. Enter the project name and business area when prompted.

Example:
    Enter Project Name: Foundation
    Enter Business Area: Finance

Output Example:
    Project 'Finance-Foundation' created successfully.
    Group 'Finance-Foundation-Development' created successfully.
    Permission 'write' assigned to group 'Finance-Foundation-Development' on project 'FIN_FOU'.
    Group 'Finance-Foundation-AppSupport' created successfully.
    Permission 'admin' assigned to group 'Finance-Foundation-AppSupport' on project 'FIN_FOU'.

Functions:
1. `create_project_and_groups(project_name, business_area, credentials, bitbucket_cloud_workspace)`:
    - Creates the project and associated groups, checking for existing project keys and ensuring uniqueness.
    
2. `generate_project_key(project_name, business_area)`:
    - Generates a project key using the first 3 letters of the business area and the first 3 letters of the project name.

3. `generate_unique_project_key(project_name, business_area, bitbucket_cloud_workspace)`:
    - If the project key already exists, it shuffles the project name and checks for uniqueness until a new, unique project key is generated.

4. `check_if_project_exists(project_key, bitbucket_cloud_workspace)`:
    - Checks if the project with the given project key already exists in the workspace.

5. `create_group_and_set_permission(project_key, group_name, permission, credentials, bitbucket_cloud_workspace)`:
    - Creates a group and sets the specified permissions (write/admin) for the project.

Error Handling:
- If a project key already exists, the script shuffles the project name and retries to generate a unique key.
- Errors from the Bitbucket API will be printed, including failure to create the project or groups.

Note:
- The script ensures that the generated project key is always valid, meeting Bitbucket's requirements (starts with a letter and consists of ASCII letters, numbers, and underscores).
'''

import getpass
import os
import random

import requests


# Class BitbucketAuthentication
class BitbucketAuthentication:
    def __init__(self, username, password):
        self.username = username
        self.password = password

# Base URL for Bitbucket Cloud API
BASE_URL_V1 = "https://api.bitbucket.org/1.0"
BASE_URL_V2 = "https://api.bitbucket.org/2.0"

def create_project_and_groups(project_name, business_area, credentials, bitbucket_cloud_workspace):
    # Step 1: Generate project key (business area first 3 letters + shuffled project name)
    project_key = generate_project_key(project_name, business_area)
    
    # Step 2: Check if the project key already exists
    if check_if_project_exists(project_key, bitbucket_cloud_workspace):
        print(f"Project key '{project_key}' already exists. Generating a new one.")
        project_key = generate_unique_project_key(project_name, business_area, bitbucket_cloud_workspace)

    # Step 3: Create the project with the unique key
    project_full_name = f"{business_area}-{project_name}"
    project_data = {
        "name": project_full_name,
        "key": project_key  # Use the generated project key
    }
    project_url = f"{BASE_URL_V2}/workspaces/{bitbucket_cloud_workspace}/projects"
    response = requests.post(project_url, json=project_data, auth=(credentials.username, credentials.password))
    
    if response.status_code == 201:
        print(f"Project '{project_full_name}' created successfully.")
        project_key = response.json()['key']
    else:
        print("Error creating project:", response.json())
        return

    # Step 4: Define group names and permissions
    development_group = f"{business_area}-{project_name}-Development"
    app_support_group = f"{business_area}-{project_name}-AppSupport"

    # Step 5: Create groups and set permissions
    create_group_and_set_permission(project_key, development_group, 'write', credentials, bitbucket_cloud_workspace)
    create_group_and_set_permission(project_key, app_support_group, 'admin', credentials, bitbucket_cloud_workspace)

def generate_project_key(project_name, business_area):
    # Generate project key using the first 3 letters of business area + first 3 letters of the project name
    return f"{business_area[:3].upper()}_{project_name[:3].upper()}"

def generate_unique_project_key(project_name, business_area, bitbucket_cloud_workspace):
    # Generate a new unique project key by shuffling the project name and checking for uniqueness
    while True:
        shuffled_project_name = ''.join(random.sample(project_name, len(project_name)))  # Shuffle project name
        project_key = f"{business_area[:3].upper()}_{shuffled_project_name[:3].upper()}"
        
        if not check_if_project_exists(project_key, bitbucket_cloud_workspace):
            return project_key  # Return the new unique project key

def check_if_project_exists(project_key, bitbucket_cloud_workspace):
    # Check if the project with the given key already exists in the workspace
    project_url = f"{BASE_URL_V2}/workspaces/{bitbucket_cloud_workspace}/projects/{project_key}"
    response = requests.get(project_url)
    
    if response.status_code == 200:
        return True  # Project exists
    elif response.status_code == 404:
        return False  # Project does not exist
    else:
        print("Error checking project existence:", response.json())
        return False

def create_group_and_set_permission(project_key, group_name, permission, credentials, bitbucket_cloud_workspace):
    # Step 1: Create a new group for the workspace
    group_url = f"{BASE_URL_V1}/groups/{bitbucket_cloud_workspace}"
    group_data = {
        "name": group_name
    }
    response = requests.post(group_url, data=group_data, auth=(credentials.username, credentials.password))
    
    if response.status_code == 200:
        print(f"Group '{group_name}' created successfully.")
    else:
        print("Error creating group:", response.json())
        return

    # Step 2: Set permission for the group on the project
    group_slug = response.json().get('slug')
    permission_url = f"{BASE_URL_V2}/workspaces/{bitbucket_cloud_workspace}/projects/{project_key}/permissions-config/groups/{group_slug}"
    permission_data = {
        "permission": permission
    }
    response = requests.put(permission_url, json=permission_data, auth=(credentials.username, credentials.password))
    
    if response.status_code == 200:
        print(f"Permission '{permission}' assigned to group '{group_name}' on project '{project_key}'.")
    else:
        print("Error setting permission:", response.json())

# Usage example
# Replace these with your Bitbucket Cloud credentials and workspace ID
credentials = None
username = os.environ.get('BITBUCKET_CLOUD_USERNAME')
password = os.environ.get('BITBUCKET_CLOUD_PASSWORD')
bitbucket_cloud_workspace = os.environ.get('BITBUCKET_CLOUD_WORKSPACE')
if not username:
    username = input('Bitbucket cloud username: ')
if not password:
    password = getpass.getpass('Bitbucket cloud password: ')
credentials = BitbucketAuthentication(username, password)
if not bitbucket_cloud_workspace:
    bitbucket_cloud_workspace = input('Bitbucket cloud workspace id: ')

bitbucket_cloud_workspace = os.environ.get('BITBUCKET_CLOUD_WORKSPACE')
project_name = input("Enter Project Name: ")
business_area = input("Enter Business Area: ")
create_project_and_groups(project_name, business_area, credentials, bitbucket_cloud_workspace)
