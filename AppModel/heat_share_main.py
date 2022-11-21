# import necessary libraries
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import cvxpy as cp
import streamlit as st
import os
import time
from pathlib import Path

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

# Streamlit containers
header = st.container()
dataset = st.container()
left_col, mid_col, right_col = st.columns(3)

with header:
    st.title('Mutli-Heater optimization')
    st.header('This optimization operates the heater based on the time of use pricing and availability of on-site resources. This is a multi-heater optimization problem, which compares the approach of independent heaters and heat sharing')

with dataset:
    time_granularity = int(left_col.selectbox('Time granularity (min)', ('15',)))
    csv_name = mid_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price', 'Price_high'))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    T_out_csv = right_col.selectbox("Ambient temperature °C (60-min)", ('T_out_Zurich',))
    T_out = pd.read_csv(f'{data_dir}\{T_out_csv}.csv', skiprows=3, index_col = 0, parse_dates=True)
    temperature_deadband = float(right_col.text_input('Temperature tolerance in °C', value = '2'))
    heater_power = float(left_col.text_input('Device power in W', value = '2500'))
    solar_csv_name = mid_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    solar_cap_csv = left_col.text_input("Input solar capacity", value = 'solar_capacity')
    solar_capacity = pd.read_csv(f'{data_dir}\{solar_cap_csv}.csv', header=None).values
    T_set_csv = left_col.text_input("Setpoint Temperature as .csv", value = 'T_set_share')
    T_set = pd.read_csv(f'{data_dir}\{T_set_csv}.csv', header=None).values
    T_start_csv = right_col.text_input("Start Temperature as .csv", value = 'T_start_share')
    T_start = pd.read_csv(f'{data_dir}\{T_start_csv}.csv', header=None).values
    R_csv = left_col.text_input("Heating resistivity as .csv", value = 'R_share')
    R = pd.read_csv(f'{data_dir}\{R_csv}.csv', header=None).values
    tao_csv = right_col.text_input("Time constant as .csv", value = 'tao_share')
    tao = pd.read_csv(f'{data_dir}\{tao_csv}.csv', header=None).values
    heater_power_csv = left_col.text_input("Heater power as .csv", value = 'heater_power_share')
    heater_power = pd.read_csv(f'{data_dir}\{heater_power_csv}.csv', header=None).values
    dead_band = float(right_col.text_input("Input tolerance deadband in °C", value = 2))
    onsite_resources = left_col.selectbox("Make use of onsite resources", ('Yes', 'No'))
    onsite_resources = 1 if onsite_resources == 'Yes' else 0
    allow_deadband_flexibility = mid_col.selectbox("Allow DB flexibility (DBF)?", ('Yes', 'No'))
    allow_deadband_flexibility = 1 if allow_deadband_flexibility == 'Yes' else 0
    allow_deadband_flexibility_price = float(right_col.text_input("DBF price threshold (€/MWh)", value = 600))

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

C = (tao*3600/R)
def heat_plan(T_start = T_start, T_set = T_set, dead_band = dead_band, heater_power = heater_power, T_out = T_out, prices = prices, R = R, tao = tao, 
              time_granularity = time_granularity, solar_data=solar_data, solar_capacity = solar_capacity, allow_deadband_flexibility = allow_deadband_flexibility, 
              allow_deadband_flexibility_price = allow_deadband_flexibility_price):
    
    C = (tao*3600/R)
    time_step_per_hour = 60//time_granularity
    SimLength = 24*time_step_per_hour
    number_of_houses = T_start.shape[1]

    prices = prices[:SimLength]
    # solar_data = solar_data[24*time_step_per_hour*50:24*time_step_per_hour*50+SimLength] # this is hard-coded to get a nice sunny day
    solar_data = solar_data[50*24*4:50*24*4+SimLength]
    T_out_array = T_out[50*24*4:50*24*4+SimLength]
    solar_data_multi_home = np.zeros((SimLength, number_of_houses))
    T_out = np.zeros((SimLength, number_of_houses))
    for house_number in range(number_of_houses):
        solar_data_multi_home[:, house_number] = solar_data
        T_out[:, house_number] = T_out_array

    solar_data_multi_home = solar_data_multi_home*solar_capacity

    heater_power_array = np.zeros((SimLength, number_of_houses))
    for timestep in range(SimLength):
        heater_power_array[timestep, :] = heater_power[0]
    print(heater_power_array)
    heater_status = cp.Variable((SimLength, number_of_houses))
    
    temperature = cp.Variable((SimLength, number_of_houses))
    T = temperature[:-1]
    T_plus_1 = temperature[1:]
    t_lower_slack = cp.Variable((SimLength, number_of_houses))
    t_upper_slack = cp.Variable((SimLength, number_of_houses))
    T_upper_bound = T_set + dead_band/2
    T_lower_bound = T_set - dead_band/2

    if allow_deadband_flexibility == 1:
        for i in range (len(prices)):
            if prices[i] > allow_deadband_flexibility_price:
                T_lower_bound[i] = T_lower_bound[i] - 1
    

    # T_plus_1[:, 0] == T_out[1:, 1:] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - cp.multiply((T_out[1:, 1:] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - T[:, 0]), np.exp(-1*(time_step_per_hour*60)/(R[:-1, 0]*C[:-1, 0]))),
    st.write(T_plus_1[:, 0].shape)
    solar_charge = cp.Variable((SimLength, number_of_houses))

    objective = cp.Minimize(cp.sum(prices@(heater_status - solar_charge)/time_step_per_hour) - 100000*cp.sum(t_lower_slack) - 10000*cp.sum(t_upper_slack)) # objective is to minimize the energy consumption cosr as well as ensure that the battery is charge to be able to drive in the next driving instance. It must be ensured that there is always a tendency to overcharge than undercharge. Here the units are not matched, with power in kW and prices in EUR/MWh, must be corrected while actual price calculation
    constraints = [heater_status >= 0, heater_status <= heater_power_array/1000,
                   temperature[0] == T_start[0,:], 
                #    T_plus_1 == T_out[1:] + cp.multiply(heater_status[:-1], R[:-1])*1000/4 - cp.multiply((T_out[1:] + cp.multiply(heater_status[:-1], R[:-1])*1000/4 - T[:]), np.exp(-1*(4*60)/(R[:-1]*C[:-1]))),
                   T_plus_1[:, 0] == T_out[1:, 0] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - cp.multiply((T_out[1:, 0] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - T[:, 0]), np.exp(-1*(time_step_per_hour*60)/(R[:-1, 0]*C[:-1, 0]))),
                   T_plus_1[:, 1:] == T_out[1:, 1:] + cp.multiply(heater_status[:-1, 1:]*0.7, R[:-1, 1:])*1000/time_step_per_hour - cp.multiply((T_out[1:, 1:] + cp.multiply(heater_status[:-1, 1:]*0.7, R[:-1, 1:])*1000/time_step_per_hour - T[:, 1:]), np.exp(-1*(time_step_per_hour*60)/(R[:-1, 1:]*C[:-1, 1:]))),
                   t_lower_slack <= 0, t_lower_slack <= temperature-T_lower_bound, t_upper_slack <= 0, t_upper_slack <= T_upper_bound - temperature,  
                   solar_charge <= solar_data_multi_home, solar_charge <= heater_status*onsite_resources, solar_charge >= 0,
                  ]

    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'MOSEK', verbose = True)

    heater_status_share = cp.Variable(T_out.shape)
    heater_status_dependents = cp.Variable(T_out.shape)

    return prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, number_of_houses, time_step_per_hour, T_start, solar_data_multi_home\
            

prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, number_of_houses, time_step_per_hour, T_start, solar_data_multi_home\
= heat_plan(T_start = T_start, T_set = T_set, dead_band = dead_band, heater_power = heater_power, T_out = T_out, prices = prices, R = R, tao = tao, time_granularity = time_granularity)


plots = st.container()
with plots:
    carbon_intensity_electricity = left_col.text_input("Carbon intensity of electricity in gCO2/kWh", value = 33)
    carbon_intensity_gas = left_col.text_input("Carbon intensity of electricity in gCO2/kWh", value = 50)
    house_number = right_col.text_input(f"Temperature evolution for house number between 0 to {number_of_houses - 1}", value = 2)
house_number = int(house_number)
carbon_intensity_electricity = float(carbon_intensity_electricity)
carbon_intensity_gas = float(carbon_intensity_gas)

time_axis = pd.date_range(date.today(), periods=len(temperature.value), freq="15min")    

fig = make_subplots(specs=[[{"secondary_y": True}]])
def fig_format(fig):
    fig.update_layout({'plot_bgcolor': 'rgba(255,255,255,0)', 'paper_bgcolor': 'rgba(255,255,255,0)',})
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', showgrid = True, gridcolor='rgba(224,224,224,50)',)
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', showgrid = False, gridcolor='rgba(224,224,224,30)',)
    fig.update_layout(autosize=False, width=1000, height=500, font_family = 'Computer Modern', font_size = 18)
    fig.update_layout(legend=dict(orientation="h",yanchor="top", y = -0.2))
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=time_axis, y=temperature.value[:,house_number], name='Temperature optimal control', line=dict(color = 'red')), secondary_y=False)
fig.add_trace(go.Scatter(x=time_axis, y=T_upper_bound[:,house_number], name='Upper temperature bound', line=dict(color = 'black', dash = 'dash')), secondary_y=False)
fig.add_trace(go.Scatter(x=time_axis, y=T_lower_bound[:,house_number], name='Lower temperature bound', line=dict(color = 'black', dash = 'dot')), secondary_y=False)
# fig.add_trace(go.Scatter(x=time_axis, y=T_out_array, name='Outside temperature + 10°C', line=dict(color='moccasin')), secondary_y=False)
fig.add_trace(go.Scatter(x=time_axis, y=T_set[:,house_number], name='Temperature set-point', line=dict(color = 'gray', dash = 'dot')), secondary_y=False)
# fig.add_trace(go.Scatter(x=time_axis, y=prices/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
fig.update_yaxes(title_text="Temperature in °C", secondary_y=False)
fig.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
fig_format(fig)
fig.update_layout(title = 'Temperature Evolution Independent Setup')

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_number], name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
fig1.add_trace(go.Scatter(x=time_axis, y=heater_status.value[:,house_number], name='Heater', line=dict(color='orchid')), secondary_y=False)
fig1.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_number], name='Solar power consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
fig1.add_trace(go.Scatter(x=time_axis, y=prices/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
fig1.update_yaxes(title_text="Power in kW", secondary_y=False)
fig1.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
fig1.update_layout(autosize=False, width=1000, height=500, font_family = 'Computer Modern')
fig_format(fig1)
fig1.update_layout(title = 'Heater Status Independent Setup')



fig2 = make_subplots(specs=[[{"secondary_y": True}]])
fig2.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_number], name='Solar Production', line=dict(color='#d62728')), secondary_y=False)
fig2.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_number], name='Solar power consumption optimal control', line=dict(color='#bcbd22')), secondary_y=False)
fig2.update_yaxes(title_text="Power in kW", secondary_y=False)
fig2.update_layout(title = 'Individual Setup')
fig2.update_layout(autosize=False, width=1000, height=500)



with plots:
    st.header('Plots')
    st.plotly_chart(fig)
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)