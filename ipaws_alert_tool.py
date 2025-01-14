import streamlit as st
import folium
import urllib.request
import json
import requests
from datetime import datetime
from streamlit_folium import st_folium
import re

api_key = "091322c2c53048edbe1d12dd1b24c0d2"  # Replace with your actual OpenCage API key

# Function to clean and normalize area descriptions
def normalize_area_description(area_desc):
    # Remove any special characters and multiple spaces
    area_desc = re.sub(r'[^a-zA-Z0-9\s,]', '', area_desc)
    area_desc = re.sub(r'\s+', ' ', area_desc).strip()
    return area_desc

def get_coordinates_opencage(area_name, api_key):
    normalized_area_name = normalize_area_description(area_name)
    url = f"https://api.opencagedata.com/geocode/v1/json"
    params = {
        'key': api_key,
        'q': normalized_area_name,
        'limit': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        quota_remaining = response.headers.get('X-RateLimit-Remaining')
        st.write(f"Quota remaining: {quota_remaining}")
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']
            return (location['lat'], location['lng'])
        else:
            return None
    else:
        st.write(f"Error: {response.status_code} {response.text}")
        return None

def format_time(time_str):
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_within_date_range(sent_date, start_date, end_date):
    sent_dt = datetime.strptime(sent_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    return start_date <= sent_dt <= end_date

def create_map(start_date, end_date):
    baseUrl = "https://www.fema.gov/api/open/v1/IpawsArchivedAlerts"
    orderby = "?$orderby=id"
    format = "&$format=json"

    try:
        request = urllib.request.urlopen(baseUrl + orderby + format)
        result = request.read()
        jsonData = json.loads(result.decode())
        
        records = [record for record in jsonData['IpawsArchivedAlerts'] if is_within_date_range(record['sent'], start_date, end_date)]
        st.write(f"Total records retrieved: {len(records)}")

        m = folium.Map(location=[37.0902, -95.7129], zoom_start=5, tiles='OpenStreetMap')
        
        for record in records:
            identifier = record['identifier']
            sender = record['sender']
            sent = format_time(record['sent'])

            if record.get('info'):
                event = record['info'][0].get('event', 'No event description')
                description = record['info'][0].get('description', 'No description')

                area_coords = [0, -160]  # Default to ocean if no coordinates found

                if 'areas' in record['info'][0]:
                    areas = record['info'][0]['areas'][0]
                    area_desc = areas.get('areaDesc', None)

                    if area_desc:
                        area_coords = get_coordinates_opencage(area_desc, api_key)
                        if not area_coords:
                            area_coords = [0, -160]  # Fallback to ocean if geocoding fails

                color = 'blue' if area_coords != [0, -160] else 'red'

                folium.Marker(
                    location=area_coords,
                    popup=folium.Popup(f"<b>{event}</b><br>{description}<br>Identifier: {identifier}<br>Sender: {sender}<br>Sent: {sent}", max_width=300),
                    tooltip=identifier,
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
            else:
                folium.Marker(
                    location=[0, -160],  # Default to ocean
                    popup=folium.Popup(f"Identifier: {identifier}<br>Sender: {sender}<br>Sent: {sent}", max_width=300),
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

st.sidebar.title("FEMA Alerts Filter")
start_date_str = st.sidebar.text_input("Start Date (YYYY-MM-DD):", "2022-01-01")
end_date_str = st.sidebar.text_input("End Date (YYYY-MM-DD):", "2022-12-31")

try:
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    with st.spinner('Loading map...'):
        m = create_map(start_date, end_date)
    if m:
        st_folium(m, width=1600, height=900)
except ValueError:
    st.error("Invalid date format. Please use YYYY-MM-DD.")
