import os
import requests  # For making HTTP requests to APIs and websites
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart  # For creating email messages with multiple parts
from email.mime.text import MIMEText  # For creating text or HTML email content
import smtplib  # For sending emails via SMTP
import pytz  # For timezone handling
import ssl  # For secure network connections
import socket  # For network communications
import json  # For parsing JSON data
import logging  # For logging information during execution

# Configure logging with timestamp and log level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_scheme(url):
    """
    Ensures the URL has an HTTP or HTTPS scheme.
    
    Args:
        url (str): URL to check or modify
    
    Returns:
        str: URL with 'https://' prefix if no scheme is present
    """
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url  # Add 'https://' if missing
    return url

def fetch_wp_directory(slug, type='plugin'):
    """
    Fetches version information from the WordPress.org API.
    
    Args:
        slug (str): Plugin or theme slug to check
        type (str): Either 'plugin' or 'theme'
    
    Returns:
        dict or None: Version information dict or None if not found
    """
    # List of premium themes/plugins that shouldn't be checked against WP directory
    exempt_slugs = [
        'avada', 'avada-builder', 'avada-core', 'avada-child',
        'avadachild', 'avada_child', 'avadacore', 'avada_core',
        'avadabuilder', 'avada_builder'
    ]
    
    # Skip WordPress.org check for exempt items
    if slug.lower() in exempt_slugs:
        logging.info(f"Exempting {slug} from WordPress API checks.")
        return None
        
    # Construct the appropriate WordPress API URL based on type
    if type == 'plugin':
        # API endpoint for plugins
        api_url = f"https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]={slug}"
    else:
        # API endpoint for themes
        api_url = f"https://api.wordpress.org/themes/info/1.2/?action=theme_information&request[slug]={slug}"
    
    # Make the API request with error handling
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise exception for bad HTTP status
        return response.json()  # Return the JSON response as a dictionary
    except requests.RequestException as e:
        logging.error(f"Error fetching {type} info for {slug}: {e}")
        return None
# Fetch info from Envato Shop website about the installed premium themes/plugins that are not installed from WP directory
def fetch_envato_version(item_id):
    """
    Fetches version information from Envato API for premium items.
    
    Args:
        item_id (str): Envato item ID
    
    Returns:
        str or None: Latest version string or None if not found
    """
    url = f"https://api.envato.com/v3/market/catalog/item-version?id={item_id}"
    # Add authorization header with API key from environment variable
    headers = {
        "Authorization": f"Bearer {os.getenv('ENVATO_API_KEY')}"  # ENVATO_API_KEY must be set in environment variables (as a Github Action Secret)
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for bad HTTP status
        data = response.json()
        # Return the latest version for themes or plugins
        return data.get("wordpress_theme_latest_version") or data.get("wordpress_plugin_latest_version")
    except requests.RequestException as e:
        logging.error(f"Error fetching Envato info for item ID {item_id}: {e}")
        return None

# Item IDs for known Envato premium items
envato_items = {
    'avada': '2833226', # Avada Wordpress template (quite popular - good as an example). The number is taken from the Envato api documentation.
}

def generate_slugs(name):
    """
    Generates possible slugs for a plugin or theme name.
    
    Args:
        name (str): The name of the plugin or theme
    
    Returns:
        list: List of possible slug strings
    """
    # Handle specific known cases for plugins and themes. Gods.. have anyone ever heard about something like standardisation? Wordpress themes and plugins directory haven't.
    special_cases = {
        # Plugins are only as an example. you need to populate this list by yourselft by the 'Trails of Errors'.
        'Cookie-Banner-Plugin für WordPress – Cookiebot CMP by Usercentrics': 'cookiebot',
        'Complianz – GDPR/CCPA Cookie Consent': 'complianz-gdpr',
        'Yoast SEO': 'wordpress-seo',
        'WP Social Widget': 'wp-social-widget',
        'Smush': 'wp-smushit',
        'Self-Hosted Google Fonts': 'selfhost-google-fonts',
        'ShortPixel Image Optimizer': 'shortpixel-image-optimiser',
        'WPCode Lite': 'insert-headers-and-footers',
        # Themes- same as plugins - you are on your own here.
        'Twenty Twenty-Four': 'twentytwentyfour',
    }
    if name in special_cases:
        return [special_cases[name]]
    
    # Generate general slugs by manipulating the name
    slugs = [
        name.lower().replace(' ', '-'),
        name.lower().replace(' ', '_'),
        name.lower().replace(' ', ''),
        name.lower().replace(' ', '-').replace('.', '')
    ]
    return slugs

def get_versions(url):
    """
    Retrieves version information for a WordPress site.
    
    Args:
        url (str): The URL of the WordPress site
    
    Returns:
        tuple: PHP version, WordPress version, plugins list, themes list
    """
    url = add_scheme(url)
    version_info_url = f"{url}/version-info.php"  # URL to the version info script installed on the website. Name it as you want it.
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'X-Auth-Key': os.getenv('GH_TOKEN')  # Authentication header; GH_TOKEN should be set in environment variables (as a Github Action Secret).
    }
    try:
        response = requests.get(version_info_url, headers=headers)
        response.raise_for_status()  # Raise exception for bad HTTP status
        version_info = response.json()
        php_version = version_info.get('php_version', 'Unknown')
        wp_version = version_info.get('wp_version', 'Unknown')
        plugins = version_info.get('plugins', [])
        themes = version_info.get('themes', [])

        # Update plugins with their latest versions
        for plugin in plugins:
            plugin_name = plugin['name']
            for slug in generate_slugs(plugin_name):
                plugin_info = fetch_wp_directory(slug, 'plugin')
                if plugin_info and 'version' in plugin_info:
                    plugin['latest_version'] = plugin_info['version']
                    break  # Break if version is found
            else:
                plugin['latest_version'] = 'Unknown'  # Set as 'Unknown' if not found

        # Update themes with their latest versions
        for theme in themes:
            theme_name = theme['name']
            if theme_name.lower() in ['avada', 'avada child']:
                # Handle Avada theme separately using Envato API
                theme_info = None
                if theme_name.lower() == 'avada':
                    theme_info = fetch_envato_version(envato_items['avada'])
                theme['latest_version'] = theme_info if theme_info else theme['version']
            else:
                for slug in generate_slugs(theme_name):
                    theme_info = fetch_wp_directory(slug, 'theme')
                    if theme_info and 'version' in theme_info:
                        theme['latest_version'] = theme_info['version']
                        break  # Break if version is found
                else:
                    theme['latest_version'] = 'Unknown'  # Set as 'Unknown' if not found

    except requests.RequestException as e:
        logging.error(f"Error fetching version info for {url}: {e}")
        php_version = 'Unknown'
        wp_version = 'Unknown'
        plugins = []
        themes = []

    return php_version, wp_version, plugins, themes

