"""
App Store review scraper
"""

import feedparser
import pandas as pd
import time
import requests


def get_app_metadata(app_id):
    """
    Get app metadata including overall rating and total review count
    
    Args:
        app_id: Apple App Store app ID
    
    Returns:
        dict with 'overall_rating', 'total_reviews', 'app_name'
    """
    try:
        url = f"https://itunes.apple.com/lookup?id={app_id}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('resultCount', 0) > 0:
            app_data = data['results'][0]
            return {
                'overall_rating': app_data.get('averageUserRating', 0),
                'total_reviews': app_data.get('userRatingCount', 0),
                'app_name': app_data.get('trackName', 'Unknown App')
            }
    except Exception as e:
        print(f"Error fetching app metadata: {e}")
    
    return {
        'overall_rating': None,
        'total_reviews': None,
        'app_name': 'Unknown App'
    }


def scrape_app_reviews(app_id, max_pages=10, progress_callback=None):
    """
    Scrape reviews from Apple App Store RSS feed
    
    Args:
        app_id: Apple App Store app ID
        max_pages: Maximum number of pages to scrape (50 reviews per page)
        progress_callback: Optional function to call with progress updates (page_num, status_text)
    
    Returns:
        pandas DataFrame with columns: rating, title, review, author, version, date
    """
    all_reviews = []
    
    for page in range(1, max_pages + 1):
        if progress_callback:
            progress_callback(page, f"Fetching page {page}/{max_pages}...")
        
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/xml"
        
        try:
            feed = feedparser.parse(url)
            
            # If no entries, we've reached the end
            if not feed.entries:
                break
            
            for entry in feed.entries:
                all_reviews.append({
                    'rating': int(entry.get('im_rating', 0)),
                    'title': entry.get('title', ''),
                    'review': entry.content[0].value if hasattr(entry, 'content') else '',
                    'author': entry.get('author', ''),
                    'version': entry.get('im_version', ''),
                    'date': entry.get('updated', '')
                })
            
            time.sleep(0.5)  # Be polite to Apple's servers
            
        except Exception as e:
            if progress_callback:
                progress_callback(page, f"Error at page {page}: {e}")
            break
    
    return pd.DataFrame(all_reviews)
