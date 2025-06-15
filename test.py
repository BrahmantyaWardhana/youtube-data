import csv
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# YouTube Data API configuration
API_KEY = os.getenv('API_KEY')  # Replace with your actual API key
SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
CHANNEL_URL = 'https://www.googleapis.com/youtube/v3/channels'

def search_channels_by_region(region_code, max_results=50):
    """
    Search for channels in a specific region
    
    Args:
        region_code (str): ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'JP')
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of channel information dictionaries
    """
    channels = []
    
    # First, search for popular videos in the region to find channels
    search_params = {
        'part': 'snippet',
        'regionCode': region_code,
        'maxResults': max_results,
        'type': 'video',
        'order': 'viewCount',  # Get popular videos
        'key': API_KEY
    }
    
    response = requests.get(SEARCH_URL, params=search_params)
    data = response.json()
    
    # Extract unique channel IDs from search results
    channel_ids = set()
    for item in data.get('items', []):
        channel_id = item['snippet']['channelId']
        channel_ids.add(channel_id)
    
    # Get channel details
    channels_params = {
        'part': 'snippet,statistics',
        'id': ','.join(channel_ids),
        'key': API_KEY
    }
    
    channels_response = requests.get(CHANNEL_URL, params=channels_params)
    channels_data = channels_response.json()
    
    # Format channel information
    for channel in channels_data.get('items', []):
        channel_info = {
            'id': channel['id'],
            'title': channel['snippet']['title'],
            'description': channel['snippet']['description'],
            'published_at': channel['snippet']['publishedAt'],
            'subscriber_count': channel['statistics'].get('subscriberCount', 'N/A'),
            'view_count': channel['statistics']['viewCount'],
            'video_count': channel['statistics']['videoCount'],
            'country': channel['snippet'].get('country', region_code),
            'thumbnail': channel['snippet']['thumbnails']['default']['url']
        }
        channels.append(channel_info)
    
    return channels

def write_to_csv(channels, filename='youtube_channels.csv'):
    """
    Write channel information to a CSV file
    
    Args:
        channels (list): List of channel information dictionaries
        filename (str): Output CSV filename
    """
    if not channels:
        print("No channels to write to CSV.")
        return
    
    # Get fieldnames from the first channel dict
    fieldnames = channels[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(channels)
    
    print(f"Successfully wrote {len(channels)} channels to {filename}")

# Example usage
if __name__ == '__main__':
    region = input("Enter a region code (e.g., US, GB, JP): ").upper()
    max_results = int(input("Enter maximum number of results (1-50): "))
    
    channels = search_channels_by_region(region, max_results)
    write_to_csv(channels, f'youtube_channels_{region}.csv')