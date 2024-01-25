from utility import api_request
import datetime
import requests
import numpy as np
import pytz

import sqlite3
import pandas as pd

# url = 'https://api.openweathermap.org/data/2.5/weather'
# params = {'APPID': "37012b8dfefdabc9cd6f71e8d652545d", 'q': 'Los Angeles', 'units': 'celsius'}
# response = requests.get(url, params=params)
# weather = response.json()
# print(weather)

# # tempmax, tempmin, temp, feelslikemax, feelslikemin, feelslike, humidity, is_rain, uvindex, conditions, description

# print(weather_json)
# print()
# print()
# print()
# print(weather_json['main']['temp_max']) # tempmax
# print(weather_json['main']['temp_min']) # tempmin
# print(weather_json['main']['temp']) # temp
# print(weather_json['main']['feels_like']) # feelslikemax
# print(weather_json['main']['feels_like']) # feelslikemin
# print(weather_json['main']['feels_like']) # feelslike
# print(weather_json['main']['humidity']) # humidity
# print(weather_json['main']['humidity']) # is_rain


# Get rid of uvindex, conditions, description, feelslikemax, feelslikemin, 
# KEEP: tempmax, tempmin, temp, feelslike, humidity


## weekday, hour, is_am, is_work, time_of_day_bin, is_weekend, avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6, hour_weekend_interaction
# weather_range, hour_rain_interaction, cluster_condition

# print(datetime.datetime.today().weekday()) # weekday
# print(datetime.datetime.now().hour) # hour
# print(datetime.datetime.now().day)
# print(datetime.datetime.now().minute)


# Get current time in UTC
# utc_now = datetime.datetime.utcnow()

# # Set UTC timezone
# utc_timezone = pytz.timezone('UTC')
# utc_now = utc_timezone.localize(utc_now)

# # Convert to Pacific Time
# pt_timezone = pytz.timezone('America/Los_Angeles')
# pt_now = utc_now.astimezone(pt_timezone).hour
# print(pt_now)


# url = 'https://api.openweathermap.org/data/2.5/weather'

# params = {'APPID': "37012b8dfefdabc9cd6f71e8d652545d", 'q': 'Los Angeles', 'units': 'farenheit'}
# response = requests.get(url, params=params)
# weather = response.json()

# print(weather)

# tempmax = weather['main']['temp_max'] # tempmax
# tempmin = weather['main']['temp_min'] # tempmin
# temp = weather['main']['temp'] # temp

# temp_celsius = round(temp - 273.15, 1)
# print(temp_celsius)



def calculate_avg_time_occupancy_previous_parkers(space_id: str):

    '''
    Takes a list of Space ID and calculates the avg time that the previous 3 and 6 people were parked
    
    '''
    
    # avg_time_in_occupancy_past_3 and avg_time_in_occupancy_past_6
    parking_meter_inventory_api_df = api_request(api_endpoint="e7h6-4a3e", api_name= 'socrata')

    # checking for empty str
    if not space_id:
        return -1
    
    # calculating avg time
    # parking_meter_inventory_api_df
    # df['avg_time_in_occupancy_past_3'] = df.groupby('SpaceID')['time_in_occupancy_state'].rolling(window=3).mean().reset_index(level=0, drop=True)
    # df['avg_time_in_occupancy_past_3'] = df.groupby('SpaceID')['avg_time_in_occupancy_past_3'].bfill()


#     avg_time_window_3 = parking_meter_inventory_api_df[parking_meter_inventory_api_df['spaceid'] == space_id]#.rolling(window=3).mean()

#     return parking_meter_inventory_api_df['spaceid'].duplicated().sum()




# print(collecting_model_features(api_endpoint_weather='37012b8dfefdabc9cd6f71e8d652545d'))
    

conn = sqlite3.connect('/Users/juanherrera/Desktop/traffic.db')
cursor = conn.cursor()
q = '''SELECT *
        FROM metered_parking_inventory  mi
        '''

inventory_df = pd.read_sql_query(q, conn)

inventory_df.to_csv("inventory_df.csv", index=False)






    





    





    


