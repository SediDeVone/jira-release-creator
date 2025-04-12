# JIRA Release Creator

This script creates a new release in a specified JIRA project and adds it as a fixVersion to all JIRA tickets with a specified status. The new fixVersion is added without removing any existing fixVersions.

## Prerequisites

- Python 3.6 or higher
- JIRA account with API access and permissions to create releases and update issues

## Installation

1. Ensure you have the required dependencies:

```bash
pip install requests
```

## Configuration

The script requires the following environment variables to be set:

- `JIRA_BASE_URL`: The base URL of your JIRA instance (e.g., `https://your-company.atlassian.net`)
- `JIRA_USERNAME`: Your JIRA username (usually your email address)
- `JIRA_API_TOKEN`: Your JIRA API token (can be generated in your Atlassian account settings)

You can set these environment variables in your shell:

```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or you can create a `.env` file and use a package like `python-dotenv` to load them.

## Usage

```bash
python jira_create_release.py --release-name <release_name> --project <project_name> --status <ticket_status>
```

### Arguments

- `--release-name`: The name of the release to create (required)
- `--project`: The JIRA project key (required)
- `--status`: The status of tickets to update with the new fixVersion (required)

### Example

```bash
python jira_create_release.py --release-name "v1.2.3" --project "PROJ" --status "Ready for Release"
```

This will:
1. Connect to your JIRA instance
2. Create a new release named "v1.2.3" in the "PROJ" project
3. Set the current user as the owner of the release
4. Find all issues in the "PROJ" project with status "Ready for Release"
5. Add the new release as a fixVersion to these issues without removing any existing fixVersions

## How It Works

1. **Authentication**: The script uses basic authentication with your JIRA username and API token.
2. **Creating a Release**: The script creates a new release in the specified project using the JIRA API.
3. **Finding Tickets**: The script uses JQL (JIRA Query Language) to find all tickets with the specified status in the project.
4. **Updating Tickets**: For each ticket found, the script adds the new release as a fixVersion without removing any existing fixVersions.

## Troubleshooting

- **JIRA API Errors**: Make sure your environment variables are set correctly and that your API token has the necessary permissions.
- **Permission Issues**: Ensure your JIRA account has permissions to create releases and update issues in the specified project.
- **Status Not Found**: Verify that the status you specified exists in your JIRA project and is spelled correctly (case-sensitive).

## License

This project is licensed under the MIT License - see the LICENSE file for details.