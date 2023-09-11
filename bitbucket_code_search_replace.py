# Script Description:
"""
This script automates the process of searching for specific code references within Bitbucket Cloud repositories and updating them.

It utilizes the Bitbucket API, Git, and various Python libraries to perform the following tasks:
- Authentication: The script starts by authenticating the user with Bitbucket Cloud using their username and password.
- Search and Update: It then searches for code references matching a given query across all repositories within a Bitbucket Cloud workspace.
- Clone Repositories: For each matching repository, the script clones it locally.
- Branch Management: It creates and switches to a new branch for updating code references.
- Code Update: The script iterates through the files in the cloned repository, excluding the `.git` and `.terraform` folders, and replaces specified search strings with replacement strings.
- Commit and Push: After updating the code, it stages and commits the changes and pushes them to the remote repository.
- Pull Request Creation: Finally, the script creates a pull request (PR) for each updated repository, providing a title and description.

Usage:
- The script can be configured by setting environmental variables for Bitbucket Cloud username and password, or it will prompt the user for these credentials if they are not provided.
- You can customize the search query, branch names, search and replace strings, commit messages, and PR titles and descriptions according to your requirements.
- To execute the script, run it in your preferred Python environment.

Author: Mehul Chamria
Date: 05/09/2023
Version: 0.0.1

This script streamlines the process of updating code references across multiple repositories in Bitbucket Cloud, making it easier to maintain and manage your codebase.
"""

#region: Import python libraries
import getpass
import os
import subprocess
import time
from urllib.parse import urlparse

import git
import requests
#endregion

#region: Class BitbucketAuthentication
class BitbucketAuthentication:
    def __init__(self, username, password):
        self.username = username
        self.password = password
#endregion

#region: Function clone_repository
def clone_repository(url, local_path):
    try:
        print(" - Cloning repository locally: ", end = '')
        git.Git().clone(url, local_path)
        print("Successful")
    except git.GitCommandError as e:
        print(f"Failed: {str(e)}")
        raise
#endregion

#region: Function create_and_switch_branch
def create_and_switch_branch(local_repository, feature_branch_name):
    try:
        print(" - Creating and switching to a new branch: ", end = '')
        repo = git.Repo(local_repository)
        feature_branch = repo.create_head(feature_branch_name)
        repo.head.reference = feature_branch
        print("Successful")
    except git.GitCommandError as e:
        print(f"Failed: {str(e)}")
        raise
#endregion

#region: Function update_references
def update_references(repo_location, search_str, replace_str):
    try:
        print(" - Updating references to the modules: ", end = '')
        # Iterate through files in the cloned repo
        for root, _, files in os.walk(repo_location):
            if '.git' in root or '.terraform' in root:
                continue  # Skip the .git folder
            for file in files:
                file_path = os.path.join(root, file)

                with open(file_path, 'rb') as f:
                    content = f.read()

                # Replace the search string with the replace string
                content = content.replace(search_str.encode(), replace_str.encode())

                with open(file_path, 'wb') as f:
                    f.write(content)
        print("Successful")
    except Exception as e:
        print(f"Failed: {str(e)}")
        raise
#endregion

#region: Function stage_and_commit
def stage_and_commit(local_repository, commit_message):
    try:
        print(" - Staging and committing file: ", end = '')
        repo = git.Repo(local_repository)
        repo.git.add(all=True)
        repo.index.commit(commit_message)
        print("Successful")
    except git.GitCommandError as e:
        print(f"Failed: {str(e)}")
        raise
#endregion

#region: Function push_changes
def push_changes(local_repository, feature_branch_name):
    try:
        print(" - Pushing changes: ", end = '')
        repo = git.Repo(local_repository)
        repo.git.push('--set-upstream', 'origin', feature_branch_name)
        print("Successful")
    except git.GitCommandError as e:
        print(f"Failed: {str(e)}")
        raise
#endregion

