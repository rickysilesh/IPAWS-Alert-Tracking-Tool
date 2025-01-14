# IPAWS Alert Tool

## Introduction
This project retrieves FEMA IPAWS archived alerts and visualizes them on a map using Streamlit and Folium. The primary goal is to accurately place markers on the map based on area descriptions from the alerts.

## Changes Made

### 1. OpenCage API Integration
- Integrated OpenCage Geocoding API to fetch coordinates for area descriptions.
- Implemented a function `get_coordinates_opencage(area_name, api_key)` to fetch coordinates using OpenCage API.
- Added API quota check to monitor remaining requests.

### 2. Normalizing Area Descriptions
- Implemented a function `normalize_area_description(area_desc)` to clean and normalize area descriptions for improved geocoding accuracy.

### 3. Caching Geocoding Results
- Added a cache mechanism to store geocoding results locally to avoid redundant requests and manage API quota efficiently.
- Implemented a function `get_coordinates_with_cache(area_name, api_key)` to fetch coordinates and store them in a cache.

### 4. Improved Error Handling
- Enhanced error handling for geocoding requests and data retrieval.
- Implemented fallback strategies to handle failed geocoding attempts by using default coordinates.

### 5. Streamlining Marker Placement
- Simplified the logic for adding markers to the map.
- Ensured markers are displayed for all records, with color coding to differentiate between successfully geocoded locations and fallbacks.

## Future Work

### 1. Further Optimize Geocoding
- Explore additional geocoding services to complement OpenCage and improve reliability.
- Implement more advanced normalization techniques for area descriptions to handle a wider variety of formats.

### 2. Enhanced Caching
- Store cached geocoding results in a persistent storage (e.g., file or database) to retain data between sessions.
- Implement mechanisms to refresh cached data periodically.

### 3. User Interface Improvements
- Enhance the user interface with more options for filtering and visualizing alerts.
- Add functionalities to interact with map markers for more detailed information.

### 4. Performance Optimization
- Optimize data retrieval and processing to handle larger datasets more efficiently.
- Explore asynchronous processing for geocoding requests to improve performance.

### 5. Documentation and Testing
- Add comprehensive documentation for all functions and modules.
- Implement unit tests and integration tests to ensure the robustness of the tool.

## Usage

1. Clone the repository:
    ```sh
    git clone https://github.com/your-repository/ipaws-alert-tool.git
    ```
2. Navigate to the project directory:
    ```sh
    cd ipaws-alert-tool
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Run the Streamlit app:
    ```sh
    streamlit run ipaws_alert_tool.py
    ```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