def check_ssl_certificate(url):
    """
    Checks the SSL certificate of the given URL.
    
    Args:
        url (str): The URL to check
    
    Returns:
        tuple: (bool indicating validity, expiry date or error message)
    """
    try:
        hostname = url.split("//")[-1].split("/")[0]  # Extract the hostname from the URL
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                # Parse the expiry date of the certificate
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                return True, expiry_date  # Return validity and expiry date
    except Exception as e:
        logging.error(f"Error checking SSL certificate for {url}: {e}")
        return False, str(e)  # Return invalidity and error message

def get_performance_metrics(url):
    """
    Retrieves performance metrics using Google PageSpeed Insights API.
    
    Args:
        url (str): The URL to check
    
    Returns:
        str: Performance score or 'N/A' if unavailable
    """
    api_key = os.getenv('PAGE_SPEED_API_KEY')  # API key must be set in environment variables (as a Github Action Secret).
    if not api_key:
        logging.error("Google PageSpeed Insights API key is missing.")
        return 'N/A'
    
    url = add_scheme(url)
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # Extract performance score from the API response
        performance_score = data['lighthouseResult']['categories']['performance']['score'] * 100
        return performance_score
    except requests.RequestException as e:
        logging.error(f"Error fetching performance metrics for {url}: {e}")
        return 'N/A'
    except KeyError:
        logging.error("Required data not found in PageSpeed Insights API response.")
        return 'N/A'

