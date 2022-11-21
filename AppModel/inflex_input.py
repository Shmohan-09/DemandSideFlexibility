"""
To create interface of the Streamlit Web App!
Inputs are obtained here
"""

# Import all necessary libraries
import os
from pathlib import Path
import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
from inflex_model import unint_scheduler
from Plots import plot_atomic

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

# Streamlit containers
header = st.container()
dataset = st.container()
left_col, mid_col, right_col = st.columns(3)

with header:
    st.title('EV Charging Optimization')
    st.header('This optimization operates the atomic device to achieve lowest energy consumption cost')

# Request inputs from the user
with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',)))
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price','Price_high',))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    solar_csv_name = right_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    inflex_start_time = left_col.text_input('Start time of inflexible load in hh:mm', value = '06:00')
    inflex_end_time = mid_col.text_input('End time of inflexible load in hh:mm', value = '12:00')
    power_inflexible_load = float(right_col.text_input('Power rating of inflexible load in watt', value = '400'))
    time_of_run = float(left_col.text_input('Duration of run (in hours)', value = '5'))
    solar_capacity = float(mid_col.text_input("Installed solar capacity in kW: ", value = 2))
    solar_day = int(right_col.text_input('Solar day integer from 0 to 365', value = '50'))
    
# process input timeseries
hour = pd.date_range(date.today(), periods=24, freq="H")
day_ahead.index = hour
day_ahead = day_ahead.resample('15T').ffill()
prices = day_ahead[0].values 
prices = np.append(prices, np.array(3*[prices[-1]]))
prices = np.append(prices,prices)
solar_data = solar_data.resample('15T').mean().interpolate(method='linear')
solar_data = solar_data['electricity'].values
inflexible_window = [inflex_start_time, inflex_end_time]

time_step_per_hour = 60 // time_granularity

inflex_start_time = inflexible_window[0].split(':')
inflex_start_time = int(inflex_start_time[0])*time_step_per_hour + int(np.ceil(int(inflex_start_time[1])/time_granularity))

inflex_end_time = inflexible_window[1].split(':')
inflex_end_time = int(inflex_end_time[0])*time_step_per_hour + int(np.floor(int(inflex_end_time[1])/time_granularity))

flexible_window_timesteps = [inflex_start_time, inflex_end_time]
SimLength = 24*time_step_per_hour
inflexible_load = np.zeros(SimLength)
inflexible_load[inflex_start_time:inflex_end_time] = power_inflexible_load

status_stack, appliance_profile_stack, prices, solar_charge, solar_data, base_profile, energy_consumption_cost_optimal, energy_consumption_cost_base = \
    unint_scheduler(SimLength, power_inflexible_load, time_of_run, flexible_window_timesteps, prices, time_granularity, solar_capacity, solar_data, solar_day)

appliance_status = (appliance_profile_stack@status_stack).value

atomic_status = plot_atomic(prices, appliance_status, base_profile, flexible_window_timesteps, solar_data, solar_charge)
plots = st.container()
with plots:
    st.header('Plots')
    st.plotly_chart(atomic_status)
results = st.container()
with results:
    st.header('Numbers')
    st.write(f'Electricity consumption cost without flexibility: {np.round(energy_consumption_cost_base,2)} €/kWh')
    st.write(f'Electricity consumption cost with flexibility: {np.round(energy_consumption_cost_optimal,2)} €/kWh')
    