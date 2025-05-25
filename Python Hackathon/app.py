import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import os
from pathlib import Path
import numpy as np

# Initialize data directory
Path("data").mkdir(exist_ok=True)

# App configuration
st.set_page_config(
    page_title="Real-Time Job Trend Analyzer",
    page_icon="📊",
    layout="wide"
)

# Constants
DEFAULT_COLUMNS = ['title', 'company', 'location', 'salary', 'url', 
                  'date_posted', 'description', 'skills', 'source']

# Sidebar for user input
with st.sidebar:
    st.title("Job Search Parameters")
    search_term = st.text_input("Job Title", "Data Analyst")
    location = st.text_input("Location", "")
    pages_to_scrape = st.slider("Pages to scrape per site", 1, 5, 1)
    
    st.markdown("---")
    if st.button("📥 Scrape Job Data", help="Fetch new job listings"):
        with st.spinner("Scraping job data..."):
            try:
                # Import scrapers only when needed to avoid unnecessary dependencies
                from scraper.indeed_scraper import scrape_indeed
                from scraper.linkedin_scraper import scrape_linkedin
                from scraper.utils import save_to_csv
                
                indeed_data = scrape_indeed(search_term, location, pages_to_scrape)
                linkedin_data = scrape_linkedin(search_term, location, pages_to_scrape)
                
                all_data = indeed_data + linkedin_data
                if all_data:
                    save_to_csv(all_data, 'data/jobs_data.csv')
                    st.success(f"✅ Scraped {len(all_data)} jobs successfully!")
                else:
                    st.warning("⚠️ No jobs found with these parameters")
                
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Scraping failed: {str(e)}")

# Load data with enhanced error handling
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    try:
        if os.path.exists('data/jobs_data.csv') and os.path.getsize('data/jobs_data.csv') > 0:
            df = pd.read_csv('data/jobs_data.csv')
            
            # Ensure all expected columns exist
            for col in DEFAULT_COLUMNS:
                if col not in df.columns:
                    df[col] = np.nan
            
            # Clean and process data
            df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
            df['skills'] = df['skills'].fillna('N/A')
            df['source'] = df['source'].fillna('Unknown')
            
            return df.dropna(how='all')  # Remove completely empty rows
        
        return pd.DataFrame(columns=DEFAULT_COLUMNS)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

df = load_data()

# Main dashboard
st.title("📊 Real-Time Job Trend Analyzer")

if df.empty:
    st.warning("No job data available. Please scrape some jobs first using the sidebar.")
    st.image("https://via.placeholder.com/800x400?text=No+Data+Available", use_column_width=True)
else:
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Jobs", len(df))
    col2.metric("Unique Companies", df['company'].nunique())
    col3.metric("Locations", df['location'].nunique())
    col4.metric("Primary Source", df['source'].mode()[0] if not df['source'].empty else "N/A")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Job Titles", "🛠️ Skills", "🌍 Locations", "📈 Trends"])
    
    with tab1:
        st.subheader("Top Job Titles")
        title_counts = df['title'].value_counts().head(10)
        if not title_counts.empty:
            fig = px.bar(title_counts, 
                         x=title_counts.index, 
                         y=title_counts.values,
                         labels={'x': 'Job Title', 'y': 'Count'},
                         color=title_counts.values,
                         color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View Raw Data"):
                st.dataframe(
                    df[['title', 'company', 'location', 'date_posted', 'source']]
                    .sort_values('date_posted', ascending=False)
                    .reset_index(drop=True)
                )
        else:
            st.info("No job title data available")
    
    with tab2:
        st.subheader("Top Required Skills")
        skills_df = df[df['skills'] != 'N/A'].copy()
        if not skills_df.empty:
            skills_df['skills'] = skills_df['skills'].str.split(', ')
            skills_exploded = skills_df.explode('skills')
            top_skills = skills_exploded['skills'].value_counts().head(15)
            
            fig = px.pie(top_skills, 
                         names=top_skills.index, 
                         values=top_skills.values,
                         title="Top 15 Skills in Demand")
            st.plotly_chart(fig, use_container_width=True)
            
            # Skills by job title
            st.subheader("Skills by Job Title")
            job_filter = st.selectbox("Select Job Title", skills_exploded['title'].unique())
            filtered_skills = skills_exploded[skills_exploded['title'] == job_filter]['skills'].value_counts().head(10)
            
            if not filtered_skills.empty:
                fig = px.bar(filtered_skills,
                             x=filtered_skills.index,
                             y=filtered_skills.values,
                             labels={'x': 'Skill', 'y': 'Count'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No skills data available for {job_filter}")
        else:
            st.info("No skills data available")
    
    with tab3:
        st.subheader("Job Locations")
        if not df.empty:
            location_counts = df['location'].value_counts().head(15)
            fig = px.bar(location_counts,
                         x=location_counts.index,
                         y=location_counts.values,
                         labels={'x': 'Location', 'y': 'Job Count'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Location map placeholder
            with st.expander("View on Map (Placeholder)"):
                st.info("This would show actual locations with geocoding in a production app")
                st.image("https://via.placeholder.com/800x400?text=Map+Visualization+Placeholder", 
                         use_column_width=True)
        else:
            st.info("No location data available")
    
    with tab4:
        st.subheader("Posting Trends Over Time")
        if not df.empty and pd.api.types.is_datetime64_any_dtype(df['date_posted']):
            df['posting_date'] = df['date_posted'].dt.date
            daily_counts = df.groupby('posting_date').size().reset_index(name='count')
            
            fig = px.line(daily_counts,
                          x='posting_date',
                          y='count',
                          title='Job Postings Over Time',
                          markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Date information not available or not in the correct format.")
        
        st.subheader("Source Distribution")
        if not df.empty:
            source_counts = df['source'].value_counts()
            fig = px.pie(source_counts,
                         names=source_counts.index,
                         values=source_counts.values,
                         title="Job Sources")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")

# Bottom sidebar controls
with st.sidebar:
    st.markdown("---")
    if st.button("🔄 Refresh Data", help="Reload data from file"):
        df = load_data()
        st.experimental_rerun()
    
    if st.button("🗑️ Clear All Data", help="Delete all collected data"):
        if os.path.exists('data/jobs_data.csv'):
            os.remove('data/jobs_data.csv')
            st.success("Data cleared successfully!")
            st.experimental_rerun()
        else:
            st.warning("No data file found to delete")
    
    st.markdown("---")
    st.markdown("### Data Info")
    st.info(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"Total records: {len(df)}")