def scan_for_malware(url):
    """
    Scans the URL for malware using Google Safe Browsing API.
    
    Args:
        url (str): The URL to scan
    
    Returns:
        str: 'Malware found', 'No malware detected', or 'Scan failed'
    """
    api_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    payload = {
        "client": {
            "clientId": "yourcompanyname",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': os.getenv('SAFE_BROWSING_API_KEY')  # API key must be set in environment variables (as a Github Action Secret).
    }

    try:
        response = requests.post(api_url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        data = response.json()
        if 'matches' in data and data['matches']:
            return "Malware found"
        else:
            return "No malware detected"
    except requests.RequestException as e:
        logging.error(f"Error scanning for malware on {url}: {e}")
        return "Scan failed"

def check_uptime(url):
    """
    Checks if the website is online.
    
    Args:
        url (str): The URL to check
    
    Returns:
        str: 'Online' or 'Error' with HTML color coding
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return "<span style='color:green;'>Online</span>"
    except requests.RequestException as e:
        logging.error(f"Error checking uptime for {url}: {e}")
        return "<span style='color:red;'>Error</span>"

def send_email(subject, body, to_emails):
    """
    Sends an email with the given subject and body to the specified recipients.
    
    Args:
        subject (str): Email subject
        body (str): Email body in HTML format
        to_emails (list): List of recipient email addresses
    
    Returns:
        None
    """
    from_email = os.getenv('EMAIL_ADDRESS')  # Sender's email address from environment variable (as a Github Action Secret).
    email_password = os.getenv('EMAIL_PASSWORD')  # Sender's email password from environment variable (as a Github Action Secret).

    # Setup the MIME message
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = ', '.join(to_emails)
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    try:
        # Fetch SMTP details from environment variables
        smtp_server = os.getenv('SMTP_SERVER')  # SMTP server address; should be set in environment variables (as a Github Action Secret).
        smtp_port = int(os.getenv('SMTP_PORT'))  # SMTP server port; usually 587 for TLS (also set as a Github Action Secret)
        smtp_user = os.getenv('SMTP_USER')  # SMTP username; typically the email address (set as a Github Action Secret)
        smtp_password = os.getenv('SMTP_PASSWORD')  # SMTP password; email account password (obviously set as a Github Action Secret)
        # smtp_server value needs to be set in environment variables (e.g., 'smtp.gmail.com' or your SMTP server)
        # smtp_port value is set in environment variables (common ports: 587 for TLS, 465 for SSL)
        # smtp_user is your email address or username used for SMTP authentication
        # smtp_password is the password for your email account used for SMTP authentication

        # Connect to the SMTP server with a secure TLS connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Start TLS encryption
        server.login(smtp_user, smtp_password)  # Log in to the SMTP server with credentials

        # Send the email
        server.sendmail(from_email, to_emails, message.as_string())
        server.quit()
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def main():
    """
    Main function to orchestrate the monitoring and reporting processes.
    
    Returns:
        None
    """
    # Get the list of URLs and recipient emails from environment variables
    urls = os.getenv('URLS').split(',')  # List of URLs to check
    to_emails = os.getenv('TO_EMAIL').split(',')  # List of recipient email addresses
    poland_tz = pytz.timezone('Europe/Warsaw')  # Timezone for reporting (as I'm based in Poland- hence Warsaw).

    results = []  # List to store the results for each site

    for url in urls:
        url = add_scheme(url.strip())
        logging.info(f"Processing URL: {url}")

        # Get versions and component info
        php_version, wp_version, plugins, themes = get_versions(url)

        # Check SSL certificate status and expiry
        ssl_valid, ssl_info = check_ssl_certificate(url)
        if ssl_valid and isinstance(ssl_info, datetime):
            # SSL certificate is valid; calculate time until expiry
            current_time = datetime.now(poland_tz)
            ssl_info = ssl_info.replace(tzinfo=pytz.UTC)  # Ensure timezone-aware
            days_until_expiry = (ssl_info - current_time).days

            # Set color based on days until expiry
            if days_until_expiry > 30:
                ssl_expiry_color = 'green'
            elif days_until_expiry > 0:
                ssl_expiry_color = 'orange'
            else:
                ssl_expiry_color = 'red'

            ssl_status = "<span style='color:green;'>Valid</span>"
            ssl_expiry_date = ssl_info.astimezone(poland_tz).strftime('%Y-%m-%d') # Again - the time format is set for Poland.
        else:
            # SSL certificate is invalid or an error occurred
            ssl_status = "<span style='color:red;'>Invalid</span>"
            ssl_expiry_date = "N/A"
            ssl_expiry_color = 'red'

        # Get performance score
        performance_score = get_performance_metrics(url)

        # Perform malware scan
        malware_scan = scan_for_malware(url)

        # Check uptime status
        uptime_status = check_uptime(url)

        # Record the check time
        checked_at = datetime.now(poland_tz).strftime('%Y-%m-%d %H:%M:%S') # Again - the time format is set for Poland.

        # Compile all results for the site
        result = {
            'url': url,
            'php_version': php_version,
            'wp_version': wp_version,
            'plugins': plugins,
            'themes': themes,
            'performance_score': performance_score,
            'malware_scan': malware_scan,
            'ssl_status': ssl_status,
            'ssl_expiry_date': ssl_expiry_date,
            'ssl_expiry_color': ssl_expiry_color,
            'uptime_status': uptime_status,
            'checked_at': checked_at
        }
        results.append(result)

        time.sleep(5)  # Rate limiting: pause for 5 seconds between requests. Some hosing are eager to ban anything bothering their servers with questions.. This value can be modified to accomodate that.

    # Prepare email content
    email_subject = "Installed PHP, WordPress & Plugins Version Check Results"
    email_body = """
    <html>
    <body>
    <h4>Website Checks:</h4>
    <table border='1' style='border-collapse: collapse; width: 100%;'>
    <tr>
        <th style='padding: 8px; text-align: center;'>URL</th>
        <th style='padding: 8px; text-align: center;'>PHP Version</th>
        <th style='padding: 8px; text-align: center;'>WordPress Version</th>
        <th style='padding: 8px; text-align: center;'>SSL Status</th>
        <th style='padding: 8px; text-align: center;'>SSL Expiry Date</th>
        <th style='padding: 8px; text-align: center;'>Performance Score</th>
        <th style='padding: 8px; text-align: center;'>Malware Scan</th>
        <th style='padding: 8px; text-align: center;'>Uptime Status</th>
        <th style='padding: 8px; text-align: center;'>Checked At</th>
    </tr>
    """

    # Populate the email body with results
    for result in results:
        email_body += f"""
        <tr>
        <td style='padding: 8px; text-align: center;'>{result['url']}</td>
        <td style='padding: 8px; text-align: center;'>{result['php_version']}</td>
        <td style='padding: 8px; text-align: center;'>{result['wp_version']}</td>
        <td style='padding: 8px; text-align: center; color: {result['ssl_expiry_color']}'>{result['ssl_status']}</td>
        <td style='padding: 8px; text-align: center; color: {result['ssl_expiry_color']}'>{result['ssl_expiry_date']}</td>
        <td style='padding: 8px; text-align: center;'>{result['performance_score']}</td>
        <td style='padding: 8px; text-align: center;'>{result['malware_scan']}</td>
        <td style='padding: 8px; text-align: center;'>{result['uptime_status']}</td>
        <td style='padding: 8px; text-align: center;'>{result['checked_at']}</td>
        </tr>
        """

    email_body += """
    </table>
    <h3>Plugins and Themes</h3>
    """

    # Add plugin and theme details for each site
    for result in results:
        email_body += f"<h4>{result['url']}</h4>"

        # Plugins table
        email_body += """
        <h5>Plugins:</h5>
        <table border='1' style='border-collapse: collapse; width: 100%;'>
        <tr>
            <th>Plugin</th>
            <th>Installed Version</th>
            <th>Latest Version</th>
        </tr>
        """
        for plugin in result['plugins']:
            plugin_name = plugin.get('name', 'Unknown')
            installed_version = plugin['version']
            latest_version = plugin['latest_version']

            # Set color based on version comparison
            if latest_version != 'Unknown' and latest_version > installed_version:
                version_color = "#E67E22"  # Orange for updates available
            else:
                version_color = "black"

            if latest_version == 'Unknown':
                latest_version_display = "<span style='color:red;'>Unknown</span>"
            else:
                latest_version_display = latest_version

            email_body += f"""
            <tr>
                <td>{plugin_name}</td>
                <td>{installed_version}</td>
                <td style='color: {version_color}'>{latest_version_display}</td>
            </tr>
            """

        email_body += "</table>"

        # Themes table
        email_body += """
        <h5>Themes:</h5>
        <table border='1' style='border-collapse: collapse; width: 100%;'>
        <tr>
            <th>Theme</th>
            <th>Installed Version</th>
            <th>Latest Version</th>
        </tr>
        """
        for theme in result['themes']:
            theme_name = theme['name']
            installed_version = theme['version']
            latest_version = theme['latest_version']

            # Set color based on version comparison
            if latest_version != 'Unknown' and latest_version > installed_version:
                version_color = "#E67E22"  # Orange for updates available
            else:
                version_color = "black"

            if latest_version == 'Unknown':
                latest_version_display = "<span style='color:red;'>Unknown</span>"
            else:
                latest_version_display = latest_version

            email_body += f"""
            <tr>
                <td>{theme_name}</td>
                <td>{installed_version}</td>
                <td style='color: {version_color}'>{latest_version_display}</td>
            </tr>
            """

        email_body += "</table>"

    email_body += "</body></html>"

    # Send the compiled email to recipients
    send_email(email_subject, email_body, to_emails)

if __name__ == "__main__":
    main()
