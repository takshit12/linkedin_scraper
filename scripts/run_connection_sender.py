#!/usr/bin/env python3
"""
LinkedIn Connection Request Sender

Reads scraped job data and sends connection requests to job posters.

WARNING: This violates LinkedIn's Terms of Service. Use at your own risk.

Usage:
    cd /Users/takshitmathur/Desktop/Projects/linkedin_scraper
    source venv/bin/activate
    python3 scripts/run_connection_sender.py
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linkedin_scraper import actions
from selenium import webdriver
from datetime import datetime
import time

from connection_automation.data_loader import load_and_prepare_data, get_profile_summary
from connection_automation.tracker import ConnectionTracker
from connection_automation.safety_manager import SafetyManager
from connection_automation.connection_sender import ConnectionSender
from connection_automation import config
from connection_automation.utils import random_sleep, format_duration


def main():
    """Main function to send connection requests"""

    print("=" * 80)
    print("LinkedIn Connection Request Sender")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This automation violates LinkedIn's Terms of Service")
    print("⚠️  Risk of account restriction or permanent ban")
    print("⚠️  Use at your own risk. Educational purposes only.")
    print()

    # Step 1: Get input file
    print("=" * 80)
    print("Step 1: Input File")
    print("=" * 80)
    print()
    print("Enter path to scraped jobs file (JSON or CSV)")
    print(f"Example: data/input/linkedin_jobs_search_20251112_183212.json")
    print()

    input_file = input("File path: ").strip()

    if not input_file:
        print("❌ No file provided. Exiting.")
        return

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    # Step 2: Daily limit configuration
    print()
    print("=" * 80)
    print("Step 2: Daily Limit")
    print("=" * 80)
    print()
    print(f"Enter daily limit (default: {config.DAILY_LIMIT})")
    print("Recommended: Start with 10, gradually increase to 20")
    print()

    daily_limit_input = input(f"Daily limit: ").strip()

    if daily_limit_input:
        try:
            daily_limit = int(daily_limit_input)
        except ValueError:
            daily_limit = config.DAILY_LIMIT
            print(f"⚠️  Invalid input, using default: {daily_limit}")
    else:
        daily_limit = config.DAILY_LIMIT

    print(f"✓ Daily limit set to: {daily_limit}")

    # Step 3: Load data
    print()
    print("=" * 80)
    print("Step 3: Loading Data")
    print("=" * 80)
    print()

    try:
        profiles = load_and_prepare_data(input_file)
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    if not profiles:
        print("❌ No profiles with poster URLs found in file")
        return

    # Step 4: Initialize components
    print()
    print("=" * 80)
    print("Step 4: Initialization")
    print("=" * 80)
    print()

    tracker = ConnectionTracker()
    safety_manager = SafetyManager(daily_limit=daily_limit)

    # Check quota before starting
    safety_manager.print_quota_status()

    can_send, reason = safety_manager.can_send_request()
    if not can_send:
        print(f"\n❌ Cannot send requests: {reason}")
        print(f"\n💡 Suggestion: {safety_manager.suggest_next_run_time()}")
        return

    # Filter out already contacted profiles
    profiles_to_contact = []
    for profile in profiles:
        profile_id = profile.get('poster_profile_id')
        if profile_id and not tracker.already_contacted(profile_id):
            profiles_to_contact.append(profile)

    print(f"\n✓ Found {len(profiles_to_contact)} profiles to contact")
    print(f"  (Skipped {len(profiles) - len(profiles_to_contact)} already contacted)")

    if not profiles_to_contact:
        print("\n✓ All profiles already contacted!")
        return

    # Step 5: Login to LinkedIn
    print()
    print("=" * 80)
    print("Step 5: LinkedIn Login")
    print("=" * 80)
    print()

    # Load credentials from environment variables
    EMAIL = os.getenv("LINKEDIN_EMAIL")
    PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    if not EMAIL or not PASSWORD:
        print("\n❌ Error: LinkedIn credentials not found!")
        print("Please create a .env file with your credentials:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        return

    print("🌐 Starting Chrome browser...")
    driver = webdriver.Chrome()

    print("🔐 Logging into LinkedIn...")
    try:
        actions.login(driver, EMAIL, PASSWORD)
        print("✅ Login successful!")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.quit()
        return

    # Step 6: Send connection requests
    print()
    print("=" * 80)
    print("Step 6: Sending Connection Requests")
    print("=" * 80)
    print()

    connection_sender = ConnectionSender(driver)

    sent_count = 0
    already_connected_count = 0
    failed_count = 0

    start_time = datetime.now()

    # Calculate how many we can send today
    quota_status = safety_manager.get_quota_status()
    max_to_send = min(len(profiles_to_contact), quota_status['daily_remaining'])

    print(f"Will attempt to send {max_to_send} connection requests")
    print(f"(Daily quota: {quota_status['daily_remaining']} remaining)")
    print()

    for i, profile in enumerate(profiles_to_contact[:max_to_send], 1):
        profile_id = profile.get('poster_profile_id')
        profile_url = profile.get('poster_profile_url')
        poster_name = profile.get('poster_name', 'Unknown')
        job_title = profile.get('job_title', 'Unknown')
        company = profile.get('company', 'Unknown')

        summary = get_profile_summary(profile)

        print(f"[{i}/{max_to_send}] {summary}")

        # Check quota before each request
        can_send, reason = safety_manager.can_send_request()
        if not can_send:
            print(f"   ⚠️  {reason}")
            break

        # Navigate to profile
        print(f"   📍 Navigating to profile...")
        if not connection_sender.navigate_to_profile(profile_url):
            print(f"   ❌ Failed to navigate")
            tracker.mark_as_sent(profile_id, profile_url, 'failed', poster_name, job_title, company, "Navigation failed")
            failed_count += 1
            continue

        # Check if already connected
        if connection_sender.is_already_connected():
            print(f"   ⚠️  Already connected or pending")
            tracker.mark_as_sent(profile_id, profile_url, 'already_connected', poster_name, job_title, company)
            already_connected_count += 1
            random_sleep(config.MIN_DELAY_BETWEEN_ACTIONS, config.MAX_DELAY_BETWEEN_ACTIONS)
            continue

        # Send connection request
        print(f"   🤝 Sending connection request...")
        success, message = connection_sender.send_connection_with_verification()

        if success:
            print(f"   ✅ {message}")
            tracker.mark_as_sent(profile_id, profile_url, 'success', poster_name, job_title, company)
            sent_count += 1

            # Delay between requests
            delay = random_sleep(config.MIN_DELAY_BETWEEN_REQUESTS, config.MAX_DELAY_BETWEEN_REQUESTS)
            print(f"   ⏸️  Waiting...")

            # Take a break every N requests
            if sent_count % config.PAUSE_EVERY_N == 0 and i < max_to_send:
                break_duration = random_sleep(config.BREAK_DURATION_MIN, config.BREAK_DURATION_MAX)
                print(f"\n   ☕ Taking a break...")
        else:
            print(f"   ❌ {message}")
            tracker.mark_as_sent(profile_id, profile_url, 'failed', poster_name, job_title, company, message)
            failed_count += 1
            random_sleep(config.MIN_DELAY_BETWEEN_ACTIONS, config.MAX_DELAY_BETWEEN_ACTIONS)

    # Step 7: Summary and Export
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"📊 Results:")
    print(f"   Attempted: {sent_count + already_connected_count + failed_count}")
    print(f"   Successfully sent: {sent_count}")
    print(f"   Already connected: {already_connected_count}")
    print(f"   Failed: {failed_count}")
    print()
    print(f"⏱️  Duration: {format_duration(duration)}")
    print()

    # Print updated quota status
    safety_manager.print_quota_status()

    # Export to CSV
    print()
    print("=" * 80)
    print("Exporting Results")
    print("=" * 80)
    print()

    tracker.export_to_csv(config.CSV_OUTPUT)

    print()
    print("=" * 80)
    print("✨ Complete!")
    print("=" * 80)
    print()

    input("Press Enter to close browser...")
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
