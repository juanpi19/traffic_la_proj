import streamlit as st
import pandas as pd
import geocoder
import sqlite3
from datetime import datetime, timedelta
import pytz  # for working with time zones
from utility import get_coordinates, calculates_distance_and_driving_time_from_point_a_to_point_b, api_request, \
                    ingests_parking_meter_live_data_to_parking_meter_occupancy_live_t, haversine, \
                    fetch_autocomplete_suggestions, joins_street_parking_inventory_with_live_api_data, \
                    collecting_model_features, calculate_avg_time_occupancy_previous_parkers, \
                    transform_ml_model_features_input


app_token = st.secrets['app_token']
username = st.secrets['username']
password = st.secrets['password']
weather_key_api_endpoint = st.secrets['weather_key_api_endpoint']
bing_map_api_endpoint = st.secrets['bing_map_api_endpoint']
parking_meter_occupancy_api_endpoint = st.secrets['parking_meter_occupancy_api_endpoint']


st.set_page_config(layout="wide")

st.title("Your Solution to Street Parking in the City of LA")

col1, col2, col3 = st.columns(3, gap='large')



if 'current_location' not in st.session_state:
        st.session_state.current_location = ""


from_address_user_input = col1.text_input("From - (if you type and hit enter you'll see the suggestions below) ", value=st.session_state.current_location)


if from_address_user_input:
    suggestions = fetch_autocomplete_suggestions(from_address_user_input)
    from_address = col1.selectbox("Suggested Places - (From)", options=suggestions)

if st.button('Current Location'):
    from_address = f" {geocoder.ip('me').latlng[0]},{geocoder.ip('me').latlng[1] } ".strip()
    st.session_state.current_location = from_address



to_address_user_input = col2.text_input("To - (if you type and hit enter you'll see the suggestions below)", value="317 S Broadway, Los Angeles, CA 90013")

if to_address_user_input:
    suggestions = fetch_autocomplete_suggestions(to_address_user_input)
    to_address = col2.selectbox("Destination", options=suggestions)


radius = col3.text_input("Enter Distance in meters you're willing to walk (100 meters = 1 block)", value="")


st.write("")
st.write("")

map_total_parking_inventory, map_available_parking = st.columns(2, gap='large')


# Displaying Map

if 'initial_map' not in st.session_state:
    st.session_state.initial_map = True

if st.session_state.initial_map:

    final_df = joins_street_parking_inventory_with_live_api_data()


    map_total_parking_inventory.subheader(f'{final_df.shape[0]} Street Parking Spots with Live Data')
    #map_total_parking_inventory.write('As soon as you update the widgets above, this map will be refreshed')
    map_total_parking_inventory.map(final_df[['lat', 'lon']])
    st.caption('ToDo: get more live parking data from other parts of LA')

###




if st.session_state.current_location != '':


    if to_address_user_input and radius:

        from_address_coordinates = st.session_state.current_location #from_address #get_coordinates(from_address) 
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

                    if int(radius) >= haversine(destination_lat, destination_lon, float(row['lat']), float(row['long'])):

                        street_parking_spaceid_in_proximity_list.append(row['spaceid'])

                if len(street_parking_spaceid_in_proximity_list) <= 0:
                    map_available_parking.write("Sorry, we didn't find anything in proximity. Try increasing the radius!")
                
                else:

                    final_df = final_df[final_df['spaceid'].isin(street_parking_spaceid_in_proximity_list)]
                    final_df['type'] = 'parking'


                    available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df])

                    map_available_parking.subheader(f"{len(street_parking_spaceid_in_proximity_list)} Street Parking Available!")

                    available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                    available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"



                    map_available_parking.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color="color")
                    map_available_parking.write(f"🏁 distance in kilometers: {distance}")
                    map_available_parking.write(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time()}")
                    map_available_parking.write(available_parking_df)

                    map_available_parking.write(available_parking_df.columns)




# Manually Enters Address
                    
else:

    if from_address_user_input and to_address_user_input and radius:

        from_address_coordinates = get_coordinates(from_address) 
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

                    if int(radius) >= haversine(destination_lat, destination_lon, float(row['lat']), float(row['long'])):

                        street_parking_spaceid_in_proximity_list.append(row['spaceid'])

                if len(street_parking_spaceid_in_proximity_list) <= 0:
                    map_available_parking.write("Sorry, we didn't find anything in proximity. Try increasing the radius!")
                
                else:

                    final_df = final_df[final_df['spaceid'].isin(street_parking_spaceid_in_proximity_list)]
                    final_df['type'] = 'parking'


                    available_parking_df = pd.concat([final_df[['lat', 'lon', 'type']], df ])

                    map_available_parking.subheader(f"{len(street_parking_spaceid_in_proximity_list)} in proximity!")

                    available_parking_df.loc[(available_parking_df['type'] == 'destination'), 'color' ] = "#ff0000"
                    available_parking_df.loc[(available_parking_df['type'] == 'parking'), 'color' ] = "#0000FF"



                    map_available_parking.map(data=available_parking_df, latitude='lat', longitude='lon', size='type', color="color")
                    map_available_parking.write(f"🏁 distance in kilometers: {distance}")

                    map_available_parking.write(f"🚗 time in minutes: {round(duration)}, get there by {(datetime.now() + timedelta(minutes=duration)).time()}")
                    map_available_parking.write(available_parking_df)

                    # Prepping data for model
                    features_model_df = final_df[['spaceid', 'occupancystate', 'block_face', 'meter_type', 'rate_type', 'rate_range', 'metered_time_limit', 'lat', 'lon']]

                    
                    map_available_parking.write(features_model_df.iloc[0])

                    map_available_parking.write(collecting_model_features(api_endpoint_weather= weather_key_api_endpoint))

                    map_available_parking.write(calculate_avg_time_occupancy_previous_parkers(space_id=features_model_df.iloc[0]['spaceid']))

                    model_inputs_dict = collecting_model_features(api_endpoint_weather= weather_key_api_endpoint)
                    avg_time_in_occupancy_past_3, avg_time_in_occupancy_past_6 = calculate_avg_time_occupancy_previous_parkers(space_id=features_model_df.iloc[0]['spaceid'])




                    model_inputs_array = transform_ml_model_features_input(
                                            SpaceID=features_model_df.iloc[0]['spaceid'],
                                            OccupancyState=features_model_df.iloc[0]['occupancystate'],
                                            block_face=features_model_df.iloc[0]['block_face'],
                                            meter_type= features_model_df.iloc[0]['meter_type'],
                                            rate_type= features_model_df.iloc[0]['rate_type'],
                                            rate_range= features_model_df.iloc[0]['rate_range'],
                                            metered_time_limit= features_model_df.iloc[0]['metered_time_limit'] ,
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
                                            lat= features_model_df.iloc[0]['lat'],
                                            long= features_model_df.iloc[0]['lon']
                                        )
                    
                    map_available_parking.write(model_inputs_array)







