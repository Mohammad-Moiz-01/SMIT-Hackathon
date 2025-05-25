from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from .utils import clean_text, polite_sleep, extract_skills
import re

def scrape_linkedin(search_term='software engineer', location='', max_pages=1):
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    jobs_data = []
    
    try:
        for page in range(max_pages):
            # LinkedIn uses different URL structure
            url = f"https://www.linkedin.com/jobs/search/?keywords={search_term}&location={location}&start={page * 25}"
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Scroll to load all jobs
            scroll_pause_time = 1
            screen_height = driver.execute_script("return window.screen.height;")
            i = 1
            
            while True:
                driver.execute_script(f"window.scrollTo(0, {screen_height * i});")
                i += 1
                time.sleep(scroll_pause_time)
                scroll_height = driver.execute_script("return document.body.scrollHeight;")
                if (screen_height * i) > scroll_height:
                    break
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards:
                title_elem = card.find('h3', class_='base-search-card__title')
                title = clean_text(title_elem.text) if title_elem else "N/A"
                
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                company = clean_text(company_elem.text) if company_elem else "N/A"
                
                location_elem = card.find('span', class_='job-search-card__location')
                location = clean_text(location_elem.text) if location_elem else "N/A"
                
                # Get job URL
                link_elem = card.find('a', class_='base-card__full-link')
                job_url = link_elem['href'] if link_elem else "N/A"
                
                # Get posting date
                date_elem = card.find('time', class_='job-search-card__listdate')
                if not date_elem:
                    date_elem = card.find('time', class_='job-search-card__listdate--new')
                date_posted = clean_text(date_elem.text) if date_elem else "N/A"
                
                # Get job description (requires another click)
                description = fetch_linkedin_job_description(driver, card)
                skills = extract_skills(description)
                
                jobs_data.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': "N/A",  # LinkedIn often doesn't show salary in listings
                    'url': job_url,
                    'date_posted': date_posted,
                    'description': description,
                    'skills': ', '.join(skills) if skills else "N/A",
                    'source': 'LinkedIn'
                })
                
    finally:
        driver.quit()
    
    return jobs_data

def fetch_linkedin_job_description(driver, card):
    try:
        # Find the job card's clickable element
        link_elem = card.find('a', class_='base-card__full-link')
        if not link_elem:
            return "N/A"
        
        # Click on the job card to load description
        job_element = driver.find_element(By.XPATH, f"//a[@href='{link_elem['href']}']")
        job_element.click()
        time.sleep(2)  # Wait for description to load
        
        # Now get the description
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        description_div = soup.find('div', class_='description__text')
        return clean_text(description_div.text) if description_div else "N/A"
        
    except Exception as e:
        print(f"Error fetching LinkedIn job description: {e}")
        return "N/A"

        