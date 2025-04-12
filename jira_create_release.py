#!/usr/bin/env python3
"""
JIRA Release Creator

This script creates a new release in a specified JIRA project and adds it as a fixVersion
to all JIRA tickets with a specified status. The new fixVersion is added without removing
any existing fixVersions.

Usage:
    python jira_create_release.py --release-name <release_name> --project <project_name> --status <ticket_status>

Example:
    python jira_create_release.py --release-name "v1.2.3" --project "PROJ" --status "Ready for Release"
"""

import argparse
import os
import sys
import requests
import json
from datetime import datetime

class JiraReleaseCreator:
    def __init__(self, release_name, project_name, ticket_status):
        """
        Initialize the JIRA Release Creator.
        
        Args:
            release_name (str): The name of the release to create.
            project_name (str): The JIRA project key.
            ticket_status (str): The status of tickets to update.
        """
        self.release_name = release_name
        self.project_name = project_name
        self.ticket_status = ticket_status
        
        # JIRA API configuration
        self.jira_base_url = os.environ.get('JIRA_BASE_URL', 'https://your-jira-instance.atlassian.net')
        self.jira_username = os.environ.get('JIRA_USERNAME')
        self.jira_api_token = os.environ.get('JIRA_API_TOKEN')
        
        if not self.jira_username or not self.jira_api_token:
            print("Error: JIRA_USERNAME and JIRA_API_TOKEN environment variables must be set.")
            sys.exit(1)
    
    def _make_jira_request(self, url, method='GET', params=None, data=None):
        """
        Make a request to the JIRA API.
        
        Args:
            url (str): The URL to request.
            method (str): The HTTP method to use (GET, POST, PUT).
            params (dict, optional): Query parameters. Defaults to None.
            data (dict, optional): JSON data for POST/PUT requests. Defaults to None.
        
        Returns:
            dict: The JSON response.
        """
        auth = (self.jira_username, self.jira_api_token)
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, auth=auth, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, auth=auth, headers=headers, json=data)
            else:
                print(f"Error: Unsupported HTTP method: {method}")
                sys.exit(1)
            
            response.raise_for_status()
            
            # Some endpoints return no content
            if response.status_code == 204 or not response.text:
                return {}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to JIRA API: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            sys.exit(1)
    
    def get_current_user(self):
        """
        Get the current user's information.
        
        Returns:
            dict: The current user's information.
        """
        url = f"{self.jira_base_url}/rest/api/2/myself"
        return self._make_jira_request(url)
    
    def create_release(self):
        """
        Create a new release in the specified project.
        
        Returns:
            dict: The created release information.
        """
        # Get current user to set as the release owner
        current_user = self.get_current_user()
        
        # Create the release
        url = f"{self.jira_base_url}/rest/api/2/version"
        data = {
            "name": self.release_name,
            "project": self.project_name,
            "released": False,
            "userReleaseDate": datetime.now().strftime("%Y-%m-%d"),
            "projectId": None  # This will be determined by the project name
        }
        
        # Add owner if available
        if current_user and 'key' in current_user:
            data["owner"] = current_user['key']
        
        print(f"Creating release '{self.release_name}' in project '{self.project_name}'...")
        response = self._make_jira_request(url, method='POST', data=data)
        
        print(f"Release created successfully: {response.get('name', self.release_name)}")
        return response
    
    def get_tickets_with_status(self):
        """
        Get all tickets with the specified status in the project.
        
        Returns:
            list: A list of JIRA issue objects.
        """
        # JQL query to find all issues with the specified status in the project
        jql = f'project = "{self.project_name}" AND status = "{self.ticket_status}" ORDER BY created ASC'
        url = f"{self.jira_base_url}/rest/api/2/search"
        params = {
            'jql': jql,
            'fields': 'key,summary,status,fixVersions',
            'maxResults': 1000
        }
        
        response = self._make_jira_request(url, params=params)
        issues = response.get('issues', [])
        
        print(f"Found {len(issues)} issues with status '{self.ticket_status}' in project '{self.project_name}'")
        return issues
    
    def add_fix_version_to_tickets(self, release_id, issues):
        """
        Add the new release as a fixVersion to the specified tickets.
        
        Args:
            release_id (str): The ID of the created release.
            issues (list): A list of JIRA issue objects.
        """
        for issue in issues:
            issue_key = issue['key']
            
            # Get current fixVersions
            current_fix_versions = issue.get('fields', {}).get('fixVersions', [])
            current_fix_version_ids = [v['id'] for v in current_fix_versions]
            
            # Add the new release ID if it's not already there
            if release_id not in current_fix_version_ids:
                current_fix_version_ids.append(release_id)
                
                # Update the issue
                url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}"
                data = {
                    "fields": {
                        "fixVersions": [{"id": version_id} for version_id in current_fix_version_ids]
                    }
                }
                
                self._make_jira_request(url, method='PUT', data=data)
                print(f"Added fixVersion to issue {issue_key}")
            else:
                print(f"Issue {issue_key} already has the fixVersion")
    
    def run(self):
        """
        Run the JIRA Release Creator.
        """
        print(f"Starting JIRA Release Creator")
        
        # Step 1: Create the release
        release = self.create_release()
        release_id = release.get('id')
        
        if not release_id:
            print("Error: Failed to get release ID from the created release")
            sys.exit(1)
        
        # Step 2: Get tickets with the specified status
        issues = self.get_tickets_with_status()
        
        # Step 3: Add the release as a fixVersion to the tickets
        self.add_fix_version_to_tickets(release_id, issues)
        
        print(f"JIRA Release Creator completed successfully!")
        print(f"Created release '{self.release_name}' and added it as a fixVersion to {len(issues)} issues")

def main():
    parser = argparse.ArgumentParser(description='JIRA Release Creator')
    parser.add_argument('--release-name', required=True, help='Name of the release to create')
    parser.add_argument('--project', required=True, help='JIRA project key')
    parser.add_argument('--status', required=True, help='Status of tickets to update')
    
    args = parser.parse_args()
    
    creator = JiraReleaseCreator(
        release_name=args.release_name,
        project_name=args.project,
        ticket_status=args.status
    )
    
    creator.run()

if __name__ == '__main__':
    main()