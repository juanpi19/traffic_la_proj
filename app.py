import streamlit as st
import pandas as pd
import numpy as np
import geocoder
import pickle as pk
# import xgboost
import sqlite3
from datetime import datetime, timedelta
import webbrowser
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


# if st.checkbox("Check my location"):
#     loc = get_user_loc()
#     st.write(f"Your coordinates are {loc}")


# lat = loc['coords']['latitude']
# lat = loc['coords']['longitude']


### Functions

# get ip location
@st.cache_data
def keeping_state(from_, to):
    return from_, to

# Loading ML model from pickle file
with open('xgb_model_v1.pkl', 'rb') as pickle_file:
    xgb_model = pk.load(pickle_file)

################
# Top Part

# Setting the app to be wide
st.set_page_config(layout="wide")
loc = get_user_loc()

# waiting until data is stored in the variable
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
# Initial Map

col1, col2, col3 = st.columns(3, gap='large')

######## Session States

# go button clicked
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# from_address_user_input
if 'from_address_user_input' not in st.session_state:
    st.session_state.from_address_user_input = ""

# to_address_user_input and radius
if 'to_address_user_input' not in st.session_state:
    st.session_state.to_address_user_input = ""

# radius
if 'radius' not in st.session_state:
    st.session_state.radius = ""

# initial_map
if 'initial_map' not in st.session_state:
    st.session_state.initial_map = True

# current location button
if 'current_location' not in st.session_state:
       #time.sleep(2)
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        from_address = f" {lat},{lon} ".strip()
        st.session_state.current_location = from_address


################

from_address_user_input = col1.text_input("**From** - (e.g. USC Marshall School of Business) ", value='')

if from_address_user_input:
    st.session_state.from_address_user_input = from_address_user_input
    suggestions = fetch_autocomplete_suggestions(from_address_user_input)
    from_address = col1.selectbox("Suggested Places - (From)", options=suggestions)
    st.session_state.from_address_user_input = suggestions[0]


if col1.checkbox("Current Location"):
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    from_address = f" {lat},{lon} ".strip()
    st.session_state.current_location = from_address
    from_address_user_input = col1.text_input("**Current Location** ", value=st.session_state.current_location)
else:
    st.session_state.current_location = ''



to_places_help = '''
        Common Destinations in Downtown:
        - Grand Central Market
        - Crypto.com Arena
        - Walt Disney Concert Hall
        - verve coffee roasters
        '''

to_address_user_input = col2.text_input("**To** - (e.g. Grand Central Market)", value="", help=to_places_help)

if to_address_user_input:
    st.session_state.to_address_user_input = to_address_user_input
    suggestions = fetch_autocomplete_suggestions(to_address_user_input)
    to_address = col2.selectbox("Destination", options=suggestions)
    st.session_state.to_address_user_input = suggestions[0]


radius = col3.text_input("Number of Blocks Away You're Willing to Park - (e.g. 2)", value="")
if radius:
    st.session_state.radius = radius


button_clicked = col3.button("Go 🔜")


st.write("")
st.write("")

# Create an empty container
placeholder = st.empty()


# Displaying Map
if 'initial_map' not in st.session_state:
    st.session_state.initial_map = True

if st.session_state.initial_map:
    with placeholder.container():
        final_df = joins_street_parking_inventory_with_live_api_data()
        st.subheader(f"We're Covering {final_df.shape[0]} Street Parking Spots in Los Angeles")
        st.write("The majority of the spots are downtown, so if you're headed there this is definitely going to help you!")
        st.map(final_df[['lat', 'lon']])



#####################
# Main Logic
        
