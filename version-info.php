<?php
// Retrieve the authorized key and value from environment variables
$authorized_key = getenv('AUTHORIZED_KEY');
$authorized_value = getenv('AUTHORIZED_VALUE');

// Retrieve the allowed IPs from an environment variable (comma-separated list)
$allowed_ips_env = getenv('ALLOWED_IPS');
$allowed_ips = array_map('trim', explode(',', $allowed_ips_env));

// Log client IP address (anonymized logging)
$client_ip = $_SERVER['REMOTE_ADDR'];
error_log("[version-info.php] Client IP Address: [REDACTED]", 0);  // Don't log real IPs in public logs

// Log received headers for debugging (anonymized)
error_log("[version-info.php] Received Headers: [ANONYMIZED]", 0);

// Check if the request contains the authorized header
$headers = getallheaders();
$authorized = isset($headers[$authorized_key]) && $headers[$authorized_key] === $authorized_value;

// Check if the client IP is in the allowed IP list
if (!$authorized && !in_array($client_ip, $allowed_ips)) {
    http_response_code(403);  // Forbidden
    echo '<html>Error 403 - Unauthorized Access</html>';
    exit; // Stop further processing
}

// Initialize variables
$php_version = phpversion();
$wp_version = '';
$plugins_data = [];
$themes_data = [];

// Define the WordPress path
$wp_path = $_SERVER['DOCUMENT_ROOT'];

// Check if the WordPress version file exists
if (file_exists($wp_path . '/wp-includes/version.php')) {
    // Include the WordPress version file
    include($wp_path . '/wp-includes/version.php');
    $wp_version = $wp_version;

    // Define the ABSPATH constant if not already defined
    if (!defined('ABSPATH')) {
        define('ABSPATH', $wp_path . '/');
    }

    // Ensure required WordPress files are included
    require_once(ABSPATH . 'wp-load.php');
    require_once(ABSPATH . 'wp-admin/includes/plugin.php');
    require_once(ABSPATH . 'wp-includes/pluggable.php');
    require_once(ABSPATH . 'wp-includes/theme.php');

    // Check if the required functions exist before calling
    if (function_exists('get_option') && function_exists('get_plugin_data') && function_exists('wp_get_themes')) {
        // Retrieve active plugins
        $active_plugins = get_option('active_plugins', []);
        foreach ($active_plugins as $plugin) {
            $plugin_path = WP_PLUGIN_DIR . '/' . $plugin;
            // Check if plugin path exists and is valid
            if (file_exists($plugin_path)) {
                $plugin_data = get_plugin_data($plugin_path);
                $plugins_data[] = [
                    'name' => $plugin_data['Name'],
                    'version' => $plugin_data['Version']
                ];
            } else {
                // Log error if plugin path is invalid
                error_log("[version-info.php] Plugin path does not exist: $plugin_path", 0);
            }
        }

        // Retrieve installed themes
        $themes = wp_get_themes();
        foreach ($themes as $theme) {
            $themes_data[] = [
                'name' => $theme->get('Name'),
                'version' => $theme->get('Version')
            ];
        }
    } else {
        // Log error if required WordPress functions are missing
        error_log("[version-info.php] Required WordPress functions do not exist", 0);
    }
} else {
    // Log error if version.php file is missing
    error_log("[version-info.php] version.php file does not exist in wp-includes directory.", 0);
}

// Output version information in JSON format (ensure safe output)
header('Content-Type: application/json');
echo json_encode([
    'php_version' => $php_version,
    'wp_version' => $wp_version,
    'plugins' => $plugins_data,
    'themes' => $themes_data
]);
?>
