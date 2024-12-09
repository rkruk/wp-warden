import requests

def fetch_envato_version(item_id):
    # url = f"https://api.envato.com/v3/market/catalog/item-version?id={item_id}"
    # You need a “personal token” before you can validate purchase codes for your items. 
    # This is similar to a password that grants limited access to your account, but it’s exclusively for the API.
    # Go to https://build.envato.com/create-token/ (sign in if prompted).
    # For purchase code verification you must select the following permissions (see this screenshot):
    # View and search Envato sites (selected by default)
    # View the user’s items’ sales history
    # After creating the token , copy and save it somewhere. Envato won’t show the token to you again. 
    # The token is set below as a 'randomStringNumber':
    headers = {
        "Authorization": "Bearer randomStringNumber" # Modify this value!
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("wordpress_theme_latest_version") or data.get("wordpress_plugin_latest_version")
    except requests.RequestException as e:
        print(f"Error fetching Envato version for item {item_id}: {e}")
        return None

# List of item IDs to check
item_ids = ['2833226', '2885264', '2885332'] # Avada premium theme, Avada Builder, Fusion Builder,... the list is endless.

# Fetch and print the latest version for each item ID
for item_id in item_ids:
    print(f"Fetching latest version for item ID {item_id}...")
    latest_version = fetch_envato_version(item_id)
    
    if latest_version:
        print(f"Latest version for item ID {item_id}: {latest_version}")
    else:
        print(f"Failed to fetch latest version for item ID {item_id}")
