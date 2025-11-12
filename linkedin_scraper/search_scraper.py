"""
LinkedIn Search Results Scraper - Scrapes all jobs from a search results page
"""
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .objects import Scraper
import time
import re


class SearchResultsScraper(Scraper):
    """
    Scrapes all job listings from a LinkedIn search results page.

    Usage:
        scraper = SearchResultsScraper(
            search_url="https://www.linkedin.com/jobs/search-results/...",
            driver=driver
        )

        job_urls = scraper.get_all_job_urls()
    """

    def __init__(
        self,
        search_url=None,
        driver=None,
        max_jobs=None,
        scroll_pause=2,
    ):
        super().__init__()
        self.search_url = search_url
        self.driver = driver
        self.max_jobs = max_jobs
        self.scroll_pause = scroll_pause
        self.job_urls = []

    def get_all_job_urls(self):
        """
        Extract all job URLs from the search results page.

        Returns:
            list: List of job URLs found on the page
        """
        if not self.search_url:
            raise ValueError("search_url is required")

        if not self.driver:
            raise ValueError("driver is required")

        print(f"\n🔍 Loading search results: {self.search_url}")
        self.driver.get(self.search_url)
        time.sleep(3)  # Wait for initial load

        # Scroll to load all job cards
        self._scroll_to_load_jobs()

        # Extract job URLs
        self._extract_job_urls()

        print(f"✅ Found {len(self.job_urls)} job listings")
        return self.job_urls

    def _scroll_to_load_jobs(self):
        """Scroll down the page to load all job listings"""
        print("📜 Scrolling to load all jobs...")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        jobs_loaded = 0

        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.scroll_pause)

            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Count current jobs
            try:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id], li.jobs-search-results__list-item")
                current_count = len(job_cards)

                if current_count > jobs_loaded:
                    jobs_loaded = current_count
                    print(f"  Loaded {jobs_loaded} jobs so far...")

                # Stop if max_jobs reached
                if self.max_jobs and jobs_loaded >= self.max_jobs:
                    print(f"  Reached max_jobs limit ({self.max_jobs})")
                    break

            except:
                pass

            # Break if no new content loaded
            if new_height == last_height:
                break

            last_height = new_height

        print(f"✅ Finished scrolling. Total job cards visible: {jobs_loaded}")

    def _extract_job_urls(self):
        """Extract job URLs from loaded job cards"""
        print("🔗 Extracting job URLs...")

        # Try multiple selectors for job cards
        job_card_selectors = [
            "li[data-occludable-job-id]",
            "li.jobs-search-results__list-item",
            "div.job-card-container",
            "div.jobs-search__job-card-wrapper",
        ]

        job_cards = []
        for selector in job_card_selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    job_cards = cards
                    print(f"  Found {len(cards)} job cards using selector: {selector}")
                    break
            except:
                continue

        if not job_cards:
            print("⚠️  No job cards found on page")
            return

        # Extract URLs from job cards
        for card in job_cards:
            try:
                # Try to find job link
                link_selectors = [
                    "a.job-card-list__title",
                    "a.job-card-container__link",
                    "a[href*='/jobs/view/']",
                    "a.job-card__link",
                ]

                job_link = None
                for link_selector in link_selectors:
                    try:
                        link = card.find_element(By.CSS_SELECTOR, link_selector)
                        if link:
                            job_link = link
                            break
                    except:
                        continue

                if job_link:
                    href = job_link.get_attribute("href")
                    if href and "/jobs/view/" in href:
                        # Clean URL (remove tracking params)
                        clean_url = href.split("?")[0]
                        if clean_url not in self.job_urls:
                            self.job_urls.append(clean_url)

                            # Stop if max_jobs reached
                            if self.max_jobs and len(self.job_urls) >= self.max_jobs:
                                print(f"  Reached max_jobs limit ({self.max_jobs})")
                                return

            except Exception as e:
                continue

        print(f"  Extracted {len(self.job_urls)} unique job URLs")


