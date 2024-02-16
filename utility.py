import sqlite3
import pandas as pd
import numpy as np
import pickle as pk
from sodapy import Socrata
# from pw import app_token, username, password, weather_key_api_endpoint, bing_map_api_endpoint, parking_meter_occupancy_api_endpoint
import requests
import streamlit as st
from datetime import datetime
import pytz  # for working with time zones
from math import radians, sin, cos, sqrt, atan2
# import webbrowser
from streamlit.components.v1 import html
from streamlit_js_eval import  get_geolocation



app_token = st.secrets['app_token']
username = st.secrets['username']
password = st.secrets['password']
weather_key_api_endpoint = st.secrets['weather_key_api_endpoint']
bing_map_api_endpoint = st.secrets['bing_map_api_endpoint']
parking_meter_occupancy_api_endpoint = st.secrets['parking_meter_occupancy_api_endpoint']

inventory_df = pd.read_csv("inventory_df.csv")



class preprocessing:

    @staticmethod
    def dict_to_columns_lat_long(dict_):
        return dict_['latitude'], dict_['longitude'] 


def api_request(api_endpoint: str, api_name: str) -> pd.DataFrame:
    '''
    This is the function that makes API requests

    Ex: api_request(api_endpoint=parking_meter_inventory_api_endpoint, api_name='Socrata')

    Ex 2: df = api_request(api_endpoint=parking_meter_occupancy_api_endpoint, api_name='Socrata')
          ingests_parking_meter_live_data_to_parking_meter_occupancy_live_t(df) 

    returns: df - which contains API data
    '''
    if api_name.lower().strip() == 'socrata':

        client = Socrata('data.lacity.org',
                 app_token,
                 username=username,
                 password=password)
        
        result = client.get(api_endpoint, limit=50000)

        df = pd.DataFrame.from_records(result)

        if api_endpoint == 'e7h6-4a3e':
            df['eventtime'] = pd.to_datetime(df['eventtime']).dt.tz_localize('UTC')

        return df
    
    elif api_name.lower().strip() == 'weather':

        url = 'https://api.openweathermap.org/data/2.5/weather'
        params = {'APPID': api_endpoint, 'q': 'Los Angeles', 'units': 'celsius'}
        response = requests.get(url, params=params)
        weather = response.json()
        
        temp = weather['main']['temp'] - 273.15
        condition = weather['weather'][0]['description']
        df = pd.DataFrame({'condition': condition, 'temp': temp, 'eventtime_utc': datetime.now(pytz.utc).isoformat()}, index=[1])

        return df #, weather #pd.DataFrame({'condition': condition, 'temp': temp}, index=[1])




# def ingests_parking_meter_live_data_to_parking_meter_occupancy_live_t(df: pd.DataFrame) -> None:
#     '''
#     This functions takes a dataframe collected from the parking meter live API endpoint data and stores
#     it in the parking_meter_occupancy_live table in the database

#     returns: None
    
#     '''
#     try:
#         conn = sqlite3.connect('/Users/juanherrera/Desktop/traffic.db')
#         cursor = conn.cursor()
#         for _, row in df.iterrows():
#             eventtime_string = row['eventtime'].strftime('%Y-%m-%d %H:%M:%S')
#             space_id = row['spaceid']

#             # Check if the record already exists
#             select_query = "SELECT COUNT(*) FROM parking_meter_occupancy_live WHERE space_id = ? AND eventtime_utc = ?"
#             cursor.execute(select_query, (space_id, eventtime_string))
#             count = cursor.fetchone()[0]

#             if count == 0:
#                 # The record doesn't exist, so insert it
#                 insert_query = "INSERT INTO parking_meter_occupancy_live (space_id, eventtime_utc, occupancy_state) VALUES (?, ?, ?);"
#                 cursor.execute(insert_query, (space_id, eventtime_string, row['occupancystate']))

#             else:
#                 pass

