'''
Bitbucket Cloud Audit Script

This script retrieves information from Bitbucket Cloud, including repositories, projects, and groups,
and outputs the data in YAML format.

Usage:
    python script_name.py [--config CONFIG] [--workspace WORKSPACE] [--bitbucket-url BITBUCKET_URL] [--output OUTPUT]

Arguments:
    --config CONFIG: Path to the config file (default: 'config.ini').
    --workspace WORKSPACE: Bitbucket workspace (prompted if not provided).
    --bitbucket-url BITBUCKET_URL: Bitbucket URL (optional, uses default if not provided).
    --output OUTPUT: Path to the output YAML file (default: 'output.yaml').

Dependencies:
    - argparse (for parsing command line arguments, part of Python's standard library)
    - configparser (for reading configuration, install via: pip install configparser)
    - getpass (for securely inputting passwords, part of Python's standard library)
    - os (for environment variable access, part of Python's standard library)
    - sys (for system-level operations, part of Python's standard library)
    - requests (for making HTTP requests, install via: pip install requests)
    - yaml (for YAML formatting, install via: pip install PyYAML)

Classes:
    - BitbucketAuthentication: Handles Bitbucket authentication with username and password.

Functions:
    - parse_args(): Parses command line arguments for the script.
    - print_status(message): Prints a status message to the console.
    - api_get_request(credentials, endpoint): Makes a GET request to the Bitbucket API with authentication.
    - get_repositories(credentials): Retrieves a list of Bitbucket repositories and their associated groups.
    - get_projects(credentials): Retrieves information about Bitbucket projects and their associated groups.
    - get_groups(credentials): Retrieves a list of Bitbucket groups.

Main Execution:
    - Reads configuration from 'config.ini', if available or prompts the user for Bitbucket Cloud workspace.
    - Retrieves Bitbucket Cloud username and password from environment variables or prompts the user, if not found.
    - Calls functions to fetch data from Bitbucket Cloud.
    - Outputs the collected data in YAML format to 'output.yaml'.

Author: Mehul Chamria
Date: 05/09/2023
Version: 0.0.1
'''

# Import python libraries
import argparse
import configparser
import getpass
import os
import sys

import requests
import yaml

# Constants
BITBUCKET_URL_FALLBACK  = 'https://api.bitbucket.org'

# Class BitbucketAuthentication
class BitbucketAuthentication:
    def __init__(self, username, password):
        self.username = username
        self.password = password

# Function to parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Bitbucket Cloud Audit Script')
    parser.add_argument('--config', default='config.ini', help='Path to the config file')
    parser.add_argument('--workspace', help='Bitbucket workspace')
    parser.add_argument('--bitbucket-url', help='Bitbucket url')
    parser.add_argument('--output', default='output.yaml', help='Path to the output YAML file')
    return parser.parse_args()

# Function to print a status message
def print_status(message):
    sys.stdout.write(message)
    sys.stdout.flush() # Flush the buffer to ensure it's printed immediately

