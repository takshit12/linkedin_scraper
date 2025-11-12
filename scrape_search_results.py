#!/usr/bin/env python3
"""
Scrape all jobs from a LinkedIn search results page with MULTI-PAGE PAGINATION

Usage:
    source venv/bin/activate
    python3 scrape_search_results.py

This will:
1. Login to LinkedIn
2. Go to the search results page
3. Loop through ALL pages (clicking "Next" button)
4. Scroll and load all job cards on each page
5. Extract all job URLs across all pages
6. Scrape each job (with poster info)
7. Save all results to JSON and CSV
"""
from linkedin_scraper import SearchResultsScraper, JobScraperV2, actions
from selenium import webdriver
import json
import csv
from datetime import datetime
import time


def scrape_all_jobs_from_search():
    """Main function to scrape all jobs from search results"""

    print("=" * 80)
    print("LinkedIn Search Results Scraper - Multi-Page with Poster Extraction")
    print("=" * 80)

    # Prompt for search URL
    print("\n📋 LinkedIn Search URL")
    print("=" * 80)
    print("Paste your LinkedIn search URL (with all filters applied)")
    print("Or press Enter to use default example URL")
    print()

    DEFAULT_SEARCH_URL = "https://www.linkedin.com/jobs/search-results/?distance=25&geoId=103644278&keywords=ai%20agent%20developer%20posted%20in%20the%20past%2024%20hours&origin=SEMANTIC_SEARCH_HISTORY"

    user_url = input("URL: ").strip()

    if user_url:
        SEARCH_URL = user_url
        print(f"✓ Using your URL: {SEARCH_URL[:80]}...")
    else:
        SEARCH_URL = DEFAULT_SEARCH_URL
        print(f"✓ Using default URL: {SEARCH_URL[:80]}...")

    # Prompt for MAX_JOBS
    print("\n📊 Maximum Jobs to Scrape")
    print("=" * 80)
    print("Enter max number of jobs to scrape (e.g., 50, 100, 200)")
    print("Or press Enter for default: 50")
    print()

    user_max_jobs = input("Max jobs: ").strip()

    if user_max_jobs:
        try:
            MAX_JOBS = int(user_max_jobs)
            print(f"✓ Will scrape up to {MAX_JOBS} jobs")
        except ValueError:
            MAX_JOBS = 50
            print(f"⚠️  Invalid input, using default: 50 jobs")
    else:
        MAX_JOBS = 50
        print(f"✓ Using default: 50 jobs")

    # Prompt for MAX_PAGES
    print("\n📄 Maximum Pages to Scrape")
    print("=" * 80)
    print("Enter max number of pages to scrape (e.g., 2, 5, 10)")
    print("Or press Enter to scrape ALL pages until no Next button")
    print()

    user_max_pages = input("Max pages: ").strip()

    if user_max_pages:
        try:
            MAX_PAGES = int(user_max_pages)
            print(f"✓ Will scrape up to {MAX_PAGES} pages")
        except ValueError:
            MAX_PAGES = None
            print(f"⚠️  Invalid input, using default: ALL pages")
    else:
        MAX_PAGES = None
        print(f"✓ Using default: ALL pages (until Next button disabled)")

    # Configuration
    EMAIL = "takshitmathur786@gmail.com"
    PASSWORD = "Invincible7@1201"
    SCROLL_PAUSE = 2  # Seconds to wait between scrolls

    print(f"\n📋 Configuration:")
    print(f"   Search URL: {SEARCH_URL}")
    print(f"   Max jobs to scrape: {MAX_JOBS if MAX_JOBS else 'Unlimited'}")
    print(f"   Max pages to scrape: {MAX_PAGES if MAX_PAGES else 'All pages until Next button disabled'}")
    print(f"   Email: {EMAIL}")

    try:
        # Step 1: Setup browser and login
        print("\n" + "=" * 80)
        print("STEP 1: Browser Setup & Login")
        print("=" * 80)

        print("🌐 Starting Chrome browser...")
        driver = webdriver.Chrome()

        print("🔐 Logging into LinkedIn...")
        actions.login(driver, EMAIL, PASSWORD)
        print("✅ Login successful!")

        time.sleep(2)

        # Step 2: Extract job URLs from search results (WITH PAGINATION!)
        print("\n" + "=" * 80)
        print("STEP 2: Extract Job URLs from Search Results (Multi-Page)")
        print("=" * 80)

        search_scraper = SearchResultsScraper(
            search_url=SEARCH_URL,
            driver=driver,
            max_jobs=MAX_JOBS,
            max_pages=MAX_PAGES,  # NEW: Pagination support!
            scroll_pause=SCROLL_PAUSE
        )

        job_urls = search_scraper.get_all_job_urls()

        if not job_urls:
            print("\n❌ No job URLs found!")
            driver.quit()
            return

        print(f"\n✅ Found {len(job_urls)} job URLs to scrape")
        print("\nFirst 5 URLs:")
        for i, url in enumerate(job_urls[:5], 1):
            print(f"   {i}. {url}")

        # Step 3: Scrape each job
        print("\n" + "=" * 80)
        print(f"STEP 3: Scraping {len(job_urls)} Jobs")
        print("=" * 80)

        all_jobs = []
        successful = 0
        failed = 0

        for i, job_url in enumerate(job_urls, 1):
            print(f"\n[{i}/{len(job_urls)}] Scraping job...")

            try:
                job_scraper = JobScraperV2(
                    linkedin_url=job_url,
                    driver=driver,
                    close_on_complete=False
                )

                job_data = job_scraper.to_dict()
                all_jobs.append(job_data)
                successful += 1

                # Small delay to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
                # Continue to next job
                continue

        # Step 4: Save results
        print("\n" + "=" * 80)
        print("STEP 4: Saving Results")
        print("=" * 80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"linkedin_jobs_search_{timestamp}.json"
        csv_output_file = f"linkedin_jobs_search_{timestamp}.csv"

        # Save as JSON
        with open(output_file, "w") as f:
            json.dump(all_jobs, f, indent=2, ensure_ascii=False)

        # Save as CSV
        with open(csv_output_file, "w", newline="", encoding="utf-8") as f:
            if all_jobs:
                # Define CSV columns (matches to_dict() field order)
                fieldnames = [
                    "linkedin_url",
                    "job_title",
                    "company",
                    "company_linkedin_url",
                    "location",
                    "posted_date",
                    "applicant_count",
                    "job_description",
                    "benefits",
                    "poster_name",
                    "poster_headline",
                    "poster_profile_url",
                    "poster_profile_id"
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_jobs)

        print(f"\n💾 Results saved to:")
        print(f"   JSON: {output_file}")
        print(f"   CSV:  {csv_output_file}")

        # Step 5: Summary
        print("\n" + "=" * 80)
        print("SCRAPING SUMMARY")
        print("=" * 80)

        print(f"\n📊 Statistics:")
        print(f"   Total jobs found: {len(job_urls)}")
        print(f"   Successfully scraped: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success rate: {(successful/len(job_urls)*100):.1f}%")

        # Show jobs with poster info
        jobs_with_poster = [j for j in all_jobs if j.get('poster_profile_id')]
        print(f"\n👤 Jobs with poster info: {len(jobs_with_poster)}/{successful}")

        if jobs_with_poster:
            print("\n📋 Sample jobs with poster:")
            for job in jobs_with_poster[:3]:
                print(f"   • {job['job_title']} at {job['company']}")
                print(f"     Posted by: {job['poster_name']} (ID: {job['poster_profile_id']})")

        print("\n" + "=" * 80)
        print("✨ Scraping Complete!")
        print("=" * 80)

        input("\n⏸️  Press Enter to close the browser...")
        driver.quit()

        return all_jobs

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
        try:
            driver.quit()
        except:
            pass
        return None

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

        try:
            input("\n⏸️  Press Enter to close the browser...")
            driver.quit()
        except:
            pass

        return None


if __name__ == "__main__":
    import sys

    result = scrape_all_jobs_from_search()
    sys.exit(0 if result else 1)
