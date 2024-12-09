# Version Checker for WordPress Sites

This repository contains code to perform automated checks on WordPress websites, specifically focusing on PHP, WordPress core, plugin, and theme versions. It also includes a GitHub Actions workflow to run these checks on a list of websites, providing essential information for website maintenance and security. This tool is the public version of the tool I'm using to monitor various websites.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Examples](#examples)
- [GitHub Actions Workflow](#github-actions-workflow)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The `version-info.php` script in this repository retrieves version information from WordPress sites, including PHP version, WordPress version, active plugins, and themes. It checks if a request is authorized by comparing the client's IP or a provided authorization header, ensuring only approved parties access this information. The GitHub Actions workflow automates these checks, running them on specified URLs and providing results through email or other notifications.

## Requirements

- PHP 7.4+ installed on the WordPress server
- `check_versions.py` Python script with dependencies:
  - `requests`
  - `pytz`
  - `Jinja2`

## Getting Started

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/rkruk/wp-warden.git
   cd version-checker
   ```

2. Install Python Dependencies:

```bash
python -m pip install --upgrade pip
pip install requests pytz Jinja2
```

3. Set Up Secrets in GitHub: Configure the following secrets in your GitHub repository:
- GH_TOKEN: GitHub token for authorization
- PAGE_SPEED_API_KEY: API key for Google PageSpeed Insights (optional)
- SAFE_BROWSING_API_KEY: API key for Google Safe Browsing (optional)
- ENVATO_API_TOKEN: Envato API token for premium plugins and templates available at Envato website
- EMAIL_ADDRESS: Email address used for sending notifications
- EMAIL_PASSWORD: Password for the email address used
- SMTP_SERVER: SMTP address
- SMTP_PORT: SMTP Port (587 or else)
- TO_EMAIL: Recipient email addresses (comma-separated)

## Configuration

PHP File (version-info.php)

Place the version-info.php script in the root of each WordPress site you want to monitor. This file includes:

- Authorization Header:
  - Custom header X-Auth-Key with a pre-defined secret (replace YOUR_SECRET_KEY with your unique key).
- Allowed IPs:
  - Set of IPs allowed to access the endpoint (allowed_ips array).
  - Local IP 127.0.0.1 included for testing purposes.
Configure these values based on your security preferences.

Python Script (check_versions.py)
This script:
- Sends requests to version-info.php endpoints to retrieve version details.
- Allows configuration of authorization headers and IP addresses to interact securely with the PHP file.

GitHub Actions Workflow (check-versions.yml)
The .github/workflows/check-versions.yml file defines the automated workflow:
- Inputs:
  - urls: Comma-separated list of URLs to check.
  - use_file: Option to read URLs from a url-list.txt file.
  - full_check: Boolean to perform a full scan on each URL.

## Usage
Running the PHP Script
- Place version-info.php in the root directory of a WordPress site.
- Send a request to it:
  
```bash
curl -H "X-Auth-Key: YOUR_SECRET_KEY" http://yourwordpresssite.com/version-info.php
```

Running the Python Script
- Execute the check_versions.py script:
```bash
python check_versions.py --urls "http://site1.com/version-info.php,http://site2.com/version-info.php" --full true
```

- Use --full true to perform a complete check (plugins, themes).
- Set --urls as a comma-separated list of URLs.
  
## GitHub Actions Workflow
To run the workflow:

1. Go to the Actions tab in your GitHub repository.
2. Select Check Versions and click Run workflow.
3. Provide values for:
  - urls: Optional comma-separated list of URLs.
  - use_file: Set to true to use url-list.txt file (if present).
  - full_check: Set to true for a detailed check.
The workflow will execute, fetching versions from each provided URL, and results will be available in the workflow logs or sent to the specified email.

## Examples
Example version-info.php Request:

```bash
curl -H "X-Auth-Key: YOUR_SECRET_KEY" http://example.com/version-info.php
```

Example Workflow Dispatch:
To use the workflow with URLs specified in a file:

```yaml
use_file: true
full_check: true
```

To specify URLs directly:

```yaml
urls: "http://example1.com/version-info.php,http://example2.com/version-info.php"
full_check: false
```

## Security
This repository uses an authorization key and IP allowlisting to ensure secure access to sensitive data. Consider these recommendations:

- Keep YOUR_SECRET_KEY confidential and unique per site.
- Use HTTPS for requests to prevent interception.
- Regularly update allowed_ips in version-info.php to restrict access.
  
## Contributing
Feel free to open issues or submit pull requests. Contributions should focus on improving security, adding new checks, or optimizing the codebase.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
