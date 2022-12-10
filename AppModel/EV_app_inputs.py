"""
To create interface of the Streamlit Web App!
Inputs are obtained here
The inputs similar to the heating app are not commented in the file
"""

# Import all necessary libraries
import os
from pathlib import Path
import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
from EV_model import EV_optimize_LP, EV_optimize_MILP
from Plots import EV_plot_gen

st.set_page_config(layout="wide")

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

# Streamlit containers
header = st.container()
dataset = st.container()
left_col, mid_col, right_col = st.columns(3)

with header:
    st.title('EV Charging Optimization')
    st.header('This optimization charges the vehicle in the lowest priced timining while using V2H capability')

# Request inputs from the user
with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',))) 
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price_high','Price'))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    v2g_feasibility = right_col.selectbox("V2G functionality availablity: ", ('Yes','No')) # input for V2G functionality
    v2g_feasibility = 1 if v2g_feasibility == 'Yes' else 0
    soc_start = float(left_col.text_input('Initial SoC in kWh', value = '12')) # Initialize the EV SoC
    battery_size = float(mid_col.text_input('EV battery size in kWh', value = '36')) # Choose battery size
    plug_in_power = float(right_col.text_input('Plug-in power in kW', value = '3.7')) # Charging power of the EV
    distance_next_trip = float(left_col.text_input('Distance to drive in next trip in km', value = '50')) # Distance to drive
    average_kWh_km = float(mid_col.text_input('Power consumption per km', value = '0.2')) # Fuel efficiency of the vehicle
    force_charge = right_col.selectbox("Force charge below a certain price?", ('Yes','No')) # If prices are quite low, but greater than zero, force charge is possible
    force_charge = 1 if force_charge == 'Yes' else 0
    force_charge_price = float(left_col.text_input("Force charge threshold", value = 285)) # Price threshold of force charge
    force_stop = mid_col.selectbox("Force stop above a certain price?", ('Yes','No')) # If prices are quite high, force discharge is possible
    force_stop = 1 if force_stop == 'Yes' else 0
    force_stop_price = float(right_col.text_input("Force stop threshold", value = 600)) # Price threshold of force discharge
    eta = float(left_col.text_input('Charge/Discharge efficiency', value = '0.98')) 
    start_time = mid_col.text_input('Plugin time in hh:mm', value = '12:00') # Start point of EV plug-in duration
    end_time = right_col.text_input('plugout time in hh:mm (>plugin, <23:59)', value = '20:00') # End point of EV plug-in duration
    onsite_resources = left_col.selectbox("Make use of onsite resources: ", ('Yes','No')) # Allow use of onsite solar
    onsite_resources = 1 if onsite_resources == 'Yes' else 0
    solar_capacity = float(mid_col.text_input("Installed solar capacity in kW: ", value = 4)) 
    solar_csv_name = right_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    inflex_start_time = left_col.text_input('Start time of inflexible load in hh:mm', value = '19:00') # Power of infexible load that uses vehicle power
    inflex_end_time = mid_col.text_input('End time of inflexible load in hh:mm', value = '20:00')
    power_inflexible_load = float(right_col.text_input('Power rating of inflexible load in kW', value = '2'))
    solar_day = int(mid_col.text_input('Solar day integer from 0 to 363', value = '50'))
    solve_model = left_col.selectbox('Solve model', ('Linear programming', 'MILP'))

# process input timeseries
hour = pd.date_range(date.today(), periods=24, freq="H")
day_ahead.index = hour
day_ahead = day_ahead.resample('15T').ffill()
price = day_ahead[0].values 
prices = np.append(price, np.array(3*[price[-1]]))
solar_data = solar_data.resample('15T').mean().interpolate(method='linear')
solar_data = solar_data['electricity'].values
EV_flexible_window = [start_time, end_time] # Time in hh:mm
inflexible_window = [inflex_start_time, inflex_end_time]

time_step_per_hour = 60 // time_granularity

# process input timestamps to bring it to nearest 15th minute
EV_start_time = EV_flexible_window[0].split(':')
EV_start_time = int(EV_start_time[0])*time_step_per_hour + int(np.ceil(int(EV_start_time[1])/time_granularity))

EV_end_time = EV_flexible_window[1].split(':')
EV_end_time = int(EV_end_time[0])*time_step_per_hour + int(np.floor(int(EV_end_time[1])/time_granularity))

inflex_start_time = inflexible_window[0].split(':')
inflex_start_time = int(inflex_start_time[0])*time_step_per_hour + int(np.ceil(int(inflex_start_time[1])/time_granularity))

inflex_end_time = inflexible_window[1].split(':')
inflex_end_time = int(inflex_end_time[0])*time_step_per_hour + int(np.floor(int(inflex_end_time[1])/time_granularity))

optimization_horizon = 24 # hours

EV_flexible_window_timesteps = [EV_start_time, EV_end_time]
SimLength = optimization_horizon*time_step_per_hour # Within a day charge cycle

SimLength = int(SimLength)
solar_data = solar_data[solar_day*24*time_step_per_hour:solar_day*24*time_step_per_hour+SimLength]*solar_capacity # choice of solar day
inflexible_load = np.zeros(SimLength)
inflexible_load[inflex_start_time:inflex_end_time] = power_inflexible_load # schedule a constant power inflexible load
prices = prices[:SimLength]