#         conn.commit()

#         #     insert_query = "INSERT INTO parking_meter_occupancy_live (space_id, eventtime_utc, occupancy_state) VALUES (?, ?, ?);"
#         #     cursor.execute(insert_query, (row['spaceid'], eventtime_string, row['occupancystate']))
#         # conn.commit()
    
#     except:
#         raise Exception("Data didn't make it to database")
#     print('Success')

    

# def ingests_parking_meter_inventory_to_metered_parking_inventory_t(df: pd.DataFrame) -> None:
#     '''
#     This functions takes a dataframe collected from the parking meter inventory API endpoint data and stores
#     it in the metered_parking_inventory table in the database

#     returns: None
    
#     '''
#     try:
#         conn = sqlite3.connect('/Users/juanherrera/Desktop/traffic.db')
#         cursor = conn.cursor()
#         for _, row in df.iterrows():
#             insert_query = '''INSERT INTO metered_parking_inventory
#                                         (space_id, block_face, meter_type, rate_type, rate_range, metered_time_limit, lat, long) 
#                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''
#             cursor.execute(insert_query, (row['spaceid'], row['blockface'], row['metertype'], 
#                                           row['ratetype'], row['raterange'], row['timelimit'],
#                                           preprocessing.dict_to_columns_lat_long(row['latlng'])[0],
#                                           preprocessing.dict_to_columns_lat_long(row['latlng'])[1]
#                                           ))
#         conn.commit()
    
#     except:
#         raise Exception("Data didn't make it to database")
#     print('Success')
    

# def ingests_weather_data_to_weather_t(df: pd.DataFrame) -> None:
#     '''
#     This function takes a dataframe containing the weather data and stores it in the database

#     returns: None
    
#     '''
#     try:
#         conn = sqlite3.connect('/Users/juanherrera/Desktop/traffic.db')
#         cursor = conn.cursor()
#         insert_query = "INSERT INTO weather (eventtime_utc, temperature, condition) VALUES (?, ?, ?);"
#         cursor.execute(insert_query, (datetime.now(pytz.utc).isoformat(), df['temp'].values[0], df['condition'].values[0]))
#         conn.commit()
    
#     except:
#         raise Exception("Data didn't make it to database")
#     print('Success')

####################
# Bing Map Functions
####################

def get_coordinates(place: str) -> str:
    '''
    
    Inputs a place
    Ex: "USC Marshall School of Business"
    
    Ouputs the coodinates as a string
    Ex: '34.01878357,-118.28292847'
    
    '''
    
    # Replace with your Bing Maps API key
    bing_maps_key = bing_map_api_endpoint

    # Set the location to query
    location = place

    # Construct the URL for the request
    url = f"https://dev.virtualearth.net/REST/v1/Locations?q={location}&key={bing_maps_key}"

    # Make the request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Extract the latitude and longitude
        latitude = data["resourceSets"][0]["resources"][0]["point"]["coordinates"][0]
        longitude = data["resourceSets"][0]["resources"][0]["point"]["coordinates"][1]

        return f' {latitude},{longitude} '.strip()
    else:
        raise Exception("Could not parse coordinates")



