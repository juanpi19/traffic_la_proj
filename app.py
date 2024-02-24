# Importing Libraries
import streamlit as st
import pandas as pd
import numpy as np
import geocoder
import pickle as pk
from datetime import datetime, timedelta
import time
from utility import get_coordinates, \
                    calculates_distance_and_driving_time_from_point_a_to_point_b, \
                    api_request, \
                    haversine, \
                    fetch_autocomplete_suggestions, \
                    joins_street_parking_inventory_with_live_api_data, \
                    collecting_model_features, \
                    calculate_avg_time_occupancy_previous_parkers, \
                    transform_ml_model_features_input, \
                    open_google_maps, \
                    get_user_loc

# Getting API keys 
app_token = st.secrets['app_token']
username = st.secrets['username']
password = st.secrets['password']
weather_key_api_endpoint = st.secrets['weather_key_api_endpoint']
bing_map_api_endpoint = st.secrets['bing_map_api_endpoint']
parking_meter_occupancy_api_endpoint = st.secrets['parking_meter_occupancy_api_endpoint']

### Functions

# get ip location
@st.cache_data
def keeping_state(from_, to):
    return from_, to

# Loading ML model from pickle file
with open('xgb_model_v1.pkl', 'rb') as pickle_file:
    xgb_model = pk.load(pickle_file)

# This dictionary contains all the encoded values from the model training 
with open('mapping_dictionary.pkl', 'rb') as pickle_file:
    mapping_dict = pk.load(pickle_file)

################
# Top Part

# Setting the app to be wide
st.set_page_config(layout="wide")
loc = get_user_loc()

# Waiting until data is stored in the variable
while loc is None:
    time.sleep(1)

# Main title
st.title("Your Solution to Street Parking in the City of LA")
st.divider()

# Expanders that Explain the App
with st.expander("Purpose of This App"):
        ul_list_markdown = '''- Minimize the time spent searching for street parking in downtown LA :sunglasses:
                              \n- It's simple. Enter your origin, your destination, the distance you're willing to walk from your destination and that's it!
                              \n- Leverage the power of live data and machine learning techniques to make the Angelenos' lives easier '''
        st.markdown(ul_list_markdown)
    

with st.expander("Wondering How It Works?"):
    ul_list_markdown = '''- **From:** USC Marshall School of Business 
                        \n- **To:** Grand Central Market
                        \n- **Blocks Away:** 3
                        \n- Hit the "Go 🔜" button and let the algorithm do its thing and then... Magic time! Get a list of available street parking in proximity to your destination with a solid prediction of how long these will remain available! :sunglasses:'''
    st.markdown(ul_list_markdown)


# Adding space for better UI
st.divider()


##################
# Splitting UI into three parts (from, to, radius)
col1, col2, col3 = st.columns(3, gap='large')

######## Session States
# go button clicked session state
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# from_address_user_input session state
if 'from_address_user_input' not in st.session_state:
    st.session_state.from_address_user_input = ""

# to_address_user_input session state
if 'to_address_user_input' not in st.session_state:
    st.session_state.to_address_user_input = ""

# radius session state
if 'radius' not in st.session_state:
    st.session_state.radius = ""

# initial_map session state
if 'initial_map' not in st.session_state:
    st.session_state.initial_map = True

# current location button session state, this also loads user's current location to the from_address variable
if 'current_location' not in st.session_state:
       #time.sleep(2)
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        from_address = f" {lat},{lon} ".strip()
        st.session_state.current_location = from_address


################ User Input Widgets

# from_address text input
from_address_user_input = col1.text_input("**From** - (e.g. USC Marshall School of Business) ", value='')

# Once the user types something in the text input, two thing will happen
# 1. we update the from_address_user_input session state with the text the user wrote
# 2. we will call the fetch_autocomplete_suggestions to get suggestions of places using bing maps api and display those to the user
if from_address_user_input:
    st.session_state.from_address_user_input = from_address_user_input
    suggestions = fetch_autocomplete_suggestions(from_address_user_input)
    from_address = col1.selectbox("Suggested Places - (From)", options=suggestions)
    st.session_state.from_address_user_input = suggestions[0]

