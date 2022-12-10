# This is the script that takes inputs for running thermal comfort optimization (heat planning)
import numpy as np
import pandas as pd
from datetime import date
import streamlit as st
import os
from app_heating_func import heat_plan, heat_plan_MILP
from Plots import heat_plots
from pathlib import Path

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

# Streamlit containers
header = st.container()
dataset = st.container()
left_col, mid_col, right_col = st.columns(3)

with header:
    st.title('Heating Optimization')
    st.header('This optimization utilizes on site generation to gain economic benefits at the end consumer level')

# Take inputs for running the simulation
hour = pd.date_range(date.today(), periods=24, freq="H") # time array to resample time-series

with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',))) # time granularity of the simulation
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price_high','Price')) # Price curve for (based on day-ahead curve)
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    day_ahead.index = hour
    day_ahead = day_ahead.resample('15T').ffill()
    price = day_ahead[0].values
    prices = np.append(price, np.array(3*[price[-1]]))

    T_out_csv = right_col.selectbox("Ambient temperature °C (60-min)", ('T_out_Zurich',)) # Ambient temperature for the home
    T_out = pd.read_csv(f'{data_dir}\{T_out_csv}.csv', skiprows=3, index_col = 0, parse_dates=True)
    T_out = T_out.resample('15T').mean().interpolate(method='linear')
    T_out = T_out['temperature'].values
    T_out_array = np.append(T_out, np.array(3*[T_out[-1]]))

    T_start = float(left_col.text_input('Start temperature in °C', value = '15')) # Initial temperature in the home
    temp_set = mid_col.selectbox("Setpoint in °C for 24houtrs", ('T_set',)) # Temperature setpoint for the home
    T_set = pd.read_csv(f'{data_dir}\{temp_set}.csv', header = None)
    T_set.index = hour
    T_set_array = T_set.resample('15T').ffill()
    T_set_array = T_set_array[0].values 
    T_set_array = np.append(T_set_array, np.array(3*[T_set_array[-1]]))

    temperature_deadband = float(right_col.text_input('Temperature tolerance in °C', value = '2')) # Temperature band within which deviation is allowed
    heater_power = float(left_col.text_input('Device power in W', value = '2500')) # Power of the heater
    allow_deadband_flexibility = mid_col.selectbox("Allow DB flexibility (DBF)?", ('Yes', 'No')) # Allowing deadband flexibility during high priced hours
    allow_deadband_flexibility = 1 if allow_deadband_flexibility == 'Yes' else 0
    allow_deadband_flexibility_price = float(right_col.text_input("DBF price threshold (€/MWh)", value = 600)) # Price threshold to activate deadband flexibility

    R = float(mid_col.text_input("Thermal resistivity in °C/Watt", value = '0.0405')) # Thermal resistivity of the home
    tao = float(mid_col.text_input("Time constant in hour", value = '2')) # Thermal time constant

    solar_capacity = float(left_col.text_input("Installed solar capacity in kW: ", value = 4)) # Installed solar power capacity
    solar_csv_name = right_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True) # Solar profile for the day
    solar_data = solar_data.resample('15T').mean().interpolate(method='linear')
    solar_data = solar_data['electricity'].values
    solar_data = np.append(solar_data, np.array(3*[solar_data[-1]]))

    day = int(right_col.text_input('Day of the year (integer b/w 0 to 363)', value = '50')) # Day of the year
    solve_model = left_col.selectbox('Solve model', ('Variable power', 'Constant power')) # Model to use (Linear programming and MILP)

optimization_horizon = 24 # 24 hour as we consider day ahead optimization
time_step_per_hour = 60//time_granularity # number of time steps per hour
C = (tao*3600/R) # thermal capacity of the room
simLength = int(optimization_horizon*60/time_granularity)

# Generate heat plan based on chosen solve model
if solve_model == 'Constant power':
    heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data\
    = heat_plan_MILP(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
 solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour)
else:
    heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data\
        = heat_plan(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
    solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour)
    
# Base model for temperature control - based on bang-bang control for heaters
# Logic: The initial heater state is chosen based on the temperature - On or Off (if not guided by temperature, then at random)
# We want to maintain temperature between the comfort bounds using the feedback controller
length = len(temperature.value)
bang_bang_control_status = np.zeros(optimization_horizon*time_step_per_hour)
bang_bang_control_temp = np.zeros(optimization_horizon*time_step_per_hour)
bang_bang_control_temp[0] = T_start
if bang_bang_control_temp[0] >= T_upper_bound[0]:
    bang_bang_control_status[0] = 0
elif bang_bang_control_temp[0] <= T_upper_bound[0]:
    bang_bang_control_status[0] = heater_power
else:
    bang_bang_control_status[0] = np.random.choice([0,1])
for i in range(1,length):
    bang_bang_control_temp[i] = T_out[i] + bang_bang_control_status[i-1]*R/time_step_per_hour - (T_out[i] + bang_bang_control_status[i-1]*R/time_step_per_hour - bang_bang_control_temp[i-1])*np.exp(-1*(4*60)/(R*C))

    if bang_bang_control_temp[i] >= T_upper_bound[i]:
        bang_bang_control_status[i] = 0
    elif bang_bang_control_temp[i] <= T_lower_bound[i]:
        bang_bang_control_status[i] = heater_power
    else:
        bang_bang_control_status[i] = bang_bang_control_status[i-1]
bang_bang_solar = np.minimum(solar_data, bang_bang_control_status/1000)

# Figure to show appliance status over different charging configurations and the price of electricity
fig_temp, optimal_status, bangbangcontrol = heat_plots(temperature, bang_bang_control_temp, T_upper_bound, T_lower_bound, T_set_array, T_out, solar_data, solar_charge, heater_status, prices,
                bang_bang_control_status, bang_bang_solar, heater_power, solve_model)
plots = st.container()
with plots:
    st.header('Plots')
    st.plotly_chart(fig_temp)
    st.plotly_chart(optimal_status)
    st.plotly_chart(bangbangcontrol)