#region: Function create_pr
def create_pr(credentials, pr_title, pr_description, feature_branch_name, base_endpoint, workspace, repository_slug):
    # Create the PR payload
    print(" - Creating PR: ", end = '')
    payload = {'title': pr_title,
               'description': pr_description,
               'source': {'branch': {'name': feature_branch_name}}}
    endpoint = f'{base_endpoint}/repositories/{workspace}/{repository_slug}/pullrequests'
    response = requests.request(method = 'POST',
                                url = endpoint,
                                auth = (credentials.username,credentials.password),
                                json = payload)
    # Check the response status
    if response.status_code == 201:
        print('Successful')
        pr_data = response.json()
        pr_url = pr_data['links']['html']['href']
        print(f' - PR URL: {pr_url}')
    else:
        print(f'Failed: {response.status_code} | {response.text}')
#endregion

#region: Function to clean up (remove) cloned repository
def cleanup_repository(repository):
    try:
        print(f" - Cleaning up repository {repository}:", end = '')
        time.sleep(5)
        if os.name == 'nt':
            subprocess.check_output(['cmd', '/C', 'rmdir', '/S', '/Q', os.path.abspath(repository)])
            print("Successful")
        else:
            print("Skipped - Only supported for Windows OS")
    except Exception as e:
        print(f"Failed: {str(e)}")
# endregion

#region: Function search_and_update_code
def search_and_update_code(credentials, base_endpoint, workspace, query, feature_branch_name, search_str, replace_str, commit_message, pr_title, pr_description):
    endpoint = f'{base_endpoint}/workspaces/{workspace}/search/code'
    headers = {
        "Accept": "application/json"
    }
    query = {
        'search_query': query
    }
    all_repositories = []
    while endpoint:
        # Make a GET request to the API
        response = requests.request(method = 'GET',
                                url = endpoint,
                                auth = (credentials.username,credentials.password),
                                headers=headers,
                                params = query)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract the items from the current page and add them to the list
            items_on_page = data.get('values', [])
            for item in items_on_page:
                parsed_url = urlparse(item['file']['links']['self']['href'])
                parsed_repository = parsed_url.path.split('/')[4]
                all_repositories.append(parsed_repository) 
            
            # Check if there is a next page
            endpoint = data.get("next")
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            break
    all_repositories = list(dict.fromkeys(all_repositories))
    for repository in all_repositories:
        print(repository)
        repo_url_ssh = f'git@bitbucket.org:{workspace}/{repository}.git'
        local_repository = f'tmp_{repository}'
        clone_repository(repo_url_ssh, local_repository)
        create_and_switch_branch(local_repository, feature_branch_name)
        update_references(local_repository, search_str, replace_str)
        stage_and_commit(local_repository, commit_message)
        push_changes(local_repository, feature_branch_name)
        create_pr(credentials, pr_title, pr_description, feature_branch_name, base_endpoint, workspace, repository)
        cleanup_repository(local_repository)
        input("Press enter to continue")
#endregion

#region: Main code
if __name__ == "__main__":
    base_endpoint = 'https://api.bitbucket.org/2.0'
    workspace = 'example-prod'
    query = '"1882 tf"'
    feature_branch_name = 'feature/update-module-reference'
    search_str = 'ssh://git@bitbucket.example.com:1882/tf'
    replace_str = 'git@bitbucket.org:example-prod'
    commit_message = 'Updating module references'
    pr_title = 'Updating module references'
    pr_description = 'This PR is to update the references to the modules from Bitbucket Server to Bitbucket Cloud.'

    try:
        username = os.environ.get('BITBUCKET_CLOUD_USERNAME')
        password = os.environ.get('BITBUCKET_CLOUD_PASSWORD')

        if not username:
            username = input('Bitbucket cloud username: ')

        if not password:
            password = getpass.getpass('Bitbucket cloud password: ')

        credentials = BitbucketAuthentication(username, password)
        search_and_update_code(credentials, base_endpoint, workspace, query, feature_branch_name, search_str, replace_str, commit_message, pr_title, pr_description)
    except Exception as e:
        print(f'Error: {str(e)}')
        raise
#endregion
