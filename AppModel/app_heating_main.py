# This is the script for EV charging Optimization - Capability of only one way energy transfer (Grid to Vehicle)
# import necessary libraries
import numpy as np
import pandas as pd
from datetime import date
import streamlit as st
import os
from app_heating_func import heat_plan, heat_plan_MILP
from app_heating_plot import heat_plots
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

with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',)))
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price_high','Price'))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    T_out_csv = right_col.selectbox("Ambient temperature °C (60-min)", ('T_out_Zurich',))
    T_out = pd.read_csv(f'{data_dir}\{T_out_csv}.csv', skiprows=3, index_col = 0, parse_dates=True)
    T_start = float(left_col.text_input('Start temperature in °C', value = '15'))
    temp_set = mid_col.selectbox("Setpoint in °C for 24houtrs", ('T_set',))
    T_set = pd.read_csv(f'{data_dir}\{temp_set}.csv', header = None)
    temperature_deadband = float(right_col.text_input('Temperature tolerance in °C', value = '2'))
    heater_power = float(left_col.text_input('Device power in W', value = '2500'))
    allow_deadband_flexibility = mid_col.selectbox("Allow DB flexibility (DBF)?", ('Yes', 'No'))
    allow_deadband_flexibility = 1 if allow_deadband_flexibility == 'Yes' else 0
    allow_deadband_flexibility_price = float(right_col.text_input("DBF price threshold (€/MWh)", value = 600))
    R = float(mid_col.text_input("Thermal resistivity in °C/Watt", value = '0.0405'))
    tao = float(mid_col.text_input("Time constant in hour", value = '2'))
    peak_house_load = float(right_col.text_input('Peak house load in kW', value = '10'))
    solar_capacity = float(left_col.text_input("Installed solar capacity in kW: ", value = 4))
    solar_csv_name = mid_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    day = int(right_col.text_input('Solar day integer from 0 to 365', value = '50'))
    solve_model = left_col.selectbox('Solve model', ('Linear programming', 'MILP'))
    optimization_horizon = int(right_col.text_input('Days as hours', value = '24'))

time_step_per_hour = 60//time_granularity
C = (tao*3600/R)
# This section is present to define the day ahead prices - taken from ENTSO-E transparency platform
# seven days, 48 hours and using a 15 minute granularity. The initial array is taken as repetition of same day ahead prices as EV charging often faces and overspill to next day

solar_data = solar_data.resample('15T').mean().interpolate(method='linear')
solar_data = solar_data['electricity'].values
solar_data = np.append(solar_data, np.array(3*[solar_data[-1]]))

T_out = T_out.resample('15T').mean().interpolate(method='linear')
T_out = T_out['temperature'].values
T_out_array = np.append(T_out, np.array(3*[T_out[-1]]))

hour = pd.date_range(date.today(), periods=24, freq="H")

day_ahead.index = hour
day_ahead = day_ahead.resample('15T').ffill()
price = day_ahead[0].values
prices = np.append(price, np.array(3*[price[-1]]))

T_set.index = hour
T_set_array = T_set.resample('15T').ffill()
T_set_array = T_set_array[0].values 
T_set_array = np.append(T_set_array, np.array(3*[T_set_array[-1]]))

simLength = int(optimization_horizon*60/time_granularity)


# This is a function to find the lowest cost of charging for a given plugin duration to achieve a certain level of charging

if solve_model == 'MILP':
    heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data\
    = heat_plan_MILP(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
 solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour)
else:
    heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data\
        = heat_plan(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
    solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour)
    

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

fig_temp, optimal_status, bangbangcontrol = heat_plots(temperature, bang_bang_control_temp, T_upper_bound, T_lower_bound, T_set, T_out, solar_data, solar_charge, heater_status, prices,
                bang_bang_control_status, bang_bang_solar, heater_power, solve_model)
plots = st.container()
with plots:
    st.header('Plots')
    st.plotly_chart(fig_temp)
    st.plotly_chart(optimal_status)
    st.plotly_chart(bangbangcontrol)

