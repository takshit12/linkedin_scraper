#!/usr/bin/env python3
"""
Dry Run - Test connection automation WITHOUT sending actual requests

This script tests the automation by:
1. Loading job data
2. Navigating to profiles
3. Finding Connect buttons
4. Reporting findings
5. NO ACTUAL CLICKING - Safe for testing

Usage:
    cd /Users/takshitmathur/Desktop/Projects/linkedin_scraper
    source venv/bin/activate
    python3 scripts/dry_run.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linkedin_scraper import actions
from selenium import webdriver
import time

from connection_automation.data_loader import load_and_prepare_data, get_profile_summary
from connection_automation.connection_sender import ConnectionSender
from connection_automation.utils import random_sleep


def main():
    """Main dry-run function"""

    print("=" * 80)
    print("Connection Automation - DRY RUN (Test Mode)")
    print("=" * 80)
    print()
    print("✓ Safe mode: NO connection requests will be sent")
    print("✓ Will only navigate and check for Connect buttons")
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

    # Step 2: How many to test
    print()
    print("=" * 80)
    print("Step 2: Test Count")
    print("=" * 80)
    print()
    print("How many profiles to test? (default: 10)")
    print()

    test_count_input = input("Test count: ").strip()

    if test_count_input:
        try:
            test_count = int(test_count_input)
        except ValueError:
            test_count = 10
            print(f"⚠️  Invalid input, using default: 10")
    else:
        test_count = 10

    print(f"✓ Will test {test_count} profiles")

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

    profiles_to_test = profiles[:test_count]
    print(f"\n✓ Selected {len(profiles_to_test)} profiles for testing")

    # Step 4: Login to LinkedIn
    print()
    print("=" * 80)
    print("Step 4: LinkedIn Login")
    print("=" * 80)
    print()

    EMAIL = "takshitmathur786@gmail.com"
    PASSWORD = "Invincible7@1201"

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

    # Step 5: Test profiles
    print()
    print("=" * 80)
    print("Step 5: Testing Profiles (DRY RUN - No Clicking)")
    print("=" * 80)
    print()

    connection_sender = ConnectionSender(driver)

    results = {
        'connect_found': 0,
        'already_connected': 0,
        'connect_not_found': 0,
        'navigation_failed': 0
    }

    for i, profile in enumerate(profiles_to_test, 1):
        profile_url = profile.get('poster_profile_url')
        summary = get_profile_summary(profile)

        print(f"[{i}/{len(profiles_to_test)}] {summary}")
        print(f"   URL: {profile_url}")

        # Navigate to profile
        print(f"   📍 Navigating...")
        if not connection_sender.navigate_to_profile(profile_url):
            print(f"   ❌ Navigation failed")
            results['navigation_failed'] += 1
            continue

        # Check if already connected
        if connection_sender.is_already_connected():
            print(f"   ⚠️  Already connected or pending")
            results['already_connected'] += 1
        else:
            # Try to find Connect button (but don't click!)
            connect_button = connection_sender.find_connect_button()

            if connect_button:
                print(f"   ✅ Connect button found (would send request)")
                results['connect_found'] += 1
            else:
                print(f"   ❌ Connect button not found")
                results['connect_not_found'] += 1

        # Small delay between profiles
        random_sleep(2, 3)
        print()

    # Step 6: Summary
    print("=" * 80)
    print("Dry Run Summary")
    print("=" * 80)
    print()
    print(f"📊 Results:")
    print(f"   Tested: {len(profiles_to_test)}")
    print(f"   Connect button found: {results['connect_found']}")
    print(f"   Already connected: {results['already_connected']}")
    print(f"   Connect button not found: {results['connect_not_found']}")
    print(f"   Navigation failed: {results['navigation_failed']}")
    print()

    if results['connect_found'] > 0:
        success_rate = (results['connect_found'] / len(profiles_to_test)) * 100
        print(f"✓ Success rate: {success_rate:.1f}%")
        print(f"✓ Ready to run production script with {results['connect_found']} profiles")
    else:
        print(f"⚠️  No Connect buttons found - check profile URLs or LinkedIn account status")

    print()
    print("=" * 80)
    print("✨ Dry Run Complete - No requests were sent")
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
