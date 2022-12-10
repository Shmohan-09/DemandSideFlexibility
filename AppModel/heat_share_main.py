# The inputs are similar to the heat planning algorithm, and thus scarcely commented.

# import necessary libraries
import numpy as np
import pandas as pd
from datetime import date
import streamlit as st
import os
from pathlib import Path
from heat_share_func import multi_heater_individual, multi_heater_share
from Plots import multi_heater_plot, multi_heater_share_plot

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

# Streamlit containers
header = st.container()
dataset = st.container()
left_col, mid_col, right_col = st.columns(3)

with header:
    st.title('Mutli-Heater optimization')
    st.header('This optimization heat sharing between independent houses - House 0 is efficient')

with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',)))
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price', 'Price_high'))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    day = int(right_col.text_input("Calendar day between 0 to 363", value = 50))
    heater_power_csv = left_col.selectbox("Heater power", ('heater_power_share',))
    heater_power = pd.read_csv(f'{data_dir}\{heater_power_csv}.csv', header=None).values
    R_csv = mid_col.selectbox("Heating resistivity °C/Watt (60-min)", ('R_share',))
    R = pd.read_csv(f'{data_dir}\{R_csv}.csv', header=None).values
    tao_csv = right_col.selectbox("Time constant in hours (60-min)", ('tao_share',))
    tao = pd.read_csv(f'{data_dir}\{tao_csv}.csv', header=None).values
    T_set_csv = left_col.text_input("Setpoint Temperature as .csv", value = 'T_set_share')
    T_set = pd.read_csv(f'{data_dir}\{T_set_csv}.csv', header=None).values
    T_start_csv = mid_col.text_input("Start Temperature as .csv", value = 'T_start_share')
    T_start = pd.read_csv(f'{data_dir}\{T_start_csv}.csv', header=None).values
    T_out_csv = right_col.selectbox("Ambient temperature °C (60-min)", ('T_out_Zurich',))
    T_out = pd.read_csv(f'{data_dir}\{T_out_csv}.csv', skiprows=3, index_col = 0, parse_dates=True)
    solar_csv_name = mid_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    solar_cap_csv = left_col.text_input("Input solar capacity", value = 'solar_capacity')
    solar_capacity = pd.read_csv(f'{data_dir}\{solar_cap_csv}.csv', header=None).values
    onsite_resources = right_col.selectbox("Make use of onsite resources", ('Yes', 'No'))
    onsite_resources = 1 if onsite_resources == 'Yes' else 0
    heat_share_allow = left_col.selectbox("Allow heat sharing", ('Yes', 'No')) # this is the command that choses to or not to opt for heat sharing
    dead_band = float(mid_col.text_input("Temperature deviation in °C", value = 2))
    efficiency_other_dependents = right_col.text_input("Efficiency of inefficient heaters", value = 0.7)
    allow_deadband_flexibility = left_col.selectbox("Allow DB flexibility (DBF)?", ('Yes', 'No'))
    allow_deadband_flexibility = 1 if allow_deadband_flexibility == 'Yes' else 0
    allow_deadband_flexibility_price = float(mid_col.text_input("DBF price threshold (€/MWh)", value = 600))
    
    
optimization_horizon = 24
hour = pd.date_range(date.today(), periods=24, freq="H")
day_ahead.index = hour
day_ahead = day_ahead.resample('15T').ffill()
price = day_ahead[0].values 
prices = np.append(price, np.array(3*[price[-1]]))

solar_data = solar_data.resample('15T').ffill()
solar_data = solar_data['electricity'].values

T_out = T_out.resample('15T').mean().interpolate(method='linear')
T_out = T_out['temperature'].values
T_out_array = np.append(T_out, np.array(3*[T_out[-1]]))

if heat_share_allow == 'No':
    prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, number_of_houses, time_step_per_hour, T_start, solar_data_multi_home, T_out\
    = multi_heater_individual(T_start, T_set, dead_band, heater_power, T_out, prices, R, tao, 
                time_granularity, solar_data, solar_capacity, allow_deadband_flexibility, 
                allow_deadband_flexibility_price, onsite_resources, day, optimization_horizon)
else:
   prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, \
        number_of_houses, time_step_per_hour, T_start, heater_status_ineff, solar_data_multi_home, T_out = multi_heater_share(T_start, T_set, dead_band, heater_power, T_out, prices, R, tao, time_granularity, solar_data, solar_capacity, allow_deadband_flexibility, 
                allow_deadband_flexibility_price, efficiency_other_dependents, onsite_resources, day, optimization_horizon)

plots = st.container()
with plots:
    house_number = int(right_col.text_input(f" Result for house number (0 to {number_of_houses - 1})", value = 1))

if heat_share_allow == 'No':
    heat_share_temp, heat_share_status = multi_heater_plot(price, T_upper_bound, T_lower_bound, temperature, house_number, T_set, T_out, solar_data_multi_home, solar_charge, heater_status)
else:
    heat_share_temp, heat_share_status = multi_heater_share_plot(price, T_upper_bound, T_lower_bound, temperature, house_number, T_set, T_out, solar_data_multi_home, solar_charge, heater_status, heater_status_ineff)

with plots:
    st.header('Plots')
    st.plotly_chart(heat_share_temp)
    st.plotly_chart(heat_share_status)
