# LinkedIn Connection Request Automation

Automatically send connection requests to job posters whose profiles were captured during job scraping.

## ⚠️ **CRITICAL WARNING**

**This automation violates LinkedIn's Terms of Service.**

**Risks:**
- Account restrictions (temporary or permanent)
- Profile shadowbanning
- Complete account termination
- Loss of LinkedIn Premium features

**Use at your own risk. Educational purposes only.**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [Folder Structure](#folder-structure)
4. [Usage Guide](#usage-guide)
5. [Configuration](#configuration)
6. [Safety Features](#safety-features)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

1. **Scraped job data** with poster profiles:
   ```bash
   python3 scrape_search_results.py
   # Outputs: linkedin_jobs_search_YYYYMMDD_HHMMSS.json
   ```

2. **Move scraped file to input folder:**
   ```bash
   cp linkedin_jobs_search_*.json data/input/
   ```

### Test First (Recommended)

**Dry run** - Tests automation WITHOUT sending requests:

```bash
python3 scripts/dry_run.py
```

### Run Production

**Send actual connection requests:**

```bash
python3 scripts/run_connection_sender.py
```

---

## How It Works

### Workflow

```
1. Load scraped job data (JSON/CSV)
   ↓
2. Filter for jobs with poster_profile_url
   ↓
3. Deduplicate by profile (one person may post multiple jobs)
   ↓
4. Check tracking database (skip already contacted)
   ↓
5. Login to LinkedIn
   ↓
6. For each profile:
   - Navigate to profile URL
   - Check if already connected/pending
   - Find Connect button
   - Send connection request (no message)
   - Random delay (30-90 seconds)
   - Take break every 5 requests (2-5 minutes)
   ↓
7. Export results to CSV
   ↓
8. Generate summary report
```

### Data Flow

```
Input:  linkedin_jobs_search_YYYYMMDD_HHMMSS.json
        ↓
Filter: Jobs with poster_profile_url != null
        ↓
Output: connections_sent.csv
        connections.db (SQLite tracking)
        connection_log.json
```

---

## Folder Structure

```
linkedin_scraper/
├── connection_automation/       # Automation package
│   ├── __init__.py
│   ├── config.py               # Settings & rate limits
│   ├── utils.py                # Helper functions
│   ├── data_loader.py          # Load JSON/CSV
│   ├── tracker.py              # SQLite tracking
│   ├── safety_manager.py       # Quota enforcement
│   └── connection_sender.py    # Core automation
│
├── scripts/                     # Executable scripts
│   ├── run_connection_sender.py  # Production script
│   └── dry_run.py                # Test mode
│
├── data/                        # Data files
│   ├── input/                  # Place scraped JSON/CSV here
│   └── output/                 # Results saved here
│       ├── connections_sent.csv
│       ├── connections.db
│       └── connection_log.json
│
└── README_CONNECTIONS.md        # This file
```

---

## Usage Guide

### Step 1: Scrape Jobs

First, scrape job postings to collect poster profiles:

```bash
python3 scrape_search_results.py
```

**Output:** `linkedin_jobs_search_20251112_183212.json`

**Required fields:**
- `poster_profile_url` - Profile URL (e.g., https://linkedin.com/in/johndoe)
- `poster_profile_id` - Profile ID (e.g., johndoe)
- `poster_name` - Person's name
- `job_title` - Job title
- `company` - Company name

### Step 2: Move File to Input Folder

```bash
mv linkedin_jobs_search_*.json data/input/
```

### Step 3: Dry Run (Test Mode)

**Test WITHOUT sending requests:**

```bash
python3 scripts/dry_run.py
```

**Prompts:**
```
File path: data/input/linkedin_jobs_search_20251112_183212.json
Test count: 10
```

**What it does:**
- Loads 10 profiles
- Navigates to each profile
- Checks if Connect button exists
- Reports findings
- **NO CLICKING** - Safe for testing

**Example output:**
```
[1/10] John Doe (AI Engineer at OpenAI)
   URL: https://linkedin.com/in/johndoe
   📍 Navigating...
   ✅ Connect button found (would send request)

[2/10] Jane Smith (ML Engineer at Google)
   URL: https://linkedin.com/in/janesmith
   📍 Navigating...
   ⚠️  Already connected or pending

...

Dry Run Summary:
   Tested: 10
   Connect button found: 8
   Already connected: 2
   Connect button not found: 0
```

### Step 4: Production Run

**Send REAL connection requests:**

```bash
python3 scripts/run_connection_sender.py
```

**Prompts:**
```
File path: data/input/linkedin_jobs_search_20251112_183212.json
Daily limit: 20
```

**What it does:**
- Loads all profiles from file
- Filters out already contacted
- Checks daily/weekly quotas
- Sends up to 20 connection requests
- Random delays between requests (30-90 sec)
- Takes breaks every 5 requests (2-5 min)
- Exports results to CSV

**Example output:**
```
✓ Loaded 50 jobs from file
✓ Found 35 jobs with poster profiles
✓ Identified 30 unique poster profiles

📊 Quota Status:
   Daily:  5/20 used (15 remaining)
   Weekly: 5/80 used (75 remaining)

✓ Found 25 profiles to contact
  (Skipped 5 already contacted)

Will attempt to send 15 connection requests

[1/15] John Doe (AI Engineer at OpenAI)
   📍 Navigating to profile...
   🤝 Sending connection request...
   ✅ Connection request sent and verified
   ⏸️  Waiting...

[2/15] Jane Smith (ML Engineer at Google)
   📍 Navigating to profile...
   ⚠️  Already connected or pending

...

[5/15] Bob Johnson (Data Scientist at Meta)
   📍 Navigating to profile...
   🤝 Sending connection request...
   ✅ Connection request sent and verified
   ⏸️  Waiting...

   ☕ Taking a break...

...

Summary:
   Attempted: 15
   Successfully sent: 12
   Already connected: 3
   Failed: 0

📊 Quota Status:
   Daily:  17/20 used (3 remaining)
   Weekly: 17/80 used (63 remaining)

✓ Exported results to data/output/connections_sent.csv
```

---

## Configuration

### Default Settings

**File:** `connection_automation/config.py`

```python
# Rate Limits
DAILY_LIMIT = 20          # Max requests per day
WEEKLY_LIMIT = 80         # Max requests per week
PAUSE_EVERY_N = 5         # Break after N requests

# Delays (seconds)
MIN_DELAY_BETWEEN_REQUESTS = 30   # Between connection requests
MAX_DELAY_BETWEEN_REQUESTS = 90
MIN_DELAY_BETWEEN_ACTIONS = 2     # Between page actions
MAX_DELAY_BETWEEN_ACTIONS = 5
BREAK_DURATION_MIN = 120          # Break duration
BREAK_DURATION_MAX = 300

# Connection Settings
SEND_WITH_NOTE = False            # No personalized messages
RANDOMIZE_ORDER = False           # Sequential processing
ENABLE_RETRY = False              # No retry logic
ENABLE_NOTIFICATIONS = False      # No email/Slack alerts
```

### Customization

To change settings, edit `connection_automation/config.py`:

```python
# Example: Increase daily limit to 25
DAILY_LIMIT = 25

# Example: Longer delays
MIN_DELAY_BETWEEN_REQUESTS = 60
MAX_DELAY_BETWEEN_REQUESTS = 120
```

**Restart required** after changing config.

---

## Safety Features

### 1. Rate Limiting

**Hard limits** prevent exceeding safe thresholds:

| Limit Type | Default | Max Safe |
|------------|---------|----------|
| Per Day | 20 | 25 |
| Per Week | 80 | 100 |

**Automatic enforcement:**
- Checks quota before each request
- Stops when limit reached
- Resets daily (midnight)
- Resets weekly (7 days from first request)

### 2. Duplicate Prevention

**SQLite tracking database** prevents contacting same person twice:
- Records every profile contacted
- Checks before sending
- Resume capability if interrupted
- Persistent across runs

### 3. Random Delays

**Human-like behavior simulation:**
- 30-90 seconds between connection requests
- 2-5 seconds between page actions
- 2-5 minute breaks every 5 requests
- Randomized within ranges

### 4. Already Connected Detection

**Automatically skips:**
- Profiles already in your network ("Message" button)
- Pending connection requests ("Pending" button)
- Saves quota for new connections

### 5. Error Handling

**Graceful failures:**
- Continues to next profile on error
- Logs all failures
- Doesn't crash on single failure
- Exports results even if incomplete

---

## Output Files

### connections_sent.csv

**Location:** `data/output/connections_sent.csv`

**Columns:**
- `profile_id` - LinkedIn profile ID
- `profile_url` - Full profile URL
- `poster_name` - Person's name
- `job_title` - Job title from posting
- `company` - Company name
- `sent_at` - Timestamp
- `status` - success/already_connected/failed
- `error_message` - Error details (if failed)

**Example:**
```csv
profile_id,profile_url,poster_name,job_title,company,sent_at,status,error_message
johndoe,https://linkedin.com/in/johndoe,John Doe,AI Engineer,OpenAI,2025-11-12 18:45:23,success,
janesmith,https://linkedin.com/in/janesmith,Jane Smith,ML Engineer,Google,2025-11-12 18:46:15,already_connected,
```

### connections.db

**Location:** `data/output/connections.db`

**SQLite database** - Tracks all sent connections for:
- Duplicate prevention
- Quota calculation
- Resume capability
- Historical record

### connection_log.json

**Location:** `data/output/connection_log.json`

**JSON log** with run metadata:
- Run date
- Total attempted
- Success/failure counts
- Quota usage
- Detailed profile list

---

## Troubleshooting

### Issue: "Connect button not found"

**Possible causes:**
1. Already connected to person
2. LinkedIn UI changed
3. Profile restricted/private
4. Not logged in properly

**Solutions:**
- Run dry_run.py to verify
- Check if manually visible in browser
- Verify login successful
- Check profile URL is valid

### Issue: "Daily limit reached"

**Message:** `Cannot send requests: Daily limit reached (20/20)`

**Solution:**
- Wait until next day (midnight)
- Or increase daily limit in config.py (not recommended)

**Check reset time:**
```python
python3 -c "from connection_automation.safety_manager import SafetyManager; sm = SafetyManager(); print(sm.suggest_next_run_time())"
```

### Issue: "Already contacted" for all profiles

**Cause:** All profiles in tracking database

**Solutions:**

**Option 1: Scrape new jobs**
```bash
python3 scrape_search_results.py
# Get fresh job postings with new posters
```

**Option 2: Clear history (USE WITH CAUTION)**
```python
from connection_automation.tracker import ConnectionTracker
tracker = ConnectionTracker()
tracker.clear_all()  # Deletes all history!
```

### Issue: "Navigation failed"

**Possible causes:**
1. Invalid profile URL
2. Network timeout
3. LinkedIn blocking access

**Solutions:**
- Check URL format in scraped data
- Increase PAGE_LOAD_TIMEOUT in config.py
- Wait and try again later
- Check if manually accessible

### Issue: Bot detection / Account warning

**Symptoms:**
- LinkedIn shows "unusual activity" warning
- CAPTCHA challenges
- Login required repeatedly

**Solutions:**
- **STOP immediately**
- Wait 24-48 hours
- Reduce daily limit to 5-10
- Increase delays in config.py
- Use account warming strategy

### Issue: Low acceptance rate

**Problem:** Many people ignore/decline requests

**This triggers LinkedIn alerts!**

**Best practices:**
- Only connect with relevant people
- Don't spam unrelated profiles
- Consider adding personalized notes (edit config)
- Quality > Quantity

---

## Best Practices

### Account Warming (ESSENTIAL)

**Don't send 20 requests on day 1!**

**Recommended schedule:**
- **Week 1:** 5 requests/day
- **Week 2:** 10 requests/day
- **Week 3:** 15 requests/day
- **Week 4+:** 20 requests/day (max)

**Edit daily limit:**
```python
# config.py
DAILY_LIMIT = 5  # Start low
```

### Targeting

**Connect with relevant people:**
- Job posters in your industry
- Recruiters hiring for your skills
- People at target companies

**Avoid:**
- Random profiles
- CEOs (low acceptance rate)
- Unrelated industries

### Monitoring

**Check daily:**
- Acceptance rate (aim for >30%)
- LinkedIn notifications
- Account health

**Stop if:**
- Receiving warnings
- Low acceptance (<20%)
- Unusually slow profile loading

---

## Support & Safety

### If Account Restricted

1. **Stop all automation immediately**
2. Review LinkedIn's Terms of Service
3. Appeal if necessary (be honest)
4. Wait for restriction to lift
5. Consider manual connecting instead

### Disclaimer

- This tool is provided for educational purposes
- Authors not responsible for account actions
- LinkedIn automation violates TOS
- Use at your own risk
- No warranty or guarantee

---

## Future Enhancements

Possible additions (not implemented per user request):

- ✗ Personalized messages
- ✗ Profile randomization
- ✗ Retry logic
- ✗ Email/Slack notifications
- ✗ Advanced scheduling
- ✗ Multiple account support

Current implementation follows user specifications:
- ✓ Fixed 20/day limit
- ✓ No messages/notes
- ✓ Sequential processing
- ✓ No retries
- ✓ No notifications

---

## License

Same as parent project (linkedin_scraper).

**Again: Use at your own risk. This violates LinkedIn TOS.**