# If the user checks off the current location checkbox, we will store the user's coordinates in the current_location session state
if col1.checkbox("Current Location"):
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    from_address = f" {lat},{lon} ".strip()
    st.session_state.current_location = from_address
    from_address_user_input = col1.text_input("**Current Location** ", value=st.session_state.current_location)
else:
    st.session_state.current_location = ''


# Common destinations in downtown LA -- this will help the user have an idea of how to use the destination text_input
to_places_help = '''
        Common Destinations in Downtown:
        - Grand Central Market
        - Crypto.com Arena
        - Walt Disney Concert Hall
        - verve coffee roasters
        '''

#  to_adress_user_input text input
to_address_user_input = col2.text_input("**To** - (e.g. Grand Central Market)", value="", help=to_places_help)

# Once the user types something in the text input, two thing will happen
# 1. we update the to_address_user_input session state with the text the user wrote
# 2. we will call the fetch_autocomplete_suggestions to get suggestions of places using bing maps api and display those to the user
if to_address_user_input:
    st.session_state.to_address_user_input = to_address_user_input
    suggestions = fetch_autocomplete_suggestions(to_address_user_input)
    to_address = col2.selectbox("Destination", options=suggestions)
    st.session_state.to_address_user_input = suggestions[0]

# radius text input, here the user is expected to insert an integer which represents the number of blocks they're willing to walk from the destination
radius = col3.text_input("Number of Blocks Away You're Willing to Park - (e.g. 2)", value="")
if radius:
    st.session_state.radius = radius

# button that triggers an action once the user has fulled all the necessary inputs (from, to, num blocks)
button_clicked = col3.button("Go 🔜")

# some space for better UI
st.write("")
st.write("")

# Create an empty container
placeholder = st.empty()

# this displays the initial map which shows all the spots that the api has coverage for
if st.session_state.initial_map:
    with placeholder.container():
        final_df = joins_street_parking_inventory_with_live_api_data()
        st.subheader(f"We're Covering {final_df.shape[0]} Street Parking Spots in Los Angeles")
        st.write("All the red dots in the map are street parking spots. The majority of the spots we cover are downtown, so if you're headed there this is definitely going to help you!")
        st.map(final_df[['lat', 'lon']])



### Everything up to this point has been about handling user input, creating session states, and orginizing the layout of the app

#####################
# Here starts the main logic, which is what happens once the user has filled all the necessary inputs and clicks the button "Go"

# Simply put, the logic goes as followed:
#   1. did user click on go button?
#   2. if user is using current location feature
#        action
#   3. else
#        action
        
