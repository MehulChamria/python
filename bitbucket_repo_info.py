#region: Script description
"""
This Python script is designed to provide information about a Bitbucket repository hosted on a Bitbucket Server instance.
It interacts with the Bitbucket REST API to fetch and display valuable repository-related data, such as default reviewers, merge checks, and branch restrictions.

The script offers the following functionality:
- Default Reviewers: It retrieves and displays the default reviewers configured for the repository. These reviewers may include their display names and email addresses.
- Merge Checks: The script fetches and presents the repository merge checks relevant to pull requests. This includes information on whether the "needs work" status is enabled, if all reviewers must approve, the minimum approvals required, and more.
- Branch Restrictions: It provides insights into branch restrictions, including whether specific branches are configured for read-only access, pull request-only access, or other restrictions.
- Effective Restrictions: Additionally, the script takes into account both inherited project-level and repository-level restrictions. It combines these restrictions to provide a clear view of the effective access controls on the repository.

The script is especially useful for DevOps engineers and administrators seeking to understand the configuration and access controls of Bitbucket repositories within their projects.

Usage:
1. Clone the repository to your local machine.
2. Navigate to the script directory.
3. Install dependencies.
4. Set Bitbucket Server credentials as environment variables or provide them when prompted.
5. Run the script with the following command, replacing placeholders with your own values:
   'python bitbucket_repo_info.py --bitbucket-url <Bitbucket Server URL> --project <project-key> --repository <repository-slug>'.

Author: Mehul Chamria
Date: 11/09/2023
Version: 0.0.1
"""
#endregion

#region: Import python libraries
import argparse
import getpass
import os

import requests
import yaml
#endregion

# Function to authenticate with Bitbucket Server
def authenticate():
    username = os.environ.get('BITBUCKET_SERVER_USERNAME')
    password = os.environ.get('BITBUCKET_SERVER_PASSWORD')
    
    if not username:
        username = input('Bitbucket server username: ')
    if not password:
        password = getpass.getpass('Bitbucket server password: ')
    
    return (username, password)

# Function to get default reviewers for a repository
def get_default_reviewers(auth, project_key, repository_slug):
    url = f'{bitbucket_url}/rest/default-reviewers/1.0/projects/{project_key}/repos/{repository_slug}/conditions'
    response = requests.get(url, auth=auth)
    response_json = response.json()
    
    if response.status_code == 200:
        default_reviewers = []
        for item in response_json[0]['reviewers']:
            reviewer_info = {}
            reviewer_info['displayName'] = item.get('displayName', '')
            reviewer_info['emailAddress'] = item.get('emailAddress', '')
            default_reviewers.append(reviewer_info)
        return default_reviewers
    else:
        print(f'Failed to fetch default reviewers. Status code: {response.status_code}')
        return []

# Function to get repository settings
def get_merge_checks(auth, project_key, repository_slug):
    url = f'{bitbucket_url}/rest/api/1.0/projects/{project_key}/repos/{repository_slug}/settings/pull-requests'
    response = requests.get(url, auth=auth)
    response_json = response.json()
    
    if response.status_code == 200:
        # Customize settings as needed
        merge_checks = {
            'No "needs work" status': response_json['needsWork'],
            'All reviewers approve': response_json['requiredAllApprovers'],
            'No incomplete tasks': response_json['requiredAllTasksComplete'],
            'Minimum Approvals': response_json['requiredApprovers'],
            'Minimum successful builds': response_json['requiredSuccessfulBuilds'],
        }
        return merge_checks
    else:
        print(f'Failed to fetch repository settings. Status code: {response.status_code}')
        return {}

# Function to get branch restrictions
def get_branch_restrictions(auth, project_key, repository_slug):
    url = f'{bitbucket_url}/rest/branch-permissions/2.0/projects/{project_key}/repos/{repository_slug}/restrictions'
    response = requests.get(url, auth=auth)
    response_json = response.json()
    
    branch_restrictions = {}
    if response.status_code == 200:
        for item in response_json['values']:
            branch_id = item['matcher']['id']
            restriction = item['type']
            if branch_id in branch_restrictions:
                if restriction in branch_restrictions[branch_id]:
                    continue
                else:
                    branch_restrictions[branch_id].append(restriction)
            else:
                branch_restrictions[branch_id] = [restriction]
        return branch_restrictions
    else:
        print(f'Failed to fetch branch restrictions. Status code: {response.status_code}')
        return {}

# Main script
if __name__ == '__main__':
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Bitbucket Repository Info Script')

    # Add command-line arguments
    parser.add_argument('--bitbucket-url', required=True, help='Bitbucket Server URL')
    parser.add_argument('--project', required=True, help='Bitbucket project key')
    parser.add_argument('--repository', required=True, help='Bitbucket repository slug')

    # Parse the arguments
    args = parser.parse_args()

    # Use args.project and args.repository in your functions
    project_key = args.project
    repository_slug = args.repository
    bitbucket_url = args.bitbucket_url

    auth = authenticate()
    print(f'Repository: {repository_slug}')

    # Fetch and print default reviewers
    default_reviewers = get_default_reviewers(auth, project_key, repository_slug)
    print('\nDefault Reviewers:')
    for reviewer in default_reviewers:
        print(f'- Name: {reviewer["displayName"]}')
        print(f'  Email: {reviewer["emailAddress"]}')

    # Fetch and print repository settings
    merge_checks = get_merge_checks(auth, project_key, repository_slug)
    print('\nMerge Checks:')
    for key, value in merge_checks.items():
        print(f'- {key}: {value}')

    # Fetch and print branch restrictions
    branch_restrictions = get_branch_restrictions(auth, project_key, repository_slug)
    print('\nBranch Restrictions:')
    yaml_output = yaml.dump(branch_restrictions, default_flow_style=False)
    print(yaml_output)
