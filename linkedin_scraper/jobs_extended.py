"""
Extended Job class that includes job poster/recruiter information extraction
"""
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from .jobs import Job


class JobExtended(Job):
    """
    Extended Job class that adds extraction of job poster/recruiter information.

    Additional fields:
    - poster_name: Name of the person who posted the job
    - poster_headline: Headline/title of the poster
    - poster_profile_url: LinkedIn profile URL of the poster
    - poster_profile_id: Profile ID extracted from the URL
    """

    def __init__(
        self,
        linkedin_url=None,
        job_title=None,
        company=None,
        company_linkedin_url=None,
        location=None,
        posted_date=None,
        applicant_count=None,
        job_description=None,
        benefits=None,
        poster_name=None,
        poster_headline=None,
        poster_profile_url=None,
        poster_profile_id=None,
        driver=None,
        close_on_complete=True,
        scrape=True,
    ):
        # Initialize poster fields
        self.poster_name = poster_name
        self.poster_headline = poster_headline
        self.poster_profile_url = poster_profile_url
        self.poster_profile_id = poster_profile_id

        # Call parent constructor (will trigger scrape if scrape=True)
        super().__init__(
            linkedin_url=linkedin_url,
            job_title=job_title,
            company=company,
            company_linkedin_url=company_linkedin_url,
            location=location,
            posted_date=posted_date,
            applicant_count=applicant_count,
            job_description=job_description,
            benefits=benefits,
            driver=driver,
            close_on_complete=close_on_complete,
            scrape=scrape,
        )

    def __repr__(self):
        poster_info = f" posted by {self.poster_name}" if self.poster_name else ""
        return f"<JobExtended {self.job_title} at {self.company}{poster_info}>"

    def to_dict(self):
        """Override to include poster information"""
        base_dict = super().to_dict()
        base_dict.update({
            "poster_name": self.poster_name,
            "poster_headline": self.poster_headline,
            "poster_profile_url": self.poster_profile_url,
            "poster_profile_id": self.poster_profile_id,
        })
        return base_dict

    def scrape_logged_in(self, close_on_complete=True):
        """Extended scraping that includes job poster information"""
        # First, run the parent scraping logic to get all basic job info
        super().scrape_logged_in(close_on_complete=False)

        # Now extract job poster information
        self._extract_job_poster()

        # Close driver if requested
        if close_on_complete:
            self.driver.close()

    def _extract_job_poster(self):
        """Extract job poster/recruiter information from the page"""
        try:
            # Try multiple selectors for job poster section
            poster_selectors = [
                "jobs-poster",
                "jobs-poster__container",
                "hiring-team",
                "jobs-unified-top-card__subtitle-secondary-grouping",
            ]

            poster_container = None
            for selector in poster_selectors:
                try:
                    poster_container = self.wait_for_element_to_load(
                        name=selector,
                        timeout=5
                    )
                    if poster_container:
                        break
                except TimeoutException:
                    continue

            if not poster_container:
                print("⚠️  No job poster container found")
                return

            # Try to find the poster's profile link
            try:
                # Look for anchor tag with linkedin.com/in/ URL
                links = poster_container.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/in/" in href:
                        self.poster_profile_url = href.split("?")[0]  # Remove query params

                        # Extract profile ID from URL
                        # Format: https://www.linkedin.com/in/profile-id/
                        if "/in/" in self.poster_profile_url:
                            profile_id = self.poster_profile_url.split("/in/")[1].rstrip("/")
                            self.poster_profile_id = profile_id

                        # Get poster name from link text
                        poster_name_text = link.text.strip()
                        if poster_name_text:
                            self.poster_name = poster_name_text
                        break
            except (NoSuchElementException, Exception) as e:
                print(f"⚠️  Could not extract poster profile link: {e}")

            # If we didn't get name from link, try other selectors
            if not self.poster_name:
                try:
                    name_selectors = [
                        ("class name", "jobs-poster__name"),
                        ("class name", "jobs-poster__name-link"),
                        ("xpath", "//div[contains(@class, 'jobs-poster')]//span[contains(@class, 'name')]"),
                    ]

                    for by_type, selector in name_selectors:
                        try:
                            if by_type == "class name":
                                elem = poster_container.find_element(By.CLASS_NAME, selector)
                            else:
                                elem = poster_container.find_element(By.XPATH, selector)

                            if elem and elem.text.strip():
                                self.poster_name = elem.text.strip()
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️  Could not extract poster name: {e}")

            # Try to extract poster headline/title
            try:
                headline_selectors = [
                    "jobs-poster__job-title",
                    "jobs-poster__subtitle",
                    "t-black--light",
                ]

                for selector in headline_selectors:
                    try:
                        headline_elem = poster_container.find_element(By.CLASS_NAME, selector)
                        if headline_elem and headline_elem.text.strip():
                            self.poster_headline = headline_elem.text.strip()
                            break
                    except:
                        continue
            except Exception as e:
                print(f"⚠️  Could not extract poster headline: {e}")

            # Log what we found
            if self.poster_name or self.poster_profile_id:
                print(f"✅ Found job poster: {self.poster_name} (ID: {self.poster_profile_id})")
            else:
                print("⚠️  Job poster information not found on this page")

        except Exception as e:
            print(f"❌ Error extracting job poster: {e}")
            # Don't raise - poster info is optional, main job data is more important
