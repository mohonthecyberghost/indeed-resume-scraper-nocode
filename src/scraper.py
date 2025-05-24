import os
import time
import json
import logging
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

    def setup_driver(self):
        """Initialize headless Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Direct Chrome driver setup
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def login(self):
        """Login to Indeed Resume"""
        try:
            self.driver.get('https://www.indeed.com/resumes')
            
            # Click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tn-element="login-button"]'))
            )
            login_button.click()

            # Enter credentials
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'login-email-input'))
            )
            email_input.send_keys(self.indeed_email)

            password_input = self.driver.find_element(By.ID, 'login-password-input')
            password_input.send_keys(self.indeed_password)

            # Submit login
            submit_button = self.driver.find_element(By.CSS_SELECTOR, '[data-tn-element="login-submit-button"]')
            submit_button.click()

            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-tn-element="resume-search-input"]'))
            )
            logger.info("Successfully logged in to Indeed")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
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