# This checks if user clicked on go button
if button_clicked or st.session_state.button_clicked:

    st.session_state.button_clicked = True

    # User uses current location feature, which means to check off the current location checkbox
    if st.session_state.current_location != '':

        # emptying the placeholder
        placeholder.empty()
        st.session_state.initial_map = False

        # checks if user filled the to_address_user_input and radius text boxes, which are essential
        if to_address_user_input and radius:
            
            with st.spinner("Searching for available street parking..."):

                from_address_coordinates = st.session_state.current_location # gets current location coordinates
                to_address_coordinates = get_coordinates(to_address) # calls the get_coordinates function to convert the to_adress location into coordinates

                # Checks if both from and to addresses have been converted to coordinates
                if from_address_coordinates and to_address_coordinates:
                        
                    # calls a function to calculate the distance and duration driving between the 2 points
                    distance, duration = calculates_distance_and_driving_time_from_point_a_to_point_b(from_address_coordinates, to_address_coordinates)

                    # if both distance and duration are successfully calculated
                    if distance and duration:
                        
                        # puts latitude and longitude from both from and to addresses into separate lists
                        lat = [float(from_address_coordinates.split(',')[0]), float(to_address_coordinates.split(',')[0])]
                        long = [float(from_address_coordinates.split(',')[1]), float(to_address_coordinates.split(',')[1])]

                        # creates dataframe with the lists
                        df = pd.DataFrame({'lat': lat, 'lon': long, 'type': ['destination', 'destination']})

                        # Pings api to get real time data on vacant parking spots
                        final_df = joins_street_parking_inventory_with_live_api_data()
                        final_df = final_df[final_df['occupancystate'] == 'VACANT']

                        # ToDo: this is repeating?? could be omitted
                        destination_lat = float(to_address_coordinates.split(',')[0])
                        destination_lon = float(to_address_coordinates.split(',')[1])

                        # this is a list that collects the spaceid that are in proximity to the destination
                        street_parking_spaceid_in_proximity_list = []

                        # loop through the live parking spot we just pulled from the api 
                        for index, row in final_df.iterrows():

                            # Uses haversine distance to check which spaceids are within proximity to the radius you specified
                            if int(radius) * 100 >= haversine(destination_lat, destination_lon, float(row['lat']), float(row['long'])):

                                # the spaceids in proximity are stored in the list
                                street_parking_spaceid_in_proximity_list.append(row['spaceid'])

            # this if-else checks if any spots were found in proximity
            if len(street_parking_spaceid_in_proximity_list) <= 0:
                st.write("Sorry, we didn't find anything in proximity. Try increasing the radius!")
            
            else:

                # filter spaceid dataframe to keep the ones in proximity only
                final_df = final_df[final_df['spaceid'].isin(street_parking_spaceid_in_proximity_list)]
                final_df['type'] = 'parking'

                # concatenate both dataframes: df: contains user info, final_df: contains api data regarding spots availability
                available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df])

                # displays the information regarding what's been found: distance, duration driving in minutes, num of parking spots available in proximity
                st.subheader(f"{len(street_parking_spaceid_in_proximity_list)} Available Street Parking Spots Near your Destination!")
                st.text(f"🏁 distance in kilometers: {round(distance,1)} from {st.session_state.current_location} to {st.session_state.to_address_user_input}")
                st.text(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time().strftime('%H:%M')}")
                st.text(f"⬇️ scroll down to find the optimal available street parking near your destination!")

                available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"

                st.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color='color')
                st.caption("🔴 Origin and Destination 🔵 Available Street Parking Around your Destination")

                # Prepping data to feed the model the right inputs to make predictions, we keep only the columns (features) I need for the model
                features_model_df = final_df[['spaceid', 'occupancystate', 'block_face', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit', 'lat', 'lon']]

                # this list will store the predictions made for the available spots found in proximity
                predicted_time_available = []

                # Making some space for better UI
                st.divider()

                with st.spinner("Predicting for available street parking near your destination..."):

                    # Pinging API to collect weather data 
                    model_inputs_dict = collecting_model_features(api_endpoint_weather= weather_key_api_endpoint)

                    for num in features_model_df['spaceid']:

                        if num in mapping_dict['SpaceID'].keys():
                    
                            avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6 = calculate_avg_time_occupancy_previous_parkers(space_id=num)

                            model_inputs_array = transform_ml_model_features_input(
                                                    SpaceID=num,
                                                    OccupancyState=features_model_df[features_model_df['spaceid'] == num]['occupancystate'].values[0],
                                                    block_face=features_model_df[features_model_df['spaceid'] == num]['block_face'].values[0],
                                                    meter_type= features_model_df[features_model_df['spaceid'] == num]['meter_type'].values[0],
                                                    rate_type= features_model_df[features_model_df['spaceid'] == num]['rate_type'].values[0],
                                                    rate_range= features_model_df[features_model_df['spaceid'] == num]['rate_range'].values[0],
                                                    metered_time_limit= features_model_df[features_model_df['spaceid'] == num]['metered_time_limit'].values[0],
                                                    day= model_inputs_dict['day'],
                                                    tempmax= model_inputs_dict['tempmax'],
                                                    tempmin= model_inputs_dict['tempmin'],
                                                    temp= model_inputs_dict['temp'],
                                                    feelslike= model_inputs_dict['feelslike'],
                                                    humidity= model_inputs_dict['humidity'],
                                                    weekday= model_inputs_dict['weekday'],
                                                    hour= model_inputs_dict['hour'],
                                                    minute= model_inputs_dict['minute'],
                                                    is_am= model_inputs_dict['is_am'],
                                                    is_work= model_inputs_dict['is_work'],
                                                    time_of_day_bin= model_inputs_dict['time_of_day_bin'],
                                                    is_weekend= model_inputs_dict['is_weekend'],
                                                    avg_time_in_occupancy_past_3= avg_time_in_occupancy_past_3 ,
                                                    avg_time_in_occupancy_past_6= avg_time_in_occupancy_past_6,
                                                    hour_weekday_interaction= model_inputs_dict['hour_weekday_interaction'],
                                                    weather_range= model_inputs_dict['weather_range'], 
                                                    lat= features_model_df[features_model_df['spaceid'] == num]['lat'].values[0],
                                                    long= features_model_df[features_model_df['spaceid'] == num]['lon'].values[0]
                                                )
                                                
                            pred = round(np.exp(xgb_model.predict(model_inputs_array))[0],1)
                            predicted_time_available.append(pred)

                        else:
                            # if the model hasn't been trained on a specific space_id, I'll drop it
                            features_model_df.drop(features_model_df[features_model_df['spaceid'] == num].index, inplace=True)

                    time.sleep(1)

                st.divider()
                st.subheader(f"Let's not waste time searching for parking... Park as soon as you arrive 😮‍💨")

                features_model_df['Spot Remaining Available Time in Minutes'] = predicted_time_available
                features_model_df[f'ETA to {st.session_state.to_address_user_input} in Minutes'] = round(duration)
                features_model_df['Spot'] = [f'Spot {i+1}' for i in range(len(predicted_time_available))]
                
                # this keeps the available parking spots whose predicted available time is greater than the duration of your trip to get there
                features_model_df_2 = features_model_df[features_model_df['Spot Remaining Available Time in Minutes'] > round(duration)]

                # This dict collects the origin and destination from all available spots
                spot_dict = {}
                for index,row in features_model_df.iterrows():
                    spot_dict[row['Spot']] = (from_address_user_input, f"{row['lat']},{row['lon']}")

                # This if-else checks if there is an optimal spot. if the shape == 0 there isn't one.
                if features_model_df_2.shape[0] == 0:
                    st.caption("The model predicts that the available parking spots near your destination will be taken by the time you arrive 🤔. Try expanding the number of blocks away from your destination or run it again when you're approaching your destination!")
                    st.write(features_model_df[['Spot', f'ETA to {st.session_state.to_address_user_input} in Minutes', 
                                                'Spot Remaining Available Time in Minutes']].sort_values(by='Spot Remaining Available Time in Minutes', ascending=False).set_index('Spot').T)

                    # Adding columns to improve UI
                    left, right = st.columns(2)

                    with left:
                        with st.form("Spot Form"):
                            
                            # if user still wants to go, they can select an option here
                            option = st.selectbox(
                                        'Still go? Select your option below!',
                                        (i for i in features_model_df['Spot']),
                                        index=None,
                                        help="Select the spot that you'd like and a google maps window will open and it'll take you right there!",
                                        placeholder="Select Parking Spot...")
                                
                            submit_button = st.form_submit_button("Go! 🔜")

                            if submit_button:
                                final_destination = keeping_state(from_=spot_dict[option][0], to=spot_dict[option][1])
                                open_google_maps(from_place=final_destination[0], to_place=final_destination[1])


                else:
                    
                    # optimizing the best one
                    st.write("This is the optimal spot :sunglasses:")
                    st.write(features_model_df_2[['Spot', f'ETA to {st.session_state.to_address_user_input} in Minutes', 
                                                  'Spot Remaining Available Time in Minutes', 
                                                  'rate_range', 'metered_time_limit']].sort_values(by='Spot Remaining Available Time in Minutes', ascending=False).head(1).set_index('Spot').T)
                    
                    # on_click=open_page(url)
                    option = features_model_df_2['Spot'].values[0]
                    final_destination = keeping_state(from_=spot_dict[option][0], to=spot_dict[option][1])
                    if st.button("Go! 🔜"):
                        open_google_maps(from_place=final_destination[0], to_place=final_destination[1])



    #########################
    # Manually Enters Address             
    else:

        if st.session_state.from_address_user_input and st.session_state.to_address_user_input and st.session_state.radius:

            with st.spinner("Searching for available street parking..."):

                # emptying the placeholder
                placeholder.empty()
                st.session_state.initial_map = False

                from_address_coordinates = get_coordinates(st.session_state.from_address_user_input) 
                to_address_coordinates = get_coordinates(st.session_state.to_address_user_input)

                if from_address_coordinates and to_address_coordinates:
                    
                    distance, duration = calculates_distance_and_driving_time_from_point_a_to_point_b(from_address_coordinates, to_address_coordinates)

                    if distance and duration:
        
                        lat = [float(from_address_coordinates.split(',')[0]), float(to_address_coordinates.split(',')[0])]
                        long = [float(from_address_coordinates.split(',')[1]), float(to_address_coordinates.split(',')[1])]

                        df = pd.DataFrame({'lat': lat, 'lon': long, 'type': ['destination', 'destination']})

                        final_df = joins_street_parking_inventory_with_live_api_data()
                        final_df = final_df[final_df['occupancystate'] == 'VACANT']

                        destination_lat = float(to_address_coordinates.split(',')[0])
                        destination_lon = float(to_address_coordinates.split(',')[1])

                        street_parking_spaceid_in_proximity_list = []


                        for index, row in final_df.iterrows():

                            if int(radius) * 100 >= haversine(destination_lat, destination_lon, float(row['lat']), float(row['long'])):

                                street_parking_spaceid_in_proximity_list.append(row['spaceid'])


            if len(street_parking_spaceid_in_proximity_list) <= 0:
                st.write("Sorry, we didn't find anything in proximity. Try increasing the radius!")
            
            else:

                final_df = final_df[final_df['spaceid'].isin(street_parking_spaceid_in_proximity_list)]
                final_df['type'] = 'parking'


                available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df ])

                # st.write(available_parking_df)

                st.subheader(f"{len(street_parking_spaceid_in_proximity_list)} Available Street Parking Spots Near your Destination!")
                st.text(f"🏁 distance in kilometers: {round(distance,1)} from {st.session_state.from_address_user_input} to {st.session_state.to_address_user_input}")
                st.text(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time().strftime('%H:%M')}")
                st.text(f"⬇️ scroll down to find the optimal available street parking near your destination!")

                available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"

                st.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color='color')
                st.caption("🔴 Origin and Destination 🔵 Available Street Parking Around your Destination")


                # Prepping data for model
                features_model_df = final_df[['spaceid', 'occupancystate', 'block_face', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit', 'lat', 'lon']]

                predicted_time_available = []

                # Making some space for better UI
                st.divider()

                # Display message to tell users the ML model is running
                with st.spinner("Predicting for available street parking near your destination..."):

                    # Pinging API to collect weather data 
                    model_inputs_dict = collecting_model_features(api_endpoint_weather= weather_key_api_endpoint)

                    for num in features_model_df['spaceid']:

                        if num in mapping_dict['SpaceID'].keys():

                            avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6 = calculate_avg_time_occupancy_previous_parkers(space_id=num)

                            model_inputs_array = transform_ml_model_features_input(
                                                    SpaceID=num,
                                                    OccupancyState=features_model_df[features_model_df['spaceid'] == num]['occupancystate'].values[0],
                                                    block_face=features_model_df[features_model_df['spaceid'] == num]['block_face'].values[0],
                                                    meter_type= features_model_df[features_model_df['spaceid'] == num]['meter_type'].values[0],
                                                    rate_type= features_model_df[features_model_df['spaceid'] == num]['rate_type'].values[0],
                                                    rate_range= features_model_df[features_model_df['spaceid'] == num]['rate_range'].values[0],
                                                    metered_time_limit= features_model_df[features_model_df['spaceid'] == num]['metered_time_limit'].values[0],
                                                    day= model_inputs_dict['day'],
                                                    tempmax= model_inputs_dict['tempmax'],
                                                    tempmin= model_inputs_dict['tempmin'],
                                                    temp= model_inputs_dict['temp'],
                                                    feelslike= model_inputs_dict['feelslike'],
                                                    humidity= model_inputs_dict['humidity'],
                                                    weekday= model_inputs_dict['weekday'],
                                                    hour= model_inputs_dict['hour'],
                                                    minute= model_inputs_dict['minute'],
                                                    is_am= model_inputs_dict['is_am'],
                                                    is_work= model_inputs_dict['is_work'],
                                                    time_of_day_bin= model_inputs_dict['time_of_day_bin'],
                                                    is_weekend= model_inputs_dict['is_weekend'],
                                                    avg_time_in_occupancy_past_3= avg_time_in_occupancy_past_3 ,
                                                    avg_time_in_occupancy_past_6= avg_time_in_occupancy_past_6,
                                                    hour_weekday_interaction= model_inputs_dict['hour_weekday_interaction'],
                                                    weather_range= model_inputs_dict['weather_range'], 
                                                    lat= features_model_df[features_model_df['spaceid'] == num]['lat'].values[0],
                                                    long= features_model_df[features_model_df['spaceid'] == num]['lon'].values[0]
                                                )
                            
                            # Predicting Available Remaining Time
                            pred = np.exp(xgb_model.predict(model_inputs_array))[0]
                            predicted_time_available.append(pred)

                        else:
                            # if the model hasn't been trained on a specific space_id, I'll drop it
                            features_model_df.drop(features_model_df[features_model_df['spaceid'] == num].index, inplace=True)

                    # Wait a longer second
                    time.sleep(1)

                st.divider()
                st.subheader(f"Let's not Waste Time Searching for Parking... Park As Soon As You Arrive 😮‍💨")
                

                features_model_df['Spot Remaining Available Time in Minutes'] = predicted_time_available
                features_model_df[f'ETA to {st.session_state.to_address_user_input} in Minutes'] = round(duration)
                features_model_df['Spot'] = [f'Spot {i+1}' for i in range(features_model_df.shape[0])]
                
                # this keeps the available parking spots whose predicted available time is greater than the duration of your trip to get there
                features_model_df_2 = features_model_df[features_model_df['Spot Remaining Available Time in Minutes'] > round(duration)]

                # This dict collects the origin and destination from all available spots
                spot_dict = {}
                for index,row in features_model_df.iterrows():
                    spot_dict[row['Spot']] = (st.session_state.from_address_user_input, f"{row['lat']},{row['lon']}")

                if features_model_df_2.shape[0] == 0:
                    st.caption("The model predicts that the available parking spots near your destination will be taken by the time you arrive 🤔. Try expanding the number of blocks away from your destination or run it again when you're approaching your destination!")
                    st.write(features_model_df[['Spot', f'ETA to {st.session_state.to_address_user_input} in Minutes', 
                                                'Spot Remaining Available Time in Minutes']].sort_values(by='Spot Remaining Available Time in Minutes', ascending=False).set_index('Spot').T)


                    # Adding columns to improve UI
                    left, right = st.columns(2)

                    with left:
                        with st.form("Spot Form"):
                            
                            # if user still wants to go, they can select an option here
                            option = st.selectbox(
                                        'Still go? Select your option below!',
                                        (i for i in features_model_df['Spot']),
                                        index=None,
                                        help="Select the spot that you'd like and a google maps window will open and it'll take you right there!",
                                        placeholder="Select Parking Spot...")
                                
                            submit_button = st.form_submit_button("Go! 🔜")

                            #option = features_model_df_2['Spot'].values
                            #final_destination = keeping_state(from_=spot_dict[option][0], to=spot_dict[option][1])
                            #st.write(spot_dict[option][0])


                            if submit_button:
                                final_destination = keeping_state(from_=spot_dict[option][0], to=spot_dict[option][1])
                                # st.write(final_destination)
                                open_google_maps(from_place=final_destination[0], to_place=final_destination[1])

                else:
                    # optimizing the best one
                    st.write("This is the optimal spot :sunglasses:")
                    st.write(features_model_df_2[['Spot', f'ETA to {st.session_state.to_address_user_input} in Minutes', 
                                                  'Spot Remaining Available Time in Minutes', 
                                                  'rate_range', 'metered_time_limit']].sort_values(by='Spot Remaining Available Time in Minutes', ascending=False).head(1).set_index('Spot').T)
                    

                    # on_click=open_page(url)
                    option = features_model_df_2['Spot'].values[0]
                    final_destination = keeping_state(from_=spot_dict[option][0], to=spot_dict[option][1])

                    if st.button("Go! 🔜"):
                        open_google_maps(from_place=final_destination[0], to_place=final_destination[1])

                



