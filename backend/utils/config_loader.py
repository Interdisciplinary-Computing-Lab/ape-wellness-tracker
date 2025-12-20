"""
Configuration loader utility for loading settings from config files.
"""
import os
import json


def get_config_path():
    """Get the path to the settings.json config file"""
    # Get project root (go up from backend/utils to project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, 'config', 'settings.json')


def load_config():
    """Load configuration from settings.json file"""
    config_path = get_config_path()
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file not found
        return get_default_config()
    except json.JSONDecodeError:
        # Return default config if file is invalid
        return get_default_config()


def get_default_config():
    """Return default configuration values"""
    return {
        "feeding_periods": {
            "morning": {
                "display_name": "Morning (6 AM - 12 PM)",
                "default_hour": 9
            },
            "afternoon": {
                "display_name": "Afternoon (12 PM - 6 PM)",
                "default_hour": 15
            },
            "evening": {
                "display_name": "Evening (6 PM - 12 AM)",
                "default_hour": 21
            },
            "night": {
                "display_name": "Night (12 AM - 6 AM)",
                "default_hour": 3
            }
        },
        "nutrition_defaults": {
            "default_protein_g": 2.0,
            "default_fiber_g": 1.0
        },
        "file_upload": {
            "max_file_size_mb": 5,
            "allowed_extensions": ["png", "jpg", "jpeg", "gif", "webp"]
        }
    }


def get_feeding_periods():
    """Get feeding periods dictionary from config"""
    config = load_config()
    periods = {}
    for key, value in config.get('feeding_periods', {}).items():
        periods[key] = value.get('display_name', key)
    return periods


def get_feeding_period_hour(period):
    """Get the default hour for a feeding period"""
    config = load_config()
    period_config = config.get('feeding_periods', {}).get(period, {})
    return period_config.get('default_hour', 9)


def get_nutrition_defaults():
    """Get default nutrition values from config"""
    config = load_config()
    defaults = config.get('nutrition_defaults', {})
    return {
        'protein_g': defaults.get('default_protein_g', 2.0),
        'fiber_g': defaults.get('default_fiber_g', 1.0)
    }