def calculates_distance_and_driving_time_from_point_a_to_point_b(from_: str, to: str) -> tuple:
    
    '''
    This function takes two strings that represent the point 1 place and the point 2 place
    It calculates how long it'll take to drive there and the distance in kilometers
    
    Ex: from: (long, lat), to: (long, lat)
    
    and returns
    Ex: (11,234, 27)
    
    '''
    
    # Replace with your Bing Maps API Key
    api_key = bing_map_api_endpoint

    # Specify the start and end coordinates (latitude, longitude)
    start_coordinates = from_ 
    end_coordinates = to   # Los Angeles, CA

    # Build the URL for the Bing Maps API request
    base_url = 'https://dev.virtualearth.net/REST/v1/Routes/Driving'
    params = {
        'wayPoint.1': start_coordinates,
        'wayPoint.2': end_coordinates,
        'key': api_key
    }

    # Make the API request
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # # Check for a successful response
    if response.status_code == 200:
        # Extract the driving distance and duration (in seconds)
        if 'resourceSets' in data and len(data['resourceSets']) > 0 and 'resources' in data['resourceSets'][0]:
            route = data['resourceSets'][0]['resources'][0]
            driving_distance = route['travelDistance']
            driving_duration_seconds = route['travelDurationTraffic']  # Includes traffic data
            driving_duration_minutes = driving_duration_seconds / 60  # Convert to minutes
            return driving_distance, driving_duration_minutes
        else:
            raise Exception("No route information found.")
    else:
        raise Exception(f"Error: {response.status_code} - {data['errorDetails'][0]['message']}")




##### Haversine function

def haversine(lat1, lon1, lat2, lon2) -> int:
    '''

    This function takes two coordinates and calculates the haversine distance in meters


    returns: int
    '''

    # Radius of the Earth in meters
    R = 6371000.0

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Calculate the distance in meters
    distance = R * c

    return distance



###############


def fetch_autocomplete_suggestions(query, user_location=None, 
                                   user_circular_map_view=None, 
                                   user_map_view=None, 
                                   max_results=10, 
                                   include_entity_types="Place,Address,Business", 
                                   culture="en-US", 
                                   user_region="US", 
                                   country_filter=None) -> list:
    
    '''
    takes a location (query) calculates the the suggested nearby places using bing's api and returns it as a list

    returns: list
    
    '''
    
    url = "http://dev.virtualearth.net/REST/v1/Autosuggest"

    params = {
        "query": query,
        "key": bing_map_api_endpoint
    }

    if user_location is not None:
        params["userLocation"] = user_location

    if user_circular_map_view is not None:
        params["userCircularMapView"] = user_circular_map_view

    if user_map_view is not None:
        params["userMapView"] = user_map_view

    params["maxResults"] = max_results
    params["includeEntityTypes"] = include_entity_types
    params["culture"] = culture
    params["userRegion"] = user_region

    if country_filter is not None:
        params["countryFilter"] = country_filter

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        
        suggestions_list = []
        
        
        for i in response.json()["resourceSets"][0]["resources"][0]['value']:
            try:
                suggestions_list.append(i['name'] + ', ' +i['address']['formattedAddress'])
            except:
                suggestions_list.append(i['address']['formattedAddress'])
        
        
        return suggestions_list #response.json()#["resourceSets"][0]["resources"][0]#["suggestions"]
    else:
        raise Exception("Failed to fetch autocomplete suggestions from Bing Maps API. Error code: {}".format(response.status_code))




def joins_street_parking_inventory_with_live_api_data() -> pd.DataFrame:
    '''
    when this function is called, it pings the live paking meter API and joins it with the parking meter inventory
    it then performs some cleaning and returns everything as a dataframe

    returns: df
    
    '''
    # conn = sqlite3.connect('/Users/juanherrera/Desktop/traffic.db')
    # cursor = conn.cursor()
    # q = '''SELECT *
    #         FROM metered_parking_inventory  mi
    #         '''


    api_df = api_request(api_endpoint=parking_meter_occupancy_api_endpoint, api_name='Socrata')
    api_weather_df = api_request(api_endpoint=weather_key_api_endpoint, api_name='weather')
    
    # ingests_parking_meter_live_data_to_parking_meter_occupancy_live_t(api_df) 
    # ingests_weather_data_to_weather_t(api_weather_df)

    # inventory_df = pd.read_sql_query(q, conn)
    final_df = pd.merge(api_df, inventory_df, how='inner', left_on='spaceid', right_on='space_id')

    final_df['lat'] = [float(i) for i in final_df['lat']]
    final_df['lon'] = [float(i) for i in final_df['long']]
    return final_df