# Function to make an API request
def api_get_request(credentials, endpoint):
    headers = {
        'Accept': 'application/json'
        }
    # Make a GET request to the API
    response = requests.request(method = 'GET',
                            url = endpoint,
                            auth = (credentials.username,credentials.password),
                            headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        error_message = f'Failed to retrieve data. Status code: {response.status_code}'
        raise Exception(error_message)

# Function to get repositories
def get_repositories(credentials):
    print_status('Auditing repositories: ')
    repositories_endpoint = f'{bitbucket_url}/2.0/repositories/{workspace}?pagelen=100'
    repositories = []
    while repositories_endpoint:
        repository_list = api_get_request(credentials, repositories_endpoint)
        for repository in repository_list['values']:
            repository_info = {
                'slug': repository['slug'],
                'description': repository['description'],
                'main_branchname': repository['mainbranch']['name'],
                'is_private': repository['is_private'],
                'project_key': repository['project']['key']}
            
            # Get groups with explicit access to the repository
            repo_slug = repository['slug']
            repository_groups_endpoint = f'{bitbucket_url}/2.0/repositories/{workspace}/{repo_slug}/permissions-config/groups'
            groups = api_get_request(credentials, repository_groups_endpoint)
            groups_info = []
            for group in groups['values']:
                groups_info.append({
                    'slug': group['group']['slug'],
                    'permission': group['permission']
                })
            repository_info['groups'] = groups_info

            repositories.append(repository_info)
        # Check if there is a next page
        repositories_endpoint = repository_list.get('next')
    print_status('Successful\n')
    return repositories

# Function to get project information
def get_projects(credentials):
    print_status('Auditing projects: ')
    projects = []
    projects_endpoint = f'{bitbucket_url}/2.0/workspaces/{workspace}/projects?pagelen=100'
    while projects_endpoint:
        project_list = api_get_request(credentials, projects_endpoint)
        for project in project_list['values']:
            project_info = {
                'name': project['name'],
                'key': project['key'],
                'description': project['description']
            }

            # Get groups with explicit access to the project
            project_key = project['key']
            project_groups_endpoint = f'{bitbucket_url}/2.0/workspaces/{workspace}/projects/{project_key}/permissions-config/groups?pagelen=100'
            groups = api_get_request(credentials, project_groups_endpoint)
            groups_info = []
            for group in groups['values']:
                groups_info.append({
                    'slug': group['group']['slug'],
                    'permission': group['permission']
                })
            project_info['groups'] = groups_info

            projects.append(project_info)
            # Check if there is a next page
            projects_endpoint = project_list.get('next')
    print_status('Successful\n')
    return projects

# Function to get groups
def get_groups(credentials):
    print_status('Auditing groups: ')
    groups = []
    groups_endpoint = f'{bitbucket_url}/1.0/groups/{workspace}'
    group_list = api_get_request(credentials, groups_endpoint)
    for group in group_list:
        group_info = {
            'name': group['name'],
            'slug': group['slug']
        }
        member_info = []
        for member in group['members']:
            member_info.append({
                'display_name': member['display_name'],
                'account_id': member['account_id'],
            })
        group_info['members'] = member_info
        groups.append(group_info)
    print_status('Successful\n')
    return groups

# Main function
if __name__ == '__main__':
    try:
        # Parse command line arguments
        args = parse_args()

        # Create a configparser object to read configuration from a file (if it exists).
        config = configparser.ConfigParser()
        if os.path.exists(args.config):
            config.read(args.config)
        
        # Use the provided Bitbucket url or set to default if not provided
        if args.bitbucket_url:
            bitbucket_url = args.bitbucket_url
        else:
            bitbucket_url = config.get('bitbucket_cloud', 'url', fallback=BITBUCKET_URL_FALLBACK)
        
        # Use the provided workspace or prompt the user if not provided
        if args.workspace:
            workspace = args.workspace
        else:
            workspace = config.get('bitbucket_cloud', 'workspace', fallback=input('Bitbucket workspace: '))
        
        # Use the provided output file path or the default one
        output_file = args.output

        # Retrieve Bitbucket Cloud credentials from environment variables or prompt for input if not set.
        credentials = None
        username = os.environ.get('BITBUCKET_CLOUD_USERNAME')
        password = os.environ.get('BITBUCKET_CLOUD_PASSWORD')
        if not username:
            username = input('Bitbucket cloud username: ')
        if not password:
            password = getpass.getpass('Bitbucket cloud password: ')
        credentials = BitbucketAuthentication(username, password)

        # Create a Bitbucket configuration dictionary by calling functions to get groups, repositories, and projects.
        bitbucket_config = {
            'groups': get_groups(credentials),
            'repositories': get_repositories(credentials),
            'projects': get_projects(credentials)}
        
        # Generate a YAML report and write it to the specified output file.
        print_status('Generating YAML report: ')
        yaml_output = yaml.dump(bitbucket_config, default_flow_style=False,sort_keys=False)
        with open(output_file, 'w') as file:
            file.write(yaml_output)
        print_status('Successful\n')

    except Exception as e:
        print(f'Error: {str(e)}')