class JobScraperRobust(Scraper):
    """
    More robust job scraper that handles modern LinkedIn pages.
    Uses multiple selector strategies and better error handling.
    """

    def __init__(
        self,
        linkedin_url=None,
        driver=None,
        close_on_complete=True,
    ):
        super().__init__()
        self.linkedin_url = linkedin_url
        self.driver = driver

        # Job data fields
        self.job_title = None
        self.company = None
        self.company_linkedin_url = None
        self.location = None
        self.posted_date = None
        self.applicant_count = None
        self.job_description = None
        self.benefits = None

        # Poster data fields
        self.poster_name = None
        self.poster_headline = None
        self.poster_profile_url = None
        self.poster_profile_id = None

        if self.linkedin_url and self.driver:
            self.scrape(close_on_complete)

    def scrape(self, close_on_complete=True):
        """Scrape job with robust selector handling"""
        try:
            print(f"\n🔍 Scraping: {self.linkedin_url}")

            self.driver.get(self.linkedin_url)
            time.sleep(2)

            # Extract basic job info
            self._extract_job_info()

            # Extract poster info
            self._extract_poster_info()

            print(f"✅ Scraped: {self.job_title} at {self.company}")
            if self.poster_name:
                print(f"   Posted by: {self.poster_name} (ID: {self.poster_profile_id})")

            if close_on_complete:
                # Don't close, just switch to another tab or minimize
                pass

        except Exception as e:
            print(f"❌ Error scraping {self.linkedin_url}: {e}")
            raise

    def _extract_job_info(self):
        """Extract job information with multiple selector strategies"""

        # Job Title - try multiple selectors
        title_selectors = [
            (By.CSS_SELECTOR, "h1.job-details-jobs-unified-top-card__job-title"),
            (By.CSS_SELECTOR, "h1.t-24"),
            (By.CSS_SELECTOR, "h1.jobs-unified-top-card__job-title"),
            (By.XPATH, "//h1[contains(@class, 'job-title')]"),
            (By.CSS_SELECTOR, "h1[class*='job-title']"),
        ]
        self.job_title = self._try_extract_text(title_selectors, "Job Title")

        # Company
        company_selectors = [
            (By.CSS_SELECTOR, "a.job-details-jobs-unified-top-card__company-name"),
            (By.CSS_SELECTOR, "a.jobs-unified-top-card__company-name"),
            (By.CSS_SELECTOR, "a[href*='/company/']"),
            (By.XPATH, "//a[contains(@href, '/company/')]"),
        ]
        company_elem = self._try_extract_element(company_selectors, "Company")
        if company_elem:
            self.company = company_elem.text.strip()
            self.company_linkedin_url = company_elem.get_attribute("href")

        # Location
        location_selectors = [
            (By.CSS_SELECTOR, "span.job-details-jobs-unified-top-card__bullet"),
            (By.CSS_SELECTOR, "span.jobs-unified-top-card__bullet"),
            (By.XPATH, "//span[contains(@class, 'bullet')]"),
        ]
        self.location = self._try_extract_text(location_selectors, "Location")

        # Job Description
        desc_selectors = [
            (By.CSS_SELECTOR, "div.jobs-description__content"),
            (By.CSS_SELECTOR, "div.jobs-description"),
            (By.CSS_SELECTOR, "div[class*='description']"),
        ]

        # Try to click "Show more" button first
        try:
            show_more = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Show more']")
            show_more.click()
            time.sleep(0.5)
        except:
            pass

        self.job_description = self._try_extract_text(desc_selectors, "Job Description")

        print(f"   ✓ Extracted job info")

    def _extract_poster_info(self):
        """Extract job poster information"""
        try:
            # Find poster section
            poster_selectors = [
                (By.CSS_SELECTOR, "div.jobs-poster"),
                (By.CSS_SELECTOR, "section.jobs-poster"),
                (By.CSS_SELECTOR, "div[class*='poster']"),
                (By.XPATH, "//div[contains(@class, 'hiring-team')]"),
            ]

            poster_section = self._try_extract_element(poster_selectors, "Poster Section")

            if poster_section:
                # Find profile link
                try:
                    links = poster_section.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "/in/" in href:
                            self.poster_profile_url = href.split("?")[0]
                            self.poster_name = link.text.strip()

                            # Extract profile ID from URL
                            match = re.search(r'/in/([^/?]+)', self.poster_profile_url)
                            if match:
                                self.poster_profile_id = match.group(1)
                            break
                except:
                    pass

                # Find headline if we have poster
                if self.poster_name:
                    headline_selectors = [
                        (By.CSS_SELECTOR, "span.jobs-poster__job-title"),
                        (By.CSS_SELECTOR, "span[class*='subtitle']"),
                    ]
                    self.poster_headline = self._try_extract_text(headline_selectors, "Poster Headline", base=poster_section)

                    print(f"   ✓ Extracted poster info")

        except Exception as e:
            print(f"   ⚠️  Could not extract poster info: {e}")

    def _try_extract_text(self, selectors, field_name, base=None):
        """Try multiple selectors and return text"""
        base = base or self.driver
        for by, selector in selectors:
            try:
                elem = base.find_element(by, selector)
                if elem and elem.text.strip():
                    return elem.text.strip()
            except:
                continue
        print(f"   ⚠️  Could not find: {field_name}")
        return None

    def _try_extract_element(self, selectors, field_name):
        """Try multiple selectors and return element"""
        for by, selector in selectors:
            try:
                elem = self.driver.find_element(by, selector)
                if elem:
                    return elem
            except:
                continue
        return None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "linkedin_url": self.linkedin_url,
            "job_title": self.job_title,
            "company": self.company,
            "company_linkedin_url": self.company_linkedin_url,
            "location": self.location,
            "posted_date": self.posted_date,
            "applicant_count": self.applicant_count,
            "job_description": self.job_description,
            "benefits": self.benefits,
            "poster_name": self.poster_name,
            "poster_headline": self.poster_headline,
            "poster_profile_url": self.poster_profile_url,
            "poster_profile_id": self.poster_profile_id,
        }