if button_clicked or st.session_state.button_clicked:

    st.session_state.button_clicked = True

    if st.session_state.current_location != '':


        # emptying the placeholder
        placeholder.empty()
        st.session_state.initial_map = False

        if to_address_user_input and radius:
            
            with st.spinner("Searching for available street parking..."):

                from_address_coordinates = st.session_state.current_location 
                to_address_coordinates = get_coordinates(to_address)


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


                available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df])

                st.subheader(f"{len(street_parking_spaceid_in_proximity_list)} Available Street Parking Spots Near your Destination!")
                st.text(f"🏁 distance in kilometers: {round(distance,1)}")
                st.text(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time().strftime('%H:%M')}")
                st.text(f"⬇️ scroll down to find the optimal available street parking near your destination!")

                available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"


                st.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color="color")
                st.caption("🔴 Origin and Destination 🔵 Available Street Parking Around your Destination")

                # Prepping data for model
                features_model_df = final_df[['spaceid', 'occupancystate', 'block_face', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit', 'lat', 'lon']]


                predicted_time_available = []

                # Making some space for better UI
                st.divider()

                with st.spinner("Predicting for available street parking near your destination..."):

                    for num in range(len(features_model_df)):

                        model_inputs_dict = collecting_model_features(api_endpoint_weather= weather_key_api_endpoint)
                        avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6 = calculate_avg_time_occupancy_previous_parkers(space_id=features_model_df.iloc[num]['spaceid'])


                        model_inputs_array = transform_ml_model_features_input(
                                                SpaceID=features_model_df.iloc[num]['spaceid'],
                                                OccupancyState=features_model_df.iloc[num]['occupancystate'],
                                                block_face=features_model_df.iloc[num]['block_face'],
                                                meter_type= features_model_df.iloc[num]['meter_type'],
                                                rate_type= features_model_df.iloc[num]['rate_type'],
                                                rate_range= features_model_df.iloc[num]['rate_range'],
                                                metered_time_limit= features_model_df.iloc[num]['metered_time_limit'] ,
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
                                                lat= features_model_df.iloc[num]['lat'],
                                                long= features_model_df.iloc[num]['lon']
                                            )
                        
                        
                        pred = round(np.exp(xgb_model.predict(model_inputs_array))[0],1)
                        predicted_time_available.append(pred)

                    time.sleep(1)

                st.divider()
                # st.subheader(f"Available Parking & Predicted Remaining Vacant Time!")
                # st.subheader(f"Park As Soon As You Arrive 😮‍💨")
                st.subheader(f"Let's not waste time searching for parking... Park as soon as you arrive 😮‍💨")
                

                # features_model_df['Remaining Available Time in Minutes'] = predicted_time_available
                # #map_available_parking.write(features_model_df[['spaceid', 'lat', 'lon', 'rate_range', 'metered_time_limit', 'Remaining Time Vacant in Minutes']].sort_values(by='Remaining Time Vacant in Minutes', ascending=False))
                # st.write(features_model_df[['Remaining Available Time in Minutes', 'rate_range', 'metered_time_limit']].sort_values(by='Remaining Available Time in Minutes', ascending=False))


                features_model_df['Spot Remaining Available Time in Minutes'] = predicted_time_available
                features_model_df[f'ETA to {st.session_state.to_address_user_input} in Minutes'] = round(duration)
                features_model_df['Spot'] = [f'Spot {i+1}' for i in range(features_model_df.shape[0])]
                
                # this keeps the available parking spots whose predicted available time is greater than the duration of your trip to get there
                features_model_df_2 = features_model_df[features_model_df['Spot Remaining Available Time in Minutes'] > round(duration)]

                # This dict collects the origin and destination from all available spots
                spot_dict = {}
                for index,row in features_model_df.iterrows():
                    spot_dict[f"{row['Spot']}"] = (from_address_user_input, f"{row['lat']},{row['lon']}")


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
    #########################              
    else:

        if st.session_state.from_address_user_input and st.session_state.to_address_user_input and st.session_state.radius:

            with st.spinner("Searching for available street parking..."):

                # emptying the placeholder
                placeholder.empty()
                st.session_state.initial_map = False

                #from_address_coordinates = get_coordinates(from_address) 
                from_address_coordinates = get_coordinates(st.session_state.from_address_user_input) 
                #to_address_coordinates = get_coordinates(to_address)
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

                #st.success("Done")


            if len(street_parking_spaceid_in_proximity_list) <= 0:
                st.write("Sorry, we didn't find anything in proximity. Try increasing the radius!")
            
            else:

                final_df = final_df[final_df['spaceid'].isin(street_parking_spaceid_in_proximity_list)]
                final_df['type'] = 'parking'


                available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df ])

                st.subheader(f"{len(street_parking_spaceid_in_proximity_list)} Available Street Parking Spots Near your Destination!")
                st.text(f"🏁 distance in kilometers: {round(distance,1)}")
                st.text(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time().strftime('%H:%M')}")
                st.text(f"⬇️ scroll down to find the optimal available street parking near your destination!")

                available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"

                st.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color="color")
                st.caption("🔴 Origin and Destination 🔵 Available Street Parking Around your Destination")


                # Prepping data for model
                features_model_df = final_df[['spaceid', 'occupancystate', 'block_face', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit', 'lat', 'lon']]


                predicted_time_available = []

                # Making some space for better UI
                st.divider()

                # Display message to tell users the ML model is running
                with st.spinner("Predicting for available street parking near your destination..."):

                    for num in range(len(features_model_df)):

                        model_inputs_dict = collecting_model_features(api_endpoint_weather= weather_key_api_endpoint)
                        avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6 = calculate_avg_time_occupancy_previous_parkers(space_id=features_model_df.iloc[num]['spaceid'])

                        # This function takes the inputs and encodes them
                        model_inputs_array = transform_ml_model_features_input(
                                                SpaceID=features_model_df.iloc[num]['spaceid'],
                                                OccupancyState=features_model_df.iloc[num]['occupancystate'],
                                                block_face=features_model_df.iloc[num]['block_face'],
                                                meter_type= features_model_df.iloc[num]['meter_type'],
                                                rate_type= features_model_df.iloc[num]['rate_type'],
                                                rate_range= features_model_df.iloc[num]['rate_range'],
                                                metered_time_limit= features_model_df.iloc[num]['metered_time_limit'] ,
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
                                                lat= features_model_df.iloc[num]['lat'],
                                                long= features_model_df.iloc[num]['lon']
                                            )
                        
                        # Predicting Available Remaining Time
                        pred = np.exp(xgb_model.predict(model_inputs_array))[0]
                        predicted_time_available.append(pred)

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
                    spot_dict[f"{row['Spot']}"] = (st.session_state.from_address_user_input, f"{row['lat']},{row['lon']}")

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

                

# If they make a change they need to click on the "GO! 🔜" button again to rerun.
#st.session_state.button_clicked = False