#############################
######### MODEL FEATURES
##################################

# Read data from the pickle file
with open('mapping_dictionary.pkl', 'rb') as pickle_file:
    mapping_dict = pk.load(pickle_file)


coordinates_mapping_df = pd.read_csv('coordinates_mapping_compressed.csv')
avg_time_in_occupancy_matrix = pd.read_csv("avg_time_in_occupancy_matrix.csv")

def transform_ml_model_features_input(SpaceID: str,
                                    OccupancyState: str,
                                    block_face: str,
                                    meter_type: str,
                                    rate_type: str,
                                    rate_range: str,
                                    metered_time_limit: str,
                                    day: int,
                                    tempmax: float,
                                    tempmin: float,
                                    temp: float,
                                    feelslike: float,
                                    humidity: float,
                                    weekday: int,
                                    hour: int,
                                    minute: int,
                                    is_am: int,
                                    is_work: int,
                                    time_of_day_bin: str,
                                    is_weekend: int,
                                    avg_time_in_occupancy_past_3: float,
                                    avg_time_in_occupancy_past_6: float,
                                    hour_weekday_interaction: int,
                                    weather_range: float, 
                                    lat: float,
                                    long: float
                                    ):
    
    '''

    This functions takes all the raw inputs which are then transformed and returned as an array that will help our model make predictions

    These are the encoded features:
    dict_keys(['SpaceID', 'OccupancyState', 'block_face', 'is_am', 'time_of_day_bin', 'conditions', 'description', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit'])
    
    
    '''
    spaceid_feature = mapping_dict['SpaceID'][SpaceID]
    occupancy_state_feature = mapping_dict['OccupancyState'][OccupancyState]
    block_face_feature = mapping_dict['block_face'][block_face]
    time_of_day_bin_feature = mapping_dict['time_of_day_bin'][time_of_day_bin]
    meter_type_feature = mapping_dict['meter_type'][meter_type]
    rate_type_feature = mapping_dict['rate_type'][rate_type]
    rate_range_feature = mapping_dict['rate_range'][rate_range]
    metered_time_limit_feature = mapping_dict['metered_time_limit'][metered_time_limit]


    # cluster
    cluster = coordinates_mapping_df[(coordinates_mapping_df['lat'] == lat) & (coordinates_mapping_df['long'] == long)]['cluster_coordinates'].unique()[0]


    features_lst = np.array([[spaceid_feature, occupancy_state_feature, block_face_feature, meter_type_feature, rate_type_feature, rate_range_feature, metered_time_limit_feature,
                             day, tempmax, tempmin, temp, feelslike, humidity, weekday, hour, minute, is_am, is_work, time_of_day_bin_feature, is_weekend, avg_time_in_occupancy_past_3,
                             avg_time_in_occupancy_past_6, hour_weekday_interaction, weather_range, cluster]])
    

    return features_lst




