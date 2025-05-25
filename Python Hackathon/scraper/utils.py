import time
import random
import pandas as pd
from datetime import datetime
import os

def save_to_csv(data, filename='jobs_data.csv'):
    """Save scraped data to CSV file, appending if file exists"""
    df = pd.DataFrame(data)
    
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv(filename, index=False)
    else:
        df.to_csv(filename, index=False)

def polite_sleep():
    """Random delay between requests to be polite"""
    time.sleep(random.uniform(1, 3))

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_skills(description):
    """Extract potential skills from job description (basic implementation)"""
    skills = []
    common_skills = [
        'python', 'java', 'sql', 'javascript', 'html', 'css', 
        'aws', 'azure', 'docker', 'kubernetes', 'machine learning',
        'data analysis', 'excel', 'tableau', 'power bi', 'react',
        'angular', 'node.js', 'django', 'flask', 'pandas', 'numpy',
        'tensorflow', 'pytorch', 'git', 'linux', 'rest api', 'mongodb',
        'mysql', 'postgresql', 'spark', 'hadoop', 'scala', 'c++', 'c#',
        'php', 'ruby', 'go', 'rust', 'typescript'
    ]
    
    if not description:
        return skills
        
    description = description.lower()
    for skill in common_skills:
        if skill in description:
            skills.append(skill)
    
    return skills

    