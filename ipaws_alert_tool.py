import streamlit as st
import folium
import urllib.request
import json
import requests
from datetime import datetime
from streamlit_folium import st_folium
import re

# OpenCage API key
opencage_api_key = "091322c2c53048edbe1d12dd1b24c0d2"  # Replace with your actual OpenCage API key
# Google Geocoding API key
google_api_key = "AIzaSyAvwk_o6huhAmCSx3nX87KGHVLYUdmMv90"  # Replace with your actual Google API key

# Cache for storing geocoded results
cache = {}

def normalize_area_description(area_desc):
    """
    Normalize area description by removing special characters and extra spaces.
    """
    area_desc = re.sub(r'[^a-zA-Z0-9\s,]', '', area_desc)
    area_desc = re.sub(r'\s+', ' ', area_desc).strip()
    return area_desc

def get_coordinates_opencage(area_name, api_key):
    """
    Fetch coordinates from OpenCage API.
    """
    url = f"https://api.opencagedata.com/geocode/v1/json"
    params = {
        'key': api_key,
        'q': normalize_area_description(area_name),
        'limit': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']
            return (location['lat'], location['lng'])
    return None

def get_coordinates_google(area_name, api_key):
    """
    Fetch coordinates from Google Geocoding API.
    """
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': normalize_area_description(area_name),
        'key': api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
    return None

def get_coordinates_with_cache(area_name, opencage_api_key, google_api_key):
    """
    Fetch coordinates using OpenCage and Google APIs with caching.
    """
    if area_name in cache:
        return cache[area_name]
    
    coords = get_coordinates_opencage(area_name, opencage_api_key)
    if not coords:
        coords = get_coordinates_google(area_name, google_api_key)
    
    if coords:
        cache[area_name] = coords
    
    return coords

def format_time(time_str):
    """
    Format the time string for display.
    """
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_within_date_range(sent_date, start_date, end_date):
    """
    Check if a date is within the specified range.
    """
    sent_dt = datetime.strptime(sent_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    return start_date <= sent_dt <= end_date

def create_map(start_date, end_date, state=None):
    """
    Create a map with markers for FEMA alerts.
    """
    baseUrl = "https://www.fema.gov/api/open/v1/IpawsArchivedAlerts"
    orderby = "?$orderby=id"
    format = "&$format=json"

    try:
        # Fetch data from FEMA API
        request = urllib.request.urlopen(baseUrl + orderby + format)
        result = request.read()
        jsonData = json.loads(result.decode())
        
        # Filter records by date range and state
        records = [record for record in jsonData['IpawsArchivedAlerts'] if is_within_date_range(record['sent'], start_date, end_date)]
        if state:
            records = [record for record in records if record['info'][0].get('areas', [{}])[0].get('state', None) == state]

        st.write(f"Total records retrieved: {len(records)}")

        # Initialize the map
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=5, tiles='OpenStreetMap')
        
        # Process each record and add markers
        for record in records:
            identifier = record['identifier']
            sender = record['sender']
            sent = format_time(record['sent'])

            if record.get('info'):
                event = record['info'][0].get('event', 'No event description')
                description = record['info'][0].get('description', 'No description')

                area_desc = record['info'][0].get('areas', [{}])[0].get('areaDesc', None)
                area_coords = record['info'][0].get('areas', [{}])[0].get('coordinates', None)

                if area_desc:
                    coords = get_coordinates_with_cache(area_desc, opencage_api_key, google_api_key)
                    if not coords:
                        coords = [0, -160]  # Fallback to ocean if geocoding fails
                    color = 'blue' if coords != [0, -160] else 'red'
                    source = 'geocoded from area description'
                elif area_coords:
                    coords = area_coords
                    color = 'green'
                    source = 'coordinates from API'
                else:
                    coords = [0, -160]  # Default to ocean
                    color = 'red'
                    source = 'no accurate location'

                popup_content = f"""
                <b>{event}</b><br>
                {description}<br>
                Identifier: {identifier}<br>
                Sender: {sender}<br>
                Sent: {sent}<br>
                Area_description: {area_desc}<br>
                Source: {source}
                """
                
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=identifier,
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
            else:
                folium.Marker(
                    location=[0, -160],  # Default to ocean
                    popup=folium.Popup(f"Identifier: {identifier}<br>Sender: {sender}<br>Sent: {sent}<br>Source: no accurate location", max_width=300),
                    tooltip=f"{identifier} (No info key)",
                    icon=folium.Icon(color='red', icon='exclamation-sign')
                ).add_to(m)

        return m

    except urllib.error.HTTPError as e:
        st.error(f"HTTPError: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        st.error(f"URLError: {e.reason}")
    except KeyError as e:
        st.error(f"KeyError: Missing key {e}")
    except ValueError as e:
        st.error(f"ValueError: {e}")

# Sidebar inputs for filtering
st.sidebar.title("FEMA Alerts Filter")
start_date_str = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
end_date_str = st.sidebar.date_input("End Date", datetime(2022, 3, 1))
state = st.sidebar.text_input("State (Optional):", "")

try:
    start_date = datetime.combine(start_date_str, datetime.min.time())
    end_date = datetime.combine(end_date_str, datetime.min.time())
    with st.spinner('Loading map...'):
        m = create_map(start_date, end_date, state)
    if m:
        st_folium(m, width=1600, height=900)
except ValueError:
    st.error("Invalid date format. Please use YYYY-MM-DD.")
