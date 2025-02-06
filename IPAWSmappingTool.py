import pandas as pd # type: ignore
import folium
from folium.plugins import MarkerCluster
from folium import plugins
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import webbrowser

# Get a list of CSV files in the current directory
files = os.listdir()
csv_files = [file for file in files if file.endswith('_for_mapping.csv')]

# Sort files based on modification time
csv_files.sort(key=lambda x: os.path.getmtime(x))

# Get the most recent file
last_csv_file = csv_files[-1]

# Verify modification time of the selected file
selected_modification_time = os.path.getmtime(last_csv_file)

# Read the CSV file into a DataFrame
ipaws_df = pd.read_csv(last_csv_file)

# Replace null values with "None"
ipaws_df = ipaws_df.astype(object)
ipaws_df.fillna('None', inplace=True)

def parse_date(date_str):
    date_str = date_str.split('T')[0]  # Extract only the date part
    return datetime.strptime(date_str, '%Y-%m-%d').date()

state_code_to_name = {
    '02': 'Alaska', '01': 'Alabama', '05': 'Arkansas', '60': 'American Samoa', '04': 'Arizona',
    '06': 'California', '08': 'Colorado', '09': 'Connecticut', '11': 'District of Columbia', '10': 'Delaware',
    '12': 'Florida', '13': 'Georgia', '66': 'Guam', '15': 'Hawaii', '19': 'Iowa', '16': 'Idaho',
    '17': 'Illinois', '18': 'Indiana', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '25': 'Massachusetts',
    '24': 'Maryland', '23': 'Maine', '26': 'Michigan', '27': 'Minnesota', '29': 'Missouri', '28': 'Mississippi',
    '30': 'Montana', '37': 'North Carolina', '38': 'North Dakota', '31': 'Nebraska', '33': 'New Hampshire',
    '34': 'New Jersey', '35': 'New Mexico', '32': 'Nevada', '36': 'New York', '39': 'Ohio', '40': 'Oklahoma',
    '41': 'Oregon', '42': 'Pennsylvania', '72': 'Puerto Rico', '44': 'Rhode Island', '45': 'South Carolina',
    '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah', '51': 'Virginia', '78': 'Virgin Islands',
    '50': 'Vermont', '53': 'Washington', '55': 'Wisconsin', '54': 'West Virginia', '56': 'Wyoming', '81': 'Baker Island',
    '64': 'Federated States of Micronesia', '84': 'Howland Island', '86': 'Jarvis Island', '67': 'Johnston Atoll',
    '89': 'Kingman Reef', '68': 'Marshall Islands', '71': 'Midway Islands', '76': 'Navassa Island',
    '69': 'Northern Mariana Islands', '70': 'Palau', '95': 'Palmyra Atoll', '74': 'U.S. Minor Outlying Islands',
    '79': 'Wake Island', '57': 'Pacific coast from Washington to California', '58': 'Alaskan coast',
    '59': 'Hawaiian coast', '61': 'American Samoa waters', '65': 'Mariana Islands waters (including Guam)',
    '73': 'Atlantic coast from Maine to Virginia',
    '75': 'Atlantic coast from North Carolina to Florida, and the coasts of Puerto Rico and Virgin Islands',
    '77': 'Gulf of Mexico', '91': 'Lake Superior', '92': 'Lake Michigan', '93': 'Lake Huron',
    '94': 'St. Clair River, Detroit River, and Lake St. Clair', '96': 'Lake Erie', '97': 'Niagara River and Lake Ontario',
    '98': 'St. Lawrence River'
}

