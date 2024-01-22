from utility import api_request
import datetime
import requests
# weather_json = api_request("37012b8dfefdabc9cd6f71e8d652545d", 'weather')

url = 'https://api.openweathermap.org/data/2.5/weather'
params = {'APPID': "37012b8dfefdabc9cd6f71e8d652545d", 'q': 'Los Angeles', 'units': 'celsius'}
response = requests.get(url, params=params)
weather = response.json()
print(weather)

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

print(datetime.datetime.today().weekday()) # weekday
print(datetime.datetime.now().hour) # hour



# WIP

def collecting_model_features(api_endpoint_weather: str):
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
    
    tempmax = weather_json['main']['temp_max'] # tempmax
    tempmin = weather_json['main']['temp_min'] # tempmin
    temp = weather_json['main']['temp'] # temp
    feelslikemax = weather_json['main']['feels_like'] # feelslikemax
    feelslikemin = weather_json['main']['feels_like'] # feelslikemin
    feelslike = weather_json['main']['feels_like'] # feelslike
    humidity = weather_json['main']['humidity'] # humidity
     # is_rain
    weather_range = tempmax - tempmin # weather_range
    

    # Time Features
    weekeday = datetime.datetime.today().weekday() #  weekday
    hour = datetime.datetime.now().hour # hour

    time_of_day_bin = '' # time_of_day_bin
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


    is_weekend = 0 # is_weekend
    if weekeday in [5,6]:
        is_weekend = 1





    





    


