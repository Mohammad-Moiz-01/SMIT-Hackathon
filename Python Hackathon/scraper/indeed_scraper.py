from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from .utils import clean_text, polite_sleep, save_to_csv, extract_skills
import re

def scrape_indeed(search_term='software engineer', location='', max_pages=2):
    base_url = "https://www.indeed.com"
    jobs_data = []
    
    for page in range(max_pages):
        params = {
            'q': search_term,
            'l': location,
            'start': page * 10
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(f"{base_url}/jobs", params=params, headers=headers)
        polite_sleep()
        
        if response.status_code != 200:
            print(f"Failed to fetch Indeed page {page + 1}")
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        for card in job_cards:
            title_elem = card.find('h2', class_='jobTitle')
            title = clean_text(title_elem.text) if title_elem else "N/A"
            
            company_elem = card.find('span', class_='companyName')
            company = clean_text(company_elem.text) if company_elem else "N/A"
            
            location_elem = card.find('div', class_='companyLocation')
            location = clean_text(location_elem.text) if location_elem else "N/A"
            
            # Extract salary if available
            salary_elem = card.find('div', class_='metadata salary-snippet-container')
            salary = clean_text(salary_elem.text) if salary_elem else "N/A"
            
            # Get job URL
            relative_url = title_elem.find('a')['href'] if title_elem and title_elem.find('a') else None
            job_url = urljoin(base_url, relative_url) if relative_url else "N/A"
            
            # Get posting date
            date_elem = card.find('span', class_='date')
            date_posted = clean_text(date_elem.text) if date_elem else "N/A"
            
            # Get job description (requires another request)
            description = fetch_indeed_job_description(job_url)
            skills = extract_skills(description)
            
            jobs_data.append({
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'date_posted': date_posted,
                'description': description,
                'skills': ', '.join(skills) if skills else "N/A",
                'source': 'Indeed'
            })
    
    return jobs_data

def fetch_indeed_job_description(url):
    if url == "N/A":
        return "N/A"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        polite_sleep()
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            description_div = soup.find('div', id='jobDescriptionText')
            return clean_text(description_div.text) if description_div else "N/A"
    except Exception as e:
        print(f"Error fetching job description: {e}")
    
    return "N/A"

    