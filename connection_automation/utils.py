"""
Utility functions for connection automation
"""
import time
import random
import os
from datetime import datetime


def random_sleep(min_sec, max_sec):
    """
    Sleep for a random duration between min_sec and max_sec seconds.
    Simulates human-like delay patterns.
    """
    duration = random.uniform(min_sec, max_sec)
    time.sleep(duration)


def normalize_profile_url(url):
    """
    Normalize LinkedIn profile URL by removing query parameters
    and ensuring consistent format.

    Example:
        Input:  https://www.linkedin.com/in/johndoe?trackingId=...
        Output: https://www.linkedin.com/in/johndoe/
    """
    if not url:
        return None

    # Remove query parameters
    clean_url = url.split('?')[0]

    # Ensure trailing slash
    if not clean_url.endswith('/'):
        clean_url += '/'

    return clean_url


def extract_profile_id(url):
    """
    Extract profile ID from LinkedIn URL.

    Example:
        Input:  https://www.linkedin.com/in/johndoe123/
        Output: johndoe123
    """
    if not url:
        return None

    # Remove trailing slash and split
    url = url.rstrip('/')
    parts = url.split('/')

    # Profile ID is the last part
    if 'linkedin.com/in/' in url:
        return parts[-1]

    return None


def format_timestamp(dt=None):
    """
    Format datetime as string.
    If no datetime provided, use current time.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def ensure_directory_exists(dirpath):
    """
    Create directory if it doesn't exist.
    """
    os.makedirs(dirpath, exist_ok=True)


def truncate_text(text, max_length=50):
    """
    Truncate text to max_length characters and add ellipsis if needed.
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length-3] + "..."


def validate_profile_url(url):
    """
    Check if URL is a valid LinkedIn profile URL.

    Returns: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Must contain linkedin.com/in/
    if 'linkedin.com/in/' not in url.lower():
        return False

    # Must start with http or https
    if not url.startswith('http'):
        return False

    return True


def print_progress_bar(current, total, prefix='', length=50):
    """
    Print a progress bar to console.

    Args:
        current: Current progress value
        total: Total/maximum value
        prefix: Text to show before progress bar
        length: Length of progress bar in characters
    """
    percent = 100 * (current / float(total))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)

    print(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)

    if current == total:
        print()  # New line when complete


def format_duration(seconds):
    """
    Format duration in seconds as human-readable string.

    Example:
        Input:  125
        Output: "2m 5s"
    """
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