def collecting_model_features(api_endpoint_weather: str) -> dict: 
    '''
    This function calls the weather API to collect all the weather data that the ML model needs and it also calculates the time data

    the output of this model will be an array with the multiple features that the model needs

    the output from this function will be then fed to the ml_model_features_input function that will encode the features and feed it directly to the model
    
    '''

    # Weather Features
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'APPID': api_endpoint_weather, 'q': 'Los Angeles', 'units': 'celsius'}
    response = requests.get(url, params=params)
    weather = response.json()
    
    tempmax_kelvin = weather['main']['temp_max'] # tempmax
    tempmin_kelvin = weather['main']['temp_min'] # tempmin
    temp_kelvin = weather['main']['temp'] # temp

    tempmax = round(tempmax_kelvin - 273.15, 1) # to celsius
    tempmin = round(tempmin_kelvin - 273.15, 1) # to celsius
    temp = round(temp_kelvin - 273.15, 1) # to celsius


    feelslike_kelvin = weather['main']['feels_like'] # feelslike
    feelslike = round(feelslike_kelvin - 273.15, 1) # to celsius
    humidity = weather['main']['humidity'] # humidity
    weather_range = tempmax - tempmin # weather_range
    

    # Time Features
    day = datetime.now().day # day
    weekday = datetime.today().weekday() #  weekday
    hour = datetime.now().hour # hour
    minute = datetime.now().minute # minute

    # time_of_day_bin
    time_of_day_bin = '' 
    afternoon_bin_lst = [i for i in range(12,18)]
    evening_bin_lst = [i for i in range(18,24)]
    night_bin_lst = [i for i in range(0, 6)]

    if hour in afternoon_bin_lst:
        time_of_day_bin = 'afternoon'
    elif hour in evening_bin_lst:
        time_of_day_bin = 'evening'
    elif hour in night_bin_lst:
        time_of_day_bin = 'night'
    else:
        time_of_day_bin = 'morning'

    # is_weekend
    is_weekend = 0 
    if weekday in [5,6]:
        is_weekend = 1

    # is_am
    is_am = 0
    if hour in [i for i in range(0,12)]:
        is_am = 1

    # is_work
    is_work = 0
    if hour in [i for i in range(5,20)]:
        is_work = 1

    # hour_weekday_interaction
    hour_weekday_interaction = weekday * hour

    final_dict = {'day': day, 'tempmax': tempmax, 'tempmin': tempmin, 'temp':temp, 
                  'feelslike': feelslike, 'humidity': humidity, 'weekday': weekday, 
                  'hour': hour, 'minute': minute, 'is_am': is_am, 'is_work': is_work,
                   'time_of_day_bin': time_of_day_bin, 'is_weekend':is_weekend, 
                   'hour_weekday_interaction': hour_weekday_interaction, 
                   'weather_range': weather_range}

    return final_dict



def calculate_avg_time_occupancy_previous_parkers(space_id: str):

    '''
    Takes a list of Space ID and calculates the avg time that the previous 3 and 6 people were parked
    
    '''

    # calculating avg time
    day = datetime.now().day 
    
    # checking for empty str
    if not space_id:
        avg_time_in_occupancy_past_3 = avg_time_in_occupancy_matrix[avg_time_in_occupancy_matrix['day'] == day]['avg_time_in_occupancy_past_3'].median()
        avg_time_in_occupancy_past_6 = avg_time_in_occupancy_matrix[avg_time_in_occupancy_matrix['day'] == day]['avg_time_in_occupancy_past_6'].median()
        return avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6
    
    
    # calculating avg time
    day = datetime.now().day 

    # Mapping the value to its encoded value
    space_id_encoded = mapping_dict['SpaceID'][space_id]

    avg_time_in_occupancy_past_3 = avg_time_in_occupancy_matrix[(avg_time_in_occupancy_matrix['SpaceID'] == space_id_encoded) & (avg_time_in_occupancy_matrix['day'] == day)]['avg_time_in_occupancy_past_3'].values[0]
    avg_time_in_occupancy_past_6 = avg_time_in_occupancy_matrix[(avg_time_in_occupancy_matrix['SpaceID'] == space_id_encoded) & (avg_time_in_occupancy_matrix['day'] == day)]['avg_time_in_occupancy_past_6'].values[0]


    return avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6


# Opens up new tab with the right address

def open_google_maps(from_place, to_place):
    google_maps_url = f"https://www.google.com/maps/dir/{from_place}/{to_place}"
    # webbrowser.open_new_tab(google_maps_url)
    open_script= """
        <script type="text/javascript">
            window.open('%s', '_blank').focus();
        </script>
    """ % (google_maps_url)
    html(open_script)

    
def get_user_loc():
    location = get_geolocation()
    return location



print(avg_time_in_occupancy_matrix[avg_time_in_occupancy_matrix['day'] == datetime.now().day]['avg_time_in_occupancy_past_3'].median())

