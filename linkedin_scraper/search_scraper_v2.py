"""
LinkedIn Search Results Scraper V2 - Works with LinkedIn's obfuscated class names

Key insight: LinkedIn uses randomized class names, so we use:
- XPath queries to find elements by structure and text
- Tag names and relationships
- Page title parsing
- Visible text matching
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
    """

    def __init__(
        self,
        search_url=None,
        driver=None,
        max_jobs=None,
        max_pages=None,
        scroll_pause=2,
    ):
        super().__init__()
        self.search_url = search_url
        self.driver = driver
        self.max_jobs = max_jobs
        self.max_pages = max_pages
        self.scroll_pause = scroll_pause
        self.job_urls = []

    def get_all_job_urls(self):
        """
        Extract all job URLs from the search results page with pagination.
        Loops through all pages by clicking the Next button.
        """
        if not self.search_url:
            raise ValueError("search_url is required")

        if not self.driver:
            raise ValueError("driver is required")

        print(f"\n🔍 Loading search results: {self.search_url}")
        self.driver.get(self.search_url)
        time.sleep(3)

        page = 1

        # Pagination loop
        while True:
            print(f"\n📄 Page {page}:")

            # Scroll to load all job cards on CURRENT page
            self._scroll_to_load_jobs_on_current_page()

            # Extract job URLs from CURRENT page
            page_jobs_before = len(self.job_urls)
            self._extract_job_urls_from_current_page()
            page_jobs_count = len(self.job_urls) - page_jobs_before

            print(f"   Found {page_jobs_count} jobs on this page | Total collected: {len(self.job_urls)}")

            # Check if we've reached max_jobs limit
            if self.max_jobs and len(self.job_urls) >= self.max_jobs:
                print(f"   Reached max_jobs limit ({self.max_jobs})")
                self.job_urls = self.job_urls[:self.max_jobs]
                break

            # Check if we've reached max_pages limit
            if self.max_pages and page >= self.max_pages:
                print(f"   Reached max_pages limit ({self.max_pages})")
                break

            # Try to click Next button to go to next page
            if self._click_next_button():
                print(f"   ✓ Clicked Next button, loading page {page + 1}...")
                time.sleep(3)  # Wait for new page to load
                page += 1
            else:
                print(f"   ✗ No Next button found - reached last page")
                break

        print(f"\n✅ Pagination complete! Collected {len(self.job_urls)} job URLs across {page} page(s)")
        return self.job_urls

    def _scroll_to_load_jobs_on_current_page(self):
        """Scroll down the page to load all job listings on the CURRENT page"""
        print("   📜 Scrolling left sidebar...")

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
                job_cards = self.driver.find_elements(By.CSS_SELECTOR,
                    "li[data-occludable-job-id], li.jobs-search-results__list-item, li.scaffold-layout__list-item")
                current_count = len(job_cards)

                if current_count > jobs_loaded:
                    jobs_loaded = current_count
                    print(f"      Loaded {jobs_loaded} jobs so far...")

                # Stop if max_jobs reached (check total collected, not just current page)
                if self.max_jobs and len(self.job_urls) + jobs_loaded >= self.max_jobs:
                    print(f"      Approaching max_jobs limit")
                    break

            except:
                pass

            # Break if no new content loaded
            if new_height == last_height:
                break

            last_height = new_height

        print(f"      ✓ Finished scrolling current page. {jobs_loaded} job cards visible")

    def _extract_job_urls_from_current_page(self):
        """Extract job URLs from loaded job cards on the CURRENT page"""
        print("   🔗 Extracting job URLs from current page...")

        # Try multiple selectors for job cards
        # Different selectors for /search/ vs /search-results/ URLs
        job_card_selectors = [
            "li.scaffold-layout__list-item",  # NEW: Works for /search-results/ (semantic search)
            "li[data-occludable-job-id]",  # Works for /search/ URLs
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
                    print(f"      Found {len(cards)} job cards using selector: {selector}")
                    break
            except:
                continue

        if not job_cards:
            print("      ⚠️  No job cards found on page")
            return

        # Extract URLs from job cards
        for card in job_cards:
            try:
                job_id = None

                # METHOD 1: Try to get job ID from data-job-id attribute (works for semantic search)
                try:
                    job_card_wrapper = card.find_element(By.CSS_SELECTOR, "div[data-job-id]")
                    job_id = job_card_wrapper.get_attribute("data-job-id")
                except:
                    pass

                # METHOD 2: Try to extract from link href
                if not job_id:
                    link_selectors = [
                        "a[href*='/jobs/view/']",  # Traditional format
                        "a[href*='currentJobId=']",  # Semantic search format
                        "a.job-card-list__title",
                        "a.job-card-container__link",
                        "a.job-card__link",
                        "a",  # Any link as fallback
                    ]

                    for link_selector in link_selectors:
                        try:
                            link = card.find_element(By.CSS_SELECTOR, link_selector)
                            href = link.get_attribute("href")

                            if href:
                                # Extract from /jobs/view/{id}/ format
                                if "/jobs/view/" in href:
                                    job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                                    break
                                # Extract from currentJobId={id} format
                                elif "currentJobId=" in href:
                                    import re
                                    match = re.search(r'currentJobId=(\d+)', href)
                                    if match:
                                        job_id = match.group(1)
                                        break
                        except:
                            continue

                # If we found a job ID, construct clean URL
                if job_id and job_id.isdigit():
                    clean_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

                    if clean_url not in self.job_urls:
                        self.job_urls.append(clean_url)

                        # Stop if max_jobs reached
                        if self.max_jobs and len(self.job_urls) >= self.max_jobs:
                            print(f"      Reached max_jobs limit ({self.max_jobs})")
                            return

            except Exception as e:
                continue

    def _click_next_button(self):
        """
        Try to click the Next button to go to the next page.
        Returns True if successful, False if no more pages.

        Tries multiple selector strategies to handle both <button> and <a> elements.
        """
        try:
            # First, scroll down the page to make sure Next button is visible
            # The Next button is usually at the bottom of the left sidebar
            print("      Scrolling to reveal Next button...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Try to find and scroll the job results container specifically
            try:
                # Find the left sidebar container
                job_list_selectors = [
                    "div.jobs-search-results-list",
                    "div.scaffold-layout__list",
                    "ul.jobs-search-results__list",
                ]

                for selector in job_list_selectors:
                    try:
                        container = self.driver.find_element(By.CSS_SELECTOR, selector)
                        # Scroll this container to bottom to reveal pagination
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                        time.sleep(1)
                        print(f"      Scrolled job list container: {selector}")
                        break
                    except:
                        continue
            except:
                pass

            # Multiple selector strategies for Next button/link
            # LinkedIn may use <button> or <a> elements for pagination
            next_selectors = [
                '//button[@aria-label="View next page"]',  # PRIMARY: Job search pagination (confirmed working)
                '//button[@aria-label="Next"]',  # Alternative pagination
                '//span[text()="Next"]/parent::button',  # Button containing span with "Next" text
                '//button[.//text()="Next"]',  # Button with "Next" anywhere in text content
                '//button[contains(@class, "jobs-search-pagination__button--next")]',  # By class name
                '//a[@aria-label="Next"]',  # Link with aria-label
                '//a[contains(text(), "Next")]',  # Link with "Next" text
                '//div[contains(@class, "pagination")]//button',  # Any button in pagination container
            ]

            next_element = None
            used_selector = None

            # Try each selector until we find one that works
            for selector in next_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        next_element = element
                        used_selector = selector
                        print(f"      Found Next element using: {selector}")
                        break
                except NoSuchElementException:
                    continue

            if not next_element:
                print(f"      Next button/link not found (tried {len(next_selectors)} selectors)")
                return False

            # Check if element is clickable (not disabled)
            # For <a> elements, check if href exists or if it has aria-disabled
            is_clickable = False

            if next_element.tag_name == "button":
                is_clickable = next_element.is_enabled()
                if not is_clickable:
                    print(f"      Next button is disabled")
            elif next_element.tag_name == "a":
                # Check if link has aria-disabled attribute
                aria_disabled = next_element.get_attribute("aria-disabled")
                if aria_disabled == "true":
                    print(f"      Next link is disabled (aria-disabled=true)")
                    is_clickable = False
                else:
                    is_clickable = True
            else:
                # Unknown element type, try clicking anyway
                is_clickable = True

            if is_clickable:
                # Scroll element into view before clicking
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_element)
                time.sleep(0.5)
                next_element.click()
                return True
            else:
                return False

        except Exception as e:
            print(f"      Error clicking Next button: {e}")
            return False


class JobScraperV2(Scraper):
    """
    V2 scraper that works with LinkedIn's obfuscated class names.
    Uses XPath and structure-based queries instead of class names.
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
        """Scrape job with structure-based queries"""
        try:
            print(f"\n🔍 Scraping: {self.linkedin_url}")

            self.driver.get(self.linkedin_url)
            time.sleep(3)  # Wait for page to load

            # Extract basic job info
            self._extract_job_info()

            # Extract poster info
            self._extract_poster_info()

            print(f"✅ Scraped: {self.job_title} at {self.company}")
            if self.poster_name:
                print(f"   Posted by: {self.poster_name} (ID: {self.poster_profile_id})")

            if close_on_complete:
                pass  # Don't close, reuse browser

        except Exception as e:
            print(f"❌ Error scraping {self.linkedin_url}: {e}")
            raise

    def _extract_job_info(self):
        """Extract job information using structure and text patterns"""

        # 1. Parse page title first (most reliable)
        try:
            title_text = self.driver.title
            if " | " in title_text:
                parts = title_text.split(" | ")
                self.job_title = parts[0].strip() if len(parts) > 0 else None
                self.company = parts[1].strip() if len(parts) > 1 else None
                print(f"   ✓ Extracted from page title: {self.job_title} at {self.company}")
        except Exception as e:
            print(f"   ⚠️  Could not parse page title: {e}")

        # 2. Find job title in <p> tag (if not from title)
        if not self.job_title:
            try:
                # Find <p> tags with substantial text that might be job title
                p_tags = self.driver.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    text = p.text.strip()
                    # Job titles are usually short (5-50 chars) and don't contain special patterns
                    if text and 5 < len(text) < 50 and "·" not in text and "\n" not in text:
                        self.job_title = text
                        print(f"   ✓ Found job title in <p>: {self.job_title}")
                        break
            except:
                pass

        # 3. Find company from links (always try to get URL even if we have name)
        try:
            company_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/company/')]")
            for link in company_links:
                text = link.text.strip()
                href = link.get_attribute("href")
                if text and len(text) > 2:  # Company name should have substance
                    if not self.company:
                        self.company = text
                    self.company_linkedin_url = href
                    print(f"   ✓ Found company link: {self.company} - {href}")
                    break
        except:
            pass

        # 4. Find location and date (they're together in one <p> with "·" separator)
        try:
            p_tags = self.driver.find_elements(By.TAG_NAME, "p")
            for p in p_tags:
                text = p.text.strip()
                # Location/date format: "City, State, Country · X weeks ago · Y applicants"
                if "·" in text and ("ago" in text.lower() or "applicant" in text.lower()):
                    parts = text.split("·")
                    self.location = parts[0].strip() if len(parts) > 0 else None

                    # Find "ago" part for posted date
                    for part in parts:
                        if "ago" in part.lower():
                            self.posted_date = part.strip()
                        if "applicant" in part.lower():
                            self.applicant_count = part.strip()

                    print(f"   ✓ Found location: {self.location}")
                    print(f"   ✓ Posted: {self.posted_date}, {self.applicant_count}")
                    break
        except Exception as e:
            print(f"   ⚠️  Could not extract location/date: {e}")

        # 5. Find job description (large text blocks in <p> and <ul> tags)
        try:
            description_parts = []

            # Strategy: Collect all substantial text from <p> and <ul> tags
            # Skip: navigation, headers, short text
            all_p = self.driver.find_elements(By.TAG_NAME, "p")
            all_ul = self.driver.find_elements(By.TAG_NAME, "ul")

            print(f"   Found {len(all_p)} <p> tags and {len(all_ul)} <ul> tags")

            # Collect from <p> tags
            for p in all_p:
                text = p.text.strip()
                # Skip: short text, navigation items, metadata
                if (len(text) > 50 and
                    "·" not in text and  # Skip metadata lines
                    "ago" not in text.lower() and  # Skip date lines
                    "applicant" not in text.lower() and  # Skip applicant count
                    "notification" not in text.lower()):  # Skip notifications
                    description_parts.append(text)

            # Collect from <ul> tags (requirements, skills, etc.)
            for ul in all_ul:
                text = ul.text.strip()
                if len(text) > 50:
                    description_parts.append(text)

            if description_parts:
                self.job_description = "\n\n".join(description_parts[:15])  # First 15 blocks
                print(f"   ✓ Extracted description ({len(self.job_description)} chars from {len(description_parts[:15])} blocks)")
            else:
                print(f"   ⚠️  No substantial description text found")

        except Exception as e:
            print(f"   ⚠️  Could not extract description: {e}")

        # 6. Try to find salary/benefits
        try:
            # Benefits often in their own section
            all_text = self.driver.find_elements(By.TAG_NAME, "p")
            for elem in all_text:
                text = elem.text.strip()
                if "$" in text or "salary" in text.lower() or "compensation" in text.lower():
                    self.benefits = text
                    print(f"   ✓ Found benefits: {self.benefits}")
                    break
        except:
            pass

    def _extract_poster_info(self):
        """Extract job poster information using structure"""
        try:
            # Look for profile links (contain "/in/")
            profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")

            if profile_links:
                for link in profile_links:
                    href = link.get_attribute("href")
                    text = link.text.strip()

                    # Valid poster link should:
                    # 1. Have text (name)
                    # 2. Not be a random icon/image link
                    # 3. Contain "Job poster" or be in hiring team section
                    # Note: Text can be multi-line with name, title, "Job poster", etc.
                    if text and len(text) > 2 and len(text) < 200:
                        # Check if this is a job poster link
                        if "job poster" in text.lower() or "hiring team" in text.lower() or "recruiter" in text.lower():
                            self.poster_profile_url = href.split("?")[0]

                            # Parse the multi-line text to extract name and headline
                            lines = [line.strip() for line in text.split('\n') if line.strip()]

                            # First line is usually the name
                            if lines:
                                # Remove "• 3rd" or similar connection indicators
                                name_line = lines[0].replace('•', '').replace('3rd', '').replace('2nd', '').replace('1st', '').strip()
                                self.poster_name = name_line

                            # Look for headline (usually contains "at" or job title keywords)
                            for line in lines:
                                if " at " in line.lower() or "recruiter" in line.lower() or "manager" in line.lower():
                                    self.poster_headline = line.strip()
                                    break

                            # Extract profile ID from URL
                            match = re.search(r'/in/([^/?]+)', self.poster_profile_url)
                            if match:
                                self.poster_profile_id = match.group(1)

                            print(f"   ✓ Found poster: {self.poster_name} (ID: {self.poster_profile_id})")
                            if self.poster_headline:
                                print(f"   ✓ Found headline: {self.poster_headline}")

                            break
            else:
                print(f"   ⚠️  No poster profile links found")

        except Exception as e:
            print(f"   ⚠️  Could not extract poster info: {e}")

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
