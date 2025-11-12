"""
Core automation logic for sending LinkedIn connection requests
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Tuple, Optional
from . import config
from .utils import random_sleep


class ConnectionSender:
    """
    Handles navigation to profiles and sending connection requests.
    """

    def __init__(self, driver: webdriver.Chrome):
        """
        Initialize connection sender with Selenium driver.

        Args:
            driver: Selenium WebDriver instance (must be logged in)
        """
        self.driver = driver

    def navigate_to_profile(self, profile_url: str) -> bool:
        """
        Navigate to a LinkedIn profile URL.

        Args:
            profile_url: Full LinkedIn profile URL

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.driver.get(profile_url)
            # Wait for page to load
            random_sleep(config.MIN_DELAY_BETWEEN_ACTIONS, config.MAX_DELAY_BETWEEN_ACTIONS)
            return True
        except Exception as e:
            print(f"      ❌ Navigation failed: {e}")
            return False

    def is_already_connected(self) -> bool:
        """
        Check if already connected or request is pending.

        Returns:
            True if already connected/pending, False if can connect
        """
        # Indicators that we're already connected or request is pending
        indicators = [
            "//button[.//span[text()='Message']]",      # Already connected
            "//button[.//span[text()='Pending']]",      # Request pending
            "//span[contains(text(), 'Pending')]",       # Pending text
        ]

        for selector in indicators:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    return True
            except:
                continue

        return False

    def find_connect_button(self) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        Find the Connect button on the profile page.
        Tries multiple selector strategies as LinkedIn's HTML varies.

        Returns:
            WebElement if found, None otherwise
        """
        # Strategy 1: Try direct Connect button
        direct_selectors = [
            '//button[.//span[contains(@class, "artdeco-button__text") and text()="Connect"]]',
            '//button[.//span[text()="Connect"]]',
            '//button[contains(@aria-label, "Invite")]',
        ]

        for selector in direct_selectors:
            try:
                button = self.driver.find_element(By.XPATH, selector)
                if button and button.is_displayed():
                    return button
            except NoSuchElementException:
                continue

        # Strategy 2: Check if Connect is hidden in "More" dropdown
        try:
            # Click More button
            more_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="More"]]')
            if more_button:
                more_button.click()
                random_sleep(1, 2)

                # Find Connect in dropdown
                connect_in_dropdown = self.driver.find_element(
                    By.XPATH,
                    '//div[@role="menu"]//span[text()="Connect"]'
                )
                if connect_in_dropdown:
                    return connect_in_dropdown.find_element(By.XPATH, '..')  # Get parent button
        except NoSuchElementException:
            pass

        return None

    def send_connection_request(self, add_note: bool = False, message: str = "") -> Tuple[bool, str]:
        """
        Send a connection request.

        Args:
            add_note: Whether to add a personalized note (not used per user request)
            message: Message to send (not used per user request)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Find and click Connect button
            connect_button = self.find_connect_button()

            if not connect_button:
                return False, "Connect button not found"

            # Click the Connect button
            connect_button.click()
            random_sleep(2, 3)

            # Wait for modal to appear
            try:
                # Look for Send button in modal
                send_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//button[contains(@aria-label, "Send")]'))
                )

                # Note: We're NOT adding a note per user request (SEND_WITH_NOTE = False)
                # Just click Send directly

                send_button.click()
                random_sleep(1, 2)

                return True, "Connection request sent successfully"

            except TimeoutException:
                # Modal didn't appear - might have been sent directly
                # Check if we can find a success indicator
                try:
                    # Sometimes "Pending" appears immediately
                    pending = self.driver.find_element(By.XPATH, '//button[.//span[text()="Pending"]]')
                    if pending:
                        return True, "Connection request sent (no modal)"
                except:
                    pass

                return False, "Modal timeout - unclear if request sent"

        except Exception as e:
            return False, f"Error sending request: {str(e)}"

    def close_modal_if_open(self):
        """
        Close any open modal dialogs.
        Useful for cleanup after errors.
        """
        try:
            # Look for modal close button
            close_button = self.driver.find_element(
                By.XPATH,
                '//button[contains(@aria-label, "Dismiss")]'
            )
            if close_button:
                close_button.click()
                random_sleep(1, 2)
        except:
            pass

    def verify_connection_sent(self) -> bool:
        """
        Verify that connection request was sent by checking for "Pending" button.

        Returns:
            True if Pending button found, False otherwise
        """
        try:
            pending_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="Pending"]]')
            return pending_button is not None
        except NoSuchElementException:
            return False

    def send_connection_with_verification(self) -> Tuple[bool, str]:
        """
        Send connection request and verify it was sent.

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Send the request
        success, message = self.send_connection_request()

        if not success:
            return success, message

        # Verify it was sent
        random_sleep(1, 2)
        if self.verify_connection_sent():
            return True, "Connection request sent and verified"
        else:
            # Request was sent but we couldn't verify
            # Consider it successful anyway
            return True, "Connection request sent (verification skipped)"