state_coordinates = {
    "Alaska": (61.0167, -149.5333),
    "Alabama": (32.8067, -86.7911),
    "Arkansas": (34.7998, -92.1999),
    "American Samoa": (-14.3064, -170.6950),
    "Arizona": (34.0489, -111.0937),
    "California": (36.7783, -119.4179),
    "Colorado": (39.5501, -105.7821),
    "Connecticut": (41.6032, -73.0877),
    "District of Columbia": (38.9072, -77.0369),
    "Delaware": (38.9108, -75.5277),
    "Florida": (27.9944, -81.7603),
    "Georgia": (32.1656, -82.9001),
    "Guam": (13.4443, 144.7937),
    "Hawaii": (19.8968, -155.5828),
    "Iowa": (41.8780, -93.0977),
    "Idaho": (44.0682, -114.7420),
    "Illinois": (40.6331, -89.3985),
    "Indiana": (40.5512, -85.6024),
    "Kansas": (39.0558, -96.8164),
    "Kentucky": (37.6690, -84.6514),
    "Louisiana": (31.1801, -91.8749),
    "Massachusetts": (42.2596, -71.8083),
    "Maryland": (39.0458, -76.6413),
    "Maine": (45.3695, -69.2428),
    "Michigan": (44.3467, -85.4102),
    "Minnesota": (46.2807, -94.3053),
    "Missouri": (38.6468, -92.6048),
    "Northern Mariana Islands": (15.0979, 145.6739),
    "Mississippi": (32.7364, -89.6678),
    "Montana": (46.9219, -110.4544),
    "North Carolina": (35.6411, -79.8431),
    "North Dakota": (47.5289, -99.7840),
    "Nebraska": (41.5378, -99.7951),
    "New Hampshire": (43.6805, -71.5811),
    "New Jersey": (40.1907, -74.6728),
    "New Mexico": (34.4071, -106.1126),
    "Nevada": (38.4192, -117.1219),
    "New York": (42.9538, -75.5268),
    "Ohio": (40.1904, -82.6693),
    "Oklahoma": (35.3098, -98.7166),
    "Oregon": (44.1419, -120.5381),
    "Pennsylvania": (40.9946, -77.6047),
    "Puerto Rico": (18.2208, -66.5901),
    "Rhode Island": (41.5827, -71.5065),
    "South Carolina": (33.9169, -80.8964),
    "South Dakota": (44.4443, -100.2263),
    "Tennessee": (35.8580, -86.3505),
    "Texas": (31.4757, -99.3312),
    "Utah": (39.3055, -111.6703),
    "Virginia": (37.7693, -78.1700),
    "Virgin Islands": (18.0001, -64.8199),
    "Vermont": (44.0687, -72.6658),
    "Washington": (47.4009, -121.4905),
    "Wisconsin": (44.6243, -89.9941),
    "West Virginia": (38.4912, -80.9540),
    "Wyoming": (42.9957, -107.5512),
    "Baker Island": (0.2232, -176.4760),
    "Federated States of Micronesia": (7.4256, 150.5508),
    "Howland Island": (0.8067, -176.6183),
    "Jarvis Island": (-0.3764, -160.0190),
    "Johnston Atoll": (16.7290, -169.5199),
    "Kingman Reef": (6.4125, -162.3750),
    "Marshall Islands": (7.1315, 171.1845),
    "Midway Islands": (28.2013, -177.3759),
    "Navassa Island": (18.4100, -75.0324),
    "Northern Mariana Islands waters (including Guam)": (15.0979, 145.6739),
    "Palau": (7.5150, 134.5825),
    "Palmyra Atoll": (5.8830, -162.0719),
    "U.S. Minor Outlying Islands": (-12.2333, -77.3000),
    "Wake Island": (19.2928, 166.6188),
    "Pacific coast from Washington to California": (39.0000, -123.0000),
    "Alaskan coast": (61.0000, -150.0000),
    "Hawaiian coast": (21.0000, -157.5000),
    "American Samoa waters": (-14.3064, -170.6950),
    "Mariana Islands waters (including Guam)": (15.0979, 145.6739),
    "Atlantic coast from Maine to Virginia": (38.0000, -72.0000),
    "Atlantic coast from North Carolina to Florida, and the coasts of Puerto Rico and Virgin Islands": (29.0000, -82.0000),
    "Gulf of Mexico": (26.3526, -91.4767),
    "Lake Superior": (47.7528, -87.5839),
    "Lake Michigan": (44.0000, -87.0000),
    "Lake Huron": (45.0000, -83.0000),
    "St. Clair River, Detroit River, and Lake St. Clair": (42.3601, -82.1278),
    "Lake Erie": (42.0000, -81.0000),
    "Niagara River and Lake Ontario": (43.0000, -79.0000),
    "St. Lawrence River": (45.0000, -75.0000)
}

def create_map(df):
    mymap = folium.Map([39.8283, -98.5795], zoom_start=3)
    marker_cluster = MarkerCluster().add_to(mymap)
    
    # Create a new column 'State' in the DataFrame and initialize it with None
    df['State'] = None
    for index, row in df.iterrows():
        # Extract the first two digits after the leading zero of geocode_1 as state code
        geocode = str(row['geocode_1'])
        state_code = geocode[0:2]  
        # Lookup state name from state code dictionary
        state_name = state_code_to_name.get(state_code)
        if state_name is None:
            continue  # Skip if state code is not found
        
        # Retrieve latitude and longitude coordinates for the middle of the state
        state_coord = state_coordinates[state_name]

        # Update the 'State' column in the DataFrame
        df.loc[index, 'State'] = state_name

        # Create marker with popup
        marker_text = f"""
        <div style="max-height: 300px; max-width: 300px; overflow-y: scroll;">
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid black;">
                    <th style="text-align: left; font-weight: bold;">Location Name:</th>
                    <td>{state_name}</td>
                </tr>
                {''.join([f"<tr style='border-bottom: 1px solid black;'><th style='text-align: left;'>{col.capitalize()}:</th><td>{row[col]}</td></tr>" for col in df.columns if pd.notnull(row[col])])}
            </table>
        </div>
        """

        marker = folium.Marker(
            location=state_coord,
            popup=f'{marker_text}'
        )

        # Add marker to marker cluster
        marker.add_to(marker_cluster)

    return mymap, df  # Return both the map and the modified DataFrame


