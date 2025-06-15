import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# YouTube Data API configuration
API_KEY = os.getenv('API_KEY')  # Replace with your actual API key
SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
CHANNEL_URL = 'https://www.googleapis.com/youtube/v3/channels'

def search_us_channels(max_results=50):
    """
    Search for channels that are specifically marked as US-based
    
    Args:
        max_results (int): Maximum number of results to return (1-50)
        
    Returns:
        list: List of channel information dictionaries with confirmed US country code
    """
    channels = []
    attempts = 0
    max_attempts = 3  # To handle pagination if needed
    
    # Parameters for initial channel search
    search_params = {
        'part': 'snippet',
        'maxResults': min(max_results, 50),  # API max is 50 per request
        'type': 'channel',
        'relevanceLanguage': 'en',
        'regionCode': 'US',
        'key': API_KEY
    }
    
    while len(channels) < max_results and attempts < max_attempts:
        attempts += 1
        
        # Search for channels
        response = requests.get(SEARCH_URL, params=search_params)
        data = response.json()
        
        if 'items' not in data or not data['items']:
            break
        
        # Extract channel IDs
        channel_ids = [item['snippet']['channelId'] for item in data['items']]
        
        # Get detailed channel info
        if channel_ids:
            channels_params = {
                'part': 'snippet,statistics',
                'id': ','.join(channel_ids),
                'key': API_KEY
            }
            
            channels_response = requests.get(CHANNEL_URL, params=channels_params)
            channels_data = channels_response.json()
            
            # Process and filter channels
            for channel in channels_data.get('items', []):
                # Only include channels that explicitly list US as country
                if channel['snippet'].get('country', '').upper() == 'US':
                    # Convert subscriber count to readable format
                    sub_count = channel['statistics'].get('subscriberCount', 'N/A')
                    if sub_count != 'N/A':
                        sub_count = int(sub_count)
                    
                    channel_info = {
                        'channel_id': channel['id'],
                        'title': channel['snippet']['title'],
                        'description': channel['snippet']['description'],
                        'published_at': format_date(channel['snippet']['publishedAt']),
                        'subscriber_count': sub_count,
                        'view_count': int(channel['statistics']['viewCount']),
                        'video_count': int(channel['statistics']['videoCount']),
                        'country': channel['snippet'].get('country', 'US'),
                        'thumbnail_url': channel['snippet']['thumbnails']['default']['url'],
                        'custom_url': channel['snippet'].get('customUrl', ''),
                        'keywords': channel['snippet'].get('tags', [])
                    }
                    channels.append(channel_info)
                    
                    # Stop if we've reached the desired number of results
                    if len(channels) >= max_results:
                        break
        
        # Set up for next page if needed
        if 'nextPageToken' in data and len(channels) < max_results:
            search_params['pageToken'] = data['nextPageToken']
        else:
            break
    
    return channels[:max_results]  # Return only up to requested max

def format_date(iso_date):
    """Convert ISO 8601 date to more readable format"""
    try:
        dt = datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d')
    except:
        return iso_date

def write_to_csv(channels, filename='us_youtube_channels.csv'):
    """
    Write channel information to a CSV file
    
    Args:
        channels (list): List of channel information dictionaries
        filename (str): Output CSV filename
    """
    if not channels:
        print("No channels to write to CSV.")
        return
    
    # Define field order for CSV
    fieldnames = [
        'channel_id',
        'title',
        'description',
        'published_at',
        'subscriber_count',
        'view_count',
        'video_count',
        'country',
        'custom_url',
        'thumbnail_url',
        'keywords'
    ]
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for channel in channels:
            # Convert keywords list to string
            channel_copy = channel.copy()
            channel_copy['keywords'] = '|'.join(channel.get('keywords', []))
            writer.writerow(channel_copy)
    
    print(f"Successfully wrote {len(channels)} US-based channels to {filename}")

if __name__ == '__main__':
    try:
        max_results = int(input("How many US-based channels do you want to retrieve? (1-50): "))
        max_results = max(1, min(50, max_results))  # Ensure between 1-50
        
        print("Searching for US-based YouTube channels...")
        us_channels = search_us_channels(max_results)
        
        if us_channels:
            filename = f"us_youtube_channels_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            write_to_csv(us_channels, filename)
        else:
            print("No US-based channels found with the current filters.")
    except ValueError:
        print("Please enter a valid number between 1 and 50.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")