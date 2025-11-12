"""
Configuration settings for LinkedIn connection automation
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rate Limits (CONSERVATIVE DEFAULTS)
DAILY_LIMIT = 20          # Max connection requests per day
WEEKLY_LIMIT = 80         # Max connection requests per week
PAUSE_EVERY_N = 5         # Take break after N requests

# Delays (seconds) - Randomized within ranges for human-like behavior
MIN_DELAY_BETWEEN_REQUESTS = 30   # Minimum delay between connection requests
MAX_DELAY_BETWEEN_REQUESTS = 90   # Maximum delay between connection requests
MIN_DELAY_BETWEEN_ACTIONS = 2     # Minimum delay between page actions
MAX_DELAY_BETWEEN_ACTIONS = 5     # Maximum delay between page actions
BREAK_DURATION_MIN = 120          # 2 min break minimum
BREAK_DURATION_MAX = 300          # 5 min break maximum

# Connection Request Settings
SEND_WITH_NOTE = False            # Do NOT add personalized messages
DEFAULT_MESSAGE = ""              # No message template

# Tracking & Logging
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

TRACKING_DB = os.path.join(OUTPUT_DIR, "connections.db")
LOG_FILE = os.path.join(OUTPUT_DIR, "connection_log.json")
CSV_OUTPUT = os.path.join(OUTPUT_DIR, "connections_sent.csv")

# LinkedIn URLs
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_PROFILE_BASE = "https://www.linkedin.com/in/"

# Selenium Settings
PAGE_LOAD_TIMEOUT = 10           # Seconds to wait for page load
ELEMENT_WAIT_TIMEOUT = 5         # Seconds to wait for elements

# Retry Settings (disabled per user request)
ENABLE_RETRY = False             # Do not retry failed connections
MAX_RETRIES = 0                  # No retries

# Randomization Settings (disabled per user request)
RANDOMIZE_ORDER = False          # Process profiles sequentially

# Notification Settings (disabled per user request)
ENABLE_NOTIFICATIONS = False     # No email/Slack notifications