column_aliases = {
    'sent' : '''sent
The date and time from the <sent> element when the alert message was sent.''',
    'event' : '''event
The text from the <event> element denoting the type of the subject event associated with the alert message.''',
    'urgency' : '''urgency
The code from the <urgency> element denoting the urgency associated with the subject event of the alert message (See CAPv1.2 standard for code values).''',
    'category' : '''category
The code from the <category> element denoting the category associated with the subject event of the alert message (See CAPv1.2 standard for code values).''',
    'blockchannel' : '''blockchannel
one of the following four values will restrict a message dissemination channel: 'CMAS', 'EAS', 'NWEM', 'PUBLIC'. A single or multiple channels can be blocked'''
}

categorical_filter_columns = ['event'] #add more columns from column_aliases as needed (except for sent and blockchannel)

start_date_default = parse_date(ipaws_df[column_aliases['sent']].min())
end_date_default = parse_date(ipaws_df[column_aliases['sent']].max())

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Iterate through categorical columns and generate Dropdown components
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Label("Filtering Options", style={'display': 'block', 'margin-bottom': '0.5rem', 'font-weight': 'bold', 'text-align': 'center'}),
                html.Label("Select Date Range:", style={'display': 'block', 'margin-bottom': '0.5rem'}),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=start_date_default,
                    end_date=end_date_default,
                    display_format='YYYY-MM-DD',
                    className="mb-3",
                ),
                *[html.Div([
                    html.Label(f"{col.capitalize()}:"),
                    dcc.Dropdown(
                        id=f'{col}-dropdown',
                        options=[{'label': val, 'value': val} for val in ipaws_df[column_aliases[col]].unique()],
                        value=None,
                        multi=True  # Allow multiple selections
                    )
                ]) for col in categorical_filter_columns],
                html.Div([
                    html.Label("Block Channel:"),
                    dcc.Dropdown(
                        id='blockchannel-dropdown',
                        options=[
                            #options: without EAS, without CMAS, without EAS or CMAS
                            {'label': 'EAS', 'value': 'EAS'}, 
                            {'label': 'CMAS', 'value': 'CMAS'},
                        ],
                        value=None,
                        multi=True  # Allow multiple selections
                    )
                ]),
                html.Div([
                    html.Label("State:"),
                    dcc.Dropdown(
                        id='state-dropdown',
                        options=[{'label': state_name, 'value': state_name} for state_name in state_code_to_name.values()],
                        value=None,
                        multi=True  # Allow multiple selections
                    )
                ]),
            ], style={'padding': '10px', 'background-color': '#f2f2f2'}),  # Apply background color inside the border
        ], style={'border': '1px solid #ccc', 'float': 'left', 'width': '20%'}),
        html.Div(id='map-container', style={'float': 'left', 'width': '80%'}, children=[
            html.Iframe(id='map', width='100%', height='600', style={'overflow': 'hidden'})  # Remove scroll bars
        ]),
    ]),
])

# Initialize the map and marker cluster
mymap = folium.Map([39.8283, -98.5795], zoom_start=3)
marker_cluster = MarkerCluster().add_to(mymap)
mymap, ipaws_df_with_state = create_map(ipaws_df)

# Define callback
@app.callback(
    Output('map', 'srcDoc'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('state-dropdown', 'value'),
     Input('blockchannel-dropdown', 'value')]  # Added input for the blockchannel dropdown
    + [Input(f"{col}-dropdown", "value") for col in categorical_filter_columns]
)
def update_map(start_date, end_date, selected_states, selected_blockchannels, *dropdown_values):

    # Convert date strings to datetime objects
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    # Filter DataFrame based on date range
    filtered_df = ipaws_df_with_state[
        (ipaws_df_with_state[column_aliases['sent']].apply(parse_date) >= start_date) &
        (ipaws_df_with_state[column_aliases['sent']].apply(parse_date) <= end_date)
    ]

    # Apply categorical filters
    for column, values in zip(categorical_filter_columns, dropdown_values):
        if values:
            # Convert single selected value to a list
            if isinstance(values, str):
                values = [values]
            filtered_df = filtered_df[filtered_df[column_aliases[column]].isin(values)]

    if selected_states:
        filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]

    if selected_blockchannels is not None:
        for option in selected_blockchannels:
            if option == 'EAS':
                filtered_df = filtered_df[~filtered_df[column_aliases['blockchannel']].str.contains('EAS', regex=True)]
            elif option == 'CMAS':
                filtered_df = filtered_df[~filtered_df[column_aliases['blockchannel']].str.contains('CMAS', regex=True)]

    # Update the map using the modified DataFrame
    return create_map(filtered_df)[0]._repr_html_()

webbrowser.open("http://127.0.0.1:8050/")

# Run the Dash app
if __name__ == '__main__':
    app.run_server()

