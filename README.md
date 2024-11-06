# fabric-ci-cd
Fabric CI/CD using github Actions and Microsoft Fabric REST endpoints: https://learn.microsoft.com/en-us/rest/api/fabric/articles/

This project provides a set of scripts and configurations to build custom CI/CD for Fabric workspaces. It utilizes the Microsoft Fabric REST API and Azure Active Directory authentication to import/export resources from a source workspace and import them into a target workspace.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running the Script Locally](#running-the-script-locally)
- [Continuous Integration with GitHub Actions](#continuous-integration-with-github-actions)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- Python 3.8 or higher
- Pip package manager
- An Azure Active Directory tenant
- Service principal with permissions to access Microsoft Fabric resources in both source and target subscriptions
- Access to the source and target Microsoft Fabric workspaces
- GitHub account for running GitHub Actions (optional, for CI/CD pipeline)

## Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/azure-data-ai-hub/fabric-ci-cd.git
   cd fabric-ci-cd
   ```

2. **Install Dependencies**

   Install the required Python packages:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   Alternatively, you can manually install the dependencies:

   ```bash
   pip install requests azure-identity azure-mgmt-powerbiembedded
   ```

## Environment Variables

The script uses environment variables to securely handle sensitive information. Set the following environment variables in your environment:

### Source Workspace Configuration

- `SOURCE_AZURE_CLIENT_ID`: Client ID of the service principal with access to the source workspace
- `SOURCE_AZURE_CLIENT_SECRET`: Client Secret of the service principal
- `SOURCE_AZURE_TENANT_ID`: Tenant ID of the Azure Active Directory where the service principal is registered
- `SOURCE_SUBSCRIPTION_ID`: Azure subscription ID containing the source workspace
- `SOURCE_RESOURCE_GROUP`: Resource group name of the source workspace
- `SOURCE_WORKSPACE_ID`: ID of the source workspace
- `SOURCE_WORKSPACE_NAME`: Name of the source workspace

### Target Workspace Configuration

- `TARGET_AZURE_CLIENT_ID`: Client ID of the service principal with access to the target workspace
- `TARGET_AZURE_CLIENT_SECRET`: Client Secret of the service principal
- `TARGET_AZURE_TENANT_ID`: Tenant ID of the Azure Active Directory where the service principal is registered
- `TARGET_SUBSCRIPTION_ID`: Azure subscription ID containing the target workspace
- `TARGET_RESOURCE_GROUP`: Resource group name of the target workspace
- `TARGET_WORKSPACE_ID`: ID of the target workspace
- `TARGET_WORKSPACE_NAME`: Name of the target workspace

**Note:** Avoid hard-coding these credentials in your scripts or source control. Use environment variables or secret management tools.

## Running the Script Locally

1. **Set Environment Variables**

   Before running the script, ensure all required environment variables are set:

   ```bash
   export SOURCE_AZURE_CLIENT_ID='your_source_client_id'
   export SOURCE_AZURE_CLIENT_SECRET='your_source_client_secret'
   export SOURCE_AZURE_TENANT_ID='your_source_tenant_id'
   export SOURCE_SUBSCRIPTION_ID='your_source_subscription_id'
   export SOURCE_RESOURCE_GROUP='your_source_resource_group'
   export SOURCE_WORKSPACE_ID='your_source_workspace_id'
   export SOURCE_WORKSPACE_NAME='your_source_workspace_name'

   export TARGET_AZURE_CLIENT_ID='your_target_client_id'
   export TARGET_AZURE_CLIENT_SECRET='your_target_client_secret'
   export TARGET_AZURE_TENANT_ID='your_target_tenant_id'
   export TARGET_SUBSCRIPTION_ID='your_target_subscription_id'
   export TARGET_RESOURCE_GROUP='your_target_resource_group'
   export TARGET_WORKSPACE_ID='your_target_workspace_id'
   export TARGET_WORKSPACE_NAME='your_target_workspace_name'
   ```

2. **Run the Integration Script**

   Execute the script:

   ```bash
   python integration.py
   ```

   The script will:

   - Authenticate with Azure using service principals for both source and target subscriptions.
   - Retrieve datasets, reports, dashboards, and other resources from the source workspace.
   - Save the retrieved resources to JSON files.
   - Import the resources into the target workspace.

## Continuous Integration with GitHub Actions

The project includes an `integration.yml` GitHub Actions workflow file to automate the migration process.

### Setup Secrets in GitHub

1. Navigate to your GitHub repository.
2. Go to **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.
3. Add the environment variables listed above as secrets.

### Workflow File

The `integration.yml` workflow is triggered on every push to the repository. It performs the following steps:

- Checks out the code.
- Sets up Python environment.
- Installs dependencies.
- Runs the `integration.py` script.

**File:** `.github/workflows/integration.yml`

```yaml
name: Integration Pipeline

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run integration script
      env:
        SOURCE_AZURE_CLIENT_ID: ${{ secrets.SOURCE_AZURE_CLIENT_ID }}
        SOURCE_AZURE_CLIENT_SECRET: ${{ secrets.SOURCE_AZURE_CLIENT_SECRET }}
        SOURCE_AZURE_TENANT_ID: ${{ secrets.SOURCE_AZURE_TENANT_ID }}
        SOURCE_RESOURCE_GROUP: ${{ secrets.SOURCE_RESOURCE_GROUP }}
        SOURCE_WORKSPACE_ID: ${{ secrets.SOURCE_WORKSPACE_ID }}
        SOURCE_WORKSPACE_NAME: ${{ secrets.SOURCE_WORKSPACE_NAME }}
        TARGET_AZURE_CLIENT_ID: ${{ secrets.TARGET_AZURE_CLIENT_ID }}
        TARGET_AZURE_CLIENT_SECRET: ${{ secrets.TARGET_AZURE_CLIENT_SECRET }}
        TARGET_AZURE_TENANT_ID: ${{ secrets.TARGET_AZURE_TENANT_ID }}
        TARGET_RESOURCE_GROUP: ${{ secrets.TARGET_RESOURCE_GROUP }}
        TARGET_WORKSPACE_ID: ${{ secrets.TARGET_WORKSPACE_ID }}
        TARGET_WORKSPACE_NAME: ${{ secrets.TARGET_WORKSPACE_NAME }}
      run: |
        python integration.py
```

## Logging

The script uses Python's built-in 

logging

 module to provide detailed logs during execution. The logs include:

- Authentication steps and status.
- API request URLs and responses.
- Counts of resources retrieved and imported.
- Errors and exceptions encountered.

Logs are output to the console. You can adjust the logging level at the top of 

integration.py

:

```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
```

To enable debug-level logs, change 

level=logging.INFO

 to 

level=logging.DEBUG

.

## Troubleshooting

- **Authentication Errors:**
  - Verify that all client IDs, client secrets, tenant IDs, and subscription IDs are correct.
  - Ensure that service principals have the required permissions.

- **API Access Errors:**
  - Check if the API endpoints are correct and accessible.
  - Ensure that the resources exist in the source workspace.

- **Insufficient Permissions:**
  - Ensure that the service principals have access to read from the source workspace and write to the target workspace.

- **Azure SDK Errors:**
  - Verify that all dependencies are installed correctly.
  - Ensure compatibility between the Azure SDK versions and the Python version.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

When contributing, please ensure that your code follows best practices and includes appropriate logging.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
```

---

This `README.md` provides comprehensive instructions on setting up, configuring, and running your integration scripts, both locally and via GitHub Actions. It references the `integration.py` and `integration.yml` files and includes sections on prerequisites, setup, environment variables, logging, and troubleshooting.

Let me know if you need any further assistance or modifications.---

This `README.md` provides comprehensive instructions on setting up, configuring, and running your integration scripts, both locally and via GitHub Actions. It references the `integration.py` and `integration.yml` files and includes sections on prerequisites, setup, environment variables, logging, and troubleshooting.

Let me know if you need any further assistance or modifications.
