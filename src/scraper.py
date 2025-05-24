import os
import time
import json
import logging
import random
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import re
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndeedResumeScraper:
    def __init__(self):
        load_dotenv()
        self.indeed_email = os.getenv('INDEED_EMAIL')
        self.indeed_password = os.getenv('INDEED_PASSWORD')
        self.driver = None
        self.setup_driver()

    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to appear more human-like"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def setup_driver(self):
        """Initialize headless Chrome driver with anti-detection measures"""
        try:
            chrome_options = Options()
            
            # Add random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # Add additional arguments to appear more browser-like
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Add experimental options
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set window size
            self.driver.set_window_size(1920, 1080)
            
            # Add additional headers
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })
            
            # Add additional headers to appear more browser-like
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            })
            
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def wait_for_manual_verification(self, timeout=300):
        """Wait for manual verification to be completed"""
        logger.info("Waiting for manual verification...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if we're still on a verification page
                if "verify" in self.driver.current_url.lower() or "captcha" in self.driver.current_url.lower():
                    logger.info("Still on verification page. Please complete the verification...")
                    time.sleep(5)
                    continue
                    
                # Check if we're logged in
                if len(self.driver.find_elements(By.CSS_SELECTOR, '[data-tn-component="auth-header-account-menu"]')) > 0:
                    logger.info("Verification completed successfully!")
                    return True
                    
                # Check for error messages
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.error-message, .errorlist')
                if error_elements:
                    error_text = error_elements[0].text
                    logger.error(f"Error during verification: {error_text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error while waiting for verification: {str(e)}")
                
            time.sleep(5)
            
        logger.error("Timeout waiting for manual verification")
        return False

    def login(self):
        """Login to Indeed Resume with anti-detection measures and verification handling"""
        try:
            if not self.indeed_email or not self.indeed_password:
                logger.error("Indeed credentials not found in environment variables")
                return False

            # First visit Indeed homepage to get cookies
            logger.info("Visiting Indeed homepage...")
            self.driver.get('https://www.indeed.com')
            self.random_delay(2, 4)
            
            # Click sign in with a more natural approach
            logger.info("Looking for sign in button...")
            try:
                sign_in_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-gnav-element-name="SignIn"]'))
                )
                # Move to element and click with random delay
                self.driver.execute_script("arguments[0].scrollIntoView(true);", sign_in_button)
                self.random_delay()
                sign_in_button.click()
            except:
                # Try alternative sign in URL
                logger.info("Trying direct sign in URL...")
                self.driver.get('https://secure.indeed.com/account/login')
            
            self.random_delay(2, 4)
            
            # Enter email with human-like behavior
            logger.info("Entering email...")
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'login-email-input'))
                )
                # Type email with random delays between characters
                for char in self.indeed_email:
                    email_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                logger.error(f"Failed to enter email: {str(e)}")
                self.driver.save_screenshot('email_error.png')
                return False
            
            self.random_delay()
            
            # Enter password with human-like behavior
            logger.info("Entering password...")
            try:
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'login-password-input'))
                )
                # Type password with random delays between characters
                for char in self.indeed_password:
                    password_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                logger.error(f"Failed to enter password: {str(e)}")
                self.driver.save_screenshot('password_error.png')
                return False
            
            self.random_delay()
            
            # Click sign in button
            logger.info("Clicking sign in button...")
            try:
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, 'login-submit-button'))
                )
                # Move to element and click with random delay
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                self.random_delay()
                submit_button.click()
            except Exception as e:
                logger.error(f"Failed to click sign in button: {str(e)}")
                self.driver.save_screenshot('submit_error.png')
                return False
            
            # Wait for login to complete with longer timeout
            self.random_delay(3, 5)
            
            # Check for verification requirements
            current_url = self.driver.current_url.lower()
            if "verify" in current_url or "captcha" in current_url:
                logger.info("Additional verification required...")
                self.driver.save_screenshot('verification_required.png')
                
                # Wait for manual verification
                if not self.wait_for_manual_verification():
                    logger.error("Manual verification failed or timed out")
                    return False
            
            # Check if login was successful
            try:
                logger.info("Checking login status...")
                WebDriverWait(self.driver, 20).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-tn-component="auth-header-account-menu"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.error-message'))
                    )
                )
                
                # Check if we're logged in
                if len(self.driver.find_elements(By.CSS_SELECTOR, '[data-tn-component="auth-header-account-menu"]')) > 0:
                    logger.info("Successfully logged in to Indeed")
                    
                    # Navigate to resume search with random delay
                    self.random_delay(2, 4)
                    logger.info("Navigating to resume search...")
                    self.driver.get('https://www.indeed.com/resumes/search')
                    self.random_delay(3, 5)
                    
                    # Verify we're on the resume search page
                    current_url = self.driver.current_url
                    logger.info(f"Current URL: {current_url}")
                    
                    if 'resumes/search' not in current_url:
                        logger.error(f"Failed to navigate to resume search. Current URL: {current_url}")
                        self.driver.save_screenshot('navigation_error.png')
                        return False
                        
                    logger.info("Successfully navigated to resume search")
                    return True
                else:
                    logger.error("Login failed - error message present")
                    self.driver.save_screenshot('login_failed.png')
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to verify login status: {str(e)}")
                self.driver.save_screenshot('verification_error.png')
                return False

        except Exception as e:
            logger.error(f"Login failed with error: {str(e)}")
            self.driver.save_screenshot('general_error.png')
            return False

    def search_resumes(self, filters: Dict) -> List[Dict]:
        """Search resumes with given filters"""
        try:
            # Navigate to resume search
            self.driver.get('https://www.indeed.com/resumes')
            
            # Enter search keywords
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-tn-element="resume-search-input"]'))
            )
            search_input.send_keys(filters['keywords'])
            
            # Enter location
            location_input = self.driver.find_element(By.CSS_SELECTOR, '[data-tn-element="resume-location-input"]')
            location_input.send_keys(filters['location'])
            
            # Apply additional filters if provided
            if 'experience_years' in filters:
                self._apply_experience_filter(filters['experience_years'])
            if 'education' in filters:
                self._apply_education_filter(filters['education'])
            
            # Click search
            search_button = self.driver.find_element(By.CSS_SELECTOR, '[data-tn-element="resume-search-button"]')
            search_button.click()
            
            # Wait for results and collect data
            return self._collect_search_results()
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def _apply_experience_filter(self, years: int):
        """Apply experience filter"""
        try:
            experience_button = self.driver.find_element(By.CSS_SELECTOR, '[data-tn-element="experience-filter"]')
            experience_button.click()
            
            # Select appropriate experience range
            experience_option = self.driver.find_element(
                By.XPATH, f"//div[contains(text(), '{years}+ years')]"
            )
            experience_option.click()
        except Exception as e:
            logger.warning(f"Failed to apply experience filter: {str(e)}")

    def _apply_education_filter(self, education: str):
        """Apply education filter"""
        try:
            education_button = self.driver.find_element(By.CSS_SELECTOR, '[data-tn-element="education-filter"]')
            education_button.click()
            
            # Select education level
            education_option = self.driver.find_element(
                By.XPATH, f"//div[contains(text(), '{education}')]"
            )
            education_option.click()
        except Exception as e:
            logger.warning(f"Failed to apply education filter: {str(e)}")

    def _collect_search_results(self) -> List[Dict]:
        """Collect search results and extract candidate information"""
        results = []
        try:
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.resume-card'))
            )
            
            # Get all resume cards
            resume_cards = self.driver.find_elements(By.CSS_SELECTOR, '.resume-card')
            
            for card in resume_cards:
                try:
                    # Extract basic information
                    name = card.find_element(By.CSS_SELECTOR, '.resume-name').text
                    
                    # Click to view full resume
                    card.click()
                    
                    # Wait for resume details to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.resume-details'))
                    )
                    
                    # Extract contact information
                    contact_info = self._extract_contact_info()
                    
                    # Download resume
                    resume_path = self._download_resume(name)
                    
                    results.append({
                        'name': name,
                        'email': contact_info.get('email'),
                        'phone': contact_info.get('phone'),
                        'resume_path': resume_path,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Go back to search results
                    self.driver.back()
                    
                except Exception as e:
                    logger.warning(f"Failed to process resume card: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to collect search results: {str(e)}")
        
        return results

    def _extract_contact_info(self) -> Dict[str, str]:
        """Extract contact information from resume"""
        contact_info = {'email': None, 'phone': None}
        try:
            resume_text = self.driver.find_element(By.CSS_SELECTOR, '.resume-details').text
            
            # Extract email using regex
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            email_match = re.search(email_pattern, resume_text)
            if email_match:
                contact_info['email'] = email_match.group(0)
            
            # Extract phone using regex
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phone_match = re.search(phone_pattern, resume_text)
            if phone_match:
                contact_info['phone'] = phone_match.group(0)
                
        except Exception as e:
            logger.warning(f"Failed to extract contact info: {str(e)}")
            
        return contact_info

    def _download_resume(self, name: str) -> Optional[str]:
        """Download resume and return the file path"""
        try:
            # Click download button
            download_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tn-element="download-resume"]'))
            )
            download_button.click()
            
            # Wait for download to complete
            time.sleep(2)  # Adjust based on download speed
            
            # Move file to appropriate location
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Find the downloaded file
            downloaded_file = max(
                [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir)],
                key=os.path.getctime
            )
            
            # Rename file
            new_filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            new_filepath = os.path.join(downloads_dir, new_filename)
            os.rename(downloaded_file, new_filepath)
            
            return new_filepath
            
        except Exception as e:
            logger.error(f"Failed to download resume: {str(e)}")
            return None

    def export_to_csv(self, results: List[Dict], output_path: str):
        """Export results to CSV"""
        try:
            df = pd.DataFrame(results)
            df.to_csv(output_path, index=False)
            logger.info(f"Results exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export to CSV: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit() 