# define reward and penalty for unusual prices
reward_force_charge = np.array([])
for price_value in prices:
    if price_value < force_charge_price:
        reward_force_charge = np.append(reward_force_charge, -100000)
    else:
        reward_force_charge = np.append(reward_force_charge, 0)

reward_ultra_high_v2g = np.array([])
for price_value in prices:
    if price_value > force_stop_price:
        reward_ultra_high_v2g = np.append(reward_ultra_high_v2g, 100000)
    else:
        reward_ultra_high_v2g = np.append(reward_ultra_high_v2g, 0)

p_EV = plug_in_power/time_step_per_hour # take power as p/4 for the consideration of charging in 15 minute interval. However, at anypoint, the power withdrawn from outlet is plugin power

soc_min = 0.2*battery_size # suggested that we do not discharge below 20% in case of V2G
soc_max = 0.9*battery_size # suggested that we do not go above 90% of battery capacity for preservation
if soc_start >= soc_max:
    soc_start = soc_max
elif soc_start <= 0:
    soc_start = 0
soc_deadline = distance_next_trip*average_kWh_km + soc_min # the minimum charging needed for the next time window, 
soc_max_plugin = soc_start + (p_EV*eta)*(EV_flexible_window_timesteps[1] - EV_flexible_window_timesteps[0])
# maximum soc that can be reached when left plugged in for the whole duration

if soc_deadline > soc_max: 
    soc_deadline = soc_max # cannot charge beyond max
if soc_max_plugin>soc_max:
    soc_max_plugin = soc_max # cannot charge beyond max
soc_end = soc_deadline if soc_max_plugin>soc_deadline else soc_max_plugin

if solve_model == 'Linear programming':
    EV_status, V2G_status, solar_charge, soc = EV_optimize_LP(SimLength, prices, inflexible_load, force_charge, reward_force_charge, 
            force_stop, reward_ultra_high_v2g, plug_in_power, soc_start, soc_max, soc_min, v2g_feasibility, solar_data, onsite_resources, 
            eta, EV_flexible_window_timesteps, soc_deadline, time_step_per_hour)

else:
    EV_status, V2G_status, solar_charge, soc = EV_optimize_MILP(SimLength, prices, inflexible_load, force_charge, reward_force_charge, 
                force_charge, reward_ultra_high_v2g, plug_in_power, soc_start, soc_max, soc_min, v2g_feasibility, solar_data, 
                onsite_resources, eta, EV_flexible_window_timesteps, soc_deadline, time_step_per_hour)

# Uncontrolled charging strategy
uncontrolled_to_optimal_soc_status = np.zeros(len(prices))
uncontrolled_to_optimal_soc_timesteps = int(np.ceil((soc_deadline - soc_start)/(plug_in_power*eta/time_step_per_hour)))
uncontrolled_to_optimal_soc_timesteps = min(uncontrolled_to_optimal_soc_timesteps, EV_flexible_window_timesteps[1] - EV_flexible_window_timesteps[0])
uncontrolled_to_optimal_soc_status[EV_flexible_window_timesteps[0]:EV_flexible_window_timesteps[0]+uncontrolled_to_optimal_soc_timesteps] = plug_in_power
solar_uncontrolled_to_optimal_soc_status = np.minimum(uncontrolled_to_optimal_soc_status+inflexible_load, solar_data)
soc_uncontrolled_to_optimal_soc = np.zeros(len(prices))
soc_uncontrolled_to_optimal_soc[0] = soc_start
# Handling the edge case
for i in range(1,len(prices)):
    soc_uncontrolled_to_optimal_soc[i] = soc_uncontrolled_to_optimal_soc[i-1] + uncontrolled_to_optimal_soc_status[i-1]*eta/time_step_per_hour
if soc_uncontrolled_to_optimal_soc[-1] > soc_max:
    uncontrolled_to_optimal_soc_status[EV_flexible_window_timesteps[0]+uncontrolled_to_optimal_soc_timesteps-1] = soc_max - soc_uncontrolled_to_optimal_soc[[EV_flexible_window_timesteps[0]+uncontrolled_to_optimal_soc_timesteps-1]]
    for i in range(1,len(prices)):
        soc_uncontrolled_to_optimal_soc[i] = soc_uncontrolled_to_optimal_soc[i-1] + uncontrolled_to_optimal_soc_status[i-1]*eta/time_step_per_hour

fig_soc, fig_status, fig_status_uncontrolled = EV_plot_gen(SimLength, soc, soc_min, soc_max, soc_deadline, plug_in_power, EV_status, V2G_status, battery_size, 
                                    EV_flexible_window_timesteps, solar_charge, solar_data, inflexible_load, solve_model, prices, 
                                    uncontrolled_to_optimal_soc_status, soc_uncontrolled_to_optimal_soc, solar_uncontrolled_to_optimal_soc_status)

plots = st.container()
with plots:
    st.header('Plots')
    st.plotly_chart(fig_soc)
    st.plotly_chart(fig_status)
    st.plotly_chart(fig_status_uncontrolled)