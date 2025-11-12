# Setup Guide - LinkedIn Scraper

Complete guide to install and run the LinkedIn scraper from scratch.

---

## Prerequisites

### 1. Python 3.7+

Check your Python version:
```bash
python3 --version
# Should show: Python 3.7.0 or higher
```

If not installed, download from [python.org](https://www.python.org/downloads/)

### 2. Chrome Browser

Download from [google.com/chrome](https://www.google.com/chrome/)

### 3. ChromeDriver

**Option A: Automatic (Recommended)**
ChromeDriver will be downloaded automatically by Selenium 4.x

**Option B: Manual**
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver: [chromedriver.chromium.org](https://chromedriver.chromium.org/)
3. Extract and move to `/usr/local/bin/` (Mac/Linux) or add to PATH (Windows)

---

## Installation Steps

### Step 1: Clone/Download Repository

```bash
cd ~/Desktop/Projects
# If you have the folder already, skip to Step 2
```

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
cd linkedin_scraper
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
cd linkedin_scraper
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip3 install -r requirements.txt
```

**Expected output:**
```
Successfully installed selenium-4.18.1 requests-2.32.5 lxml-5.3.0
```

### Step 4: Verify Installation

```bash
python3 -c "import selenium; import requests; import lxml; print('✓ All packages installed')"
```

Should print: `✓ All packages installed`

---

## Quick Test

### Test 1: Basic Scraper Test

```bash
python3 -c "from linkedin_scraper import actions; print('✓ LinkedIn scraper imported successfully')"
```

### Test 2: Selenium Test

```bash
python3 -c "from selenium import webdriver; driver = webdriver.Chrome(); driver.quit(); print('✓ Chrome driver working')"
```

If you see `✓ Chrome driver working`, you're ready!

---

## Running the Job Scraper

### First Run

```bash
python3 scrape_search_results.py
```

**Prompts:**
```
LinkedIn Search URL: [press Enter for default or paste your URL]
Max jobs: 50
Max pages: [press Enter for all pages]
```

**Output:**
- `linkedin_jobs_search_YYYYMMDD_HHMMSS.json`
- `linkedin_jobs_search_YYYYMMDD_HHMMSS.csv`

### Expected Behavior

1. Chrome browser opens
2. Navigates to LinkedIn login
3. Logs in automatically
4. Loads search results
5. Scrolls and collects job URLs (with pagination)
6. Scrapes each job (title, company, poster, description)
7. Saves to JSON and CSV
8. Browser stays open until you press Enter

**Time estimate:**
- 50 jobs ≈ 5-10 minutes (depending on pages)

---

## Running Connection Automation

### Prerequisites

Must have scraped jobs first:
```bash
# Move scraped file to input folder
mv linkedin_jobs_search_*.json data/input/
```

### Test Mode (Recommended First)

```bash
python3 scripts/dry_run.py
```

**What it does:**
- Tests 10 profiles
- Checks if Connect buttons found
- **NO requests sent** (safe)

### Production Mode

```bash
python3 scripts/run_connection_sender.py
```

**Prompts:**
```
File path: data/input/linkedin_jobs_search_20251112_183212.json
Daily limit: 20
```

**⚠️ WARNING:** This sends REAL connection requests and violates LinkedIn TOS!

---

## Troubleshooting

### Issue: "chromedriver not found"

**Solution:**
```bash
# macOS/Linux
which chromedriver

# If not found, Selenium 4.x will auto-download
# Or manually install:
brew install chromedriver  # macOS with Homebrew
```

### Issue: "selenium not found"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall
pip3 install -r requirements.txt
```

### Issue: "Chrome version mismatch"

**Error:**
```
selenium.common.exceptions.SessionNotCreatedException:
Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

**Solution:**
```bash
# Update Chrome browser to latest version
# Then restart the script - Selenium will download matching driver
```

### Issue: "No module named 'linkedin_scraper'"

**Solution:**
```bash
# Make sure you're in the correct directory
cd /Users/takshitmathur/Desktop/Projects/linkedin_scraper

# Verify folder structure
ls linkedin_scraper/
# Should show: __init__.py, actions.py, etc.
```

### Issue: Login fails / CAPTCHA

**Solutions:**
1. **Manual login:** Let script open browser, login manually, then press Enter
2. **Cookie auth:** Use cookie-based login (see README.md)
3. **Account issue:** Check if LinkedIn flagged your account

### Issue: "Permission denied" running scripts

**Solution:**
```bash
chmod +x scripts/*.py
```

---

## Package Versions

**Confirmed working versions:**

| Package | Version | Required |
|---------|---------|----------|
| Python | 3.7+ | Yes |
| selenium | 4.18.1 | Yes |
| requests | 2.32.5 | Yes |
| lxml | 5.3.0 | Yes |
| Chrome | Latest | Yes |

---

## Fresh Install Checklist

- [ ] Python 3.7+ installed
- [ ] Chrome browser installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Test import successful
- [ ] Chrome driver working
- [ ] LinkedIn credentials ready
- [ ] Read warnings about TOS violations

---

## Environment Variables (Optional)

### Set ChromeDriver Path (if needed)

**macOS/Linux:**
```bash
export CHROMEDRIVER=/path/to/chromedriver
```

**Windows:**
```cmd
set CHROMEDRIVER=C:\path\to\chromedriver.exe
```

### Set LinkedIn Credentials (Optional)

**Not recommended** - credentials are hardcoded in scripts for convenience.

---

## Complete Installation Script

**macOS/Linux:**
```bash
#!/bin/bash
# Run this script to set up from scratch

# Navigate to project
cd ~/Desktop/Projects/linkedin_scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Test installation
python3 -c "import selenium; import requests; import lxml; print('✓ Installation complete!')"

echo ""
echo "Setup complete! Run the scraper:"
echo "  python3 scrape_search_results.py"
```

**Save as `setup.sh` and run:**
```bash
chmod +x setup.sh
./setup.sh
```

---

## Next Steps

1. ✅ **Run job scraper:** `python3 scrape_search_results.py`
2. ✅ **Verify output:** Check JSON/CSV files created
3. ✅ **Test connections:** `python3 scripts/dry_run.py`
4. ✅ **Read docs:** `README_CONNECTIONS.md` for safety info

---

## Uninstallation

To remove everything:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Remove data files (optional)
rm -rf data/output/*
rm -f linkedin_jobs_*.json
rm -f linkedin_jobs_*.csv
```

---

## Support

**Common Issues:**
- Chrome version mismatch → Update Chrome
- Module not found → Check virtual environment activated
- Login fails → Try manual login or check account status
- No jobs found → Verify search URL has results

**LinkedIn Account Safety:**
- Start with low limits (5-10 requests/day)
- Monitor for warnings
- Read `README_CONNECTIONS.md` carefully
- This violates LinkedIn TOS - use at own risk

---

## Summary

**Minimum commands to get started:**

```bash
cd ~/Desktop/Projects/linkedin_scraper
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 scrape_search_results.py
```

That's it! 🎉
