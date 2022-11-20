# This is the script for EV charging Optimization - Capability of only one way energy transfer (Grid to Vehicle)
# import necessary libraries
from turtle import width
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import cvxpy as cp
import streamlit as st
import os
import time

# This is a function to find the lowest cost of charging for a given plugin duration to achieve a certain level of charging
def heat_plan(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
 solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour):
    # we define the time window of optimization based on the plugin and plugout time. If that happens within a day, we don't consider rollover, else we do
    
    
    solar_data = solar_data[day*24*time_step_per_hour:day*24*time_step_per_hour+simLength]*solar_capacity
    T_out = T_out[day*24*time_step_per_hour:day*24*time_step_per_hour+simLength]

    T_upper_bound = T_set_array + temperature_deadband/2
    T_lower_bound = T_set_array - temperature_deadband/2
    if allow_deadband_flexibility == 1:
        for i in range (len(prices)):
            if prices[i] > allow_deadband_flexibility_price:
                T_lower_bound[i] = T_lower_bound[i] - 2
    simLength = int(optimization_horizon*60/time_granularity)

    heater_status = cp.Variable(simLength)
    temperature = cp.Variable(simLength)
    T = temperature[:-1]
    T_plus_1 = temperature[1:]
    zero_array = np.zeros(simLength)
    t_lower_slack = cp.Variable(simLength)
    t_upper_slack = cp.Variable(simLength)

    solar_charge = cp.Variable(simLength)
    zero_array = np.zeros(simLength,)

    C = (tao*3600/R)


    objective = cp.Minimize(cp.sum(prices@(heater_status/1000-solar_charge)/4) - 1000000*cp.sum(t_lower_slack) - 10000*cp.sum(t_upper_slack)) # objective is to minimize the energy consumption cosr as well as ensure that the battery is charge to be able to drive in the next driving instance. It must be ensured that there is always a tendency to overcharge than undercharge. Here the units are not matched, with power in kW and prices in EUR/MWh, must be corrected while actual price calculation
    constraints = [heater_status>=0, heater_status<=heater_power, temperature[0] == T_start, # appliance can be either on or off, assumed that soc at time 0 is same as soc at time of start of charge
                  T_plus_1 == T_out[1:] + heater_status[:-1]*R/time_step_per_hour - (T_out[1:] + heater_status[:-1]*R/time_step_per_hour - T)*np.exp(-1*(4*60)/(R*C)),
                  t_lower_slack <= 0, t_lower_slack <= temperature-T_lower_bound, t_upper_slack <= 0, t_upper_slack <= T_upper_bound - temperature, 
                  solar_charge>= zero_array, solar_charge <= heater_status/1000, solar_charge <= solar_data]
    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'MOSEK', verbose = True)

    return heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data

def heat_plan_MILP(T_start, T_set_array, temperature_deadband, heater_power, T_out , prices, R, tao, time_granularity, optimization_horizon,
 solar_data, allow_deadband_flexibility_price, allow_deadband_flexibility, simLength, solar_capacity, day, time_step_per_hour):
    # we define the time window of optimization based on the plugin and plugout time. If that happens within a day, we don't consider rollover, else we do
    
    
    solar_data = solar_data[day*24*time_step_per_hour:day*24*time_step_per_hour+simLength]*solar_capacity
    T_out = T_out[day*24*time_step_per_hour:day*24*time_step_per_hour+simLength]

    T_upper_bound = T_set_array + temperature_deadband/2
    T_lower_bound = T_set_array - temperature_deadband/2
    if allow_deadband_flexibility == 1:
        for i in range (len(prices)):
            if prices[i] > allow_deadband_flexibility_price:
                T_lower_bound[i] = T_lower_bound[i] - 2
    simLength = int(optimization_horizon*60/time_granularity)

    heater_status = cp.Variable(simLength, integer = True)
    temperature = cp.Variable(simLength)
    T = temperature[:-1]
    T_plus_1 = temperature[1:]
    zero_array = np.zeros(simLength)
    t_lower_slack = cp.Variable(simLength)
    t_upper_slack = cp.Variable(simLength)

    solar_charge = cp.Variable(simLength)
    zero_array = np.zeros(simLength,)

    C = (tao*3600/R)


    objective = cp.Minimize(cp.sum(prices@(heater_status/1000-solar_charge)/4) - 1000000*cp.sum(t_lower_slack) - 10000*cp.sum(t_upper_slack)) # objective is to minimize the energy consumption cosr as well as ensure that the battery is charge to be able to drive in the next driving instance. It must be ensured that there is always a tendency to overcharge than undercharge. Here the units are not matched, with power in kW and prices in EUR/MWh, must be corrected while actual price calculation
    constraints = [heater_status>=0, heater_status<=1, temperature[0] == T_start, # appliance can be either on or off, assumed that soc at time 0 is same as soc at time of start of charge
                  T_plus_1 == T_out[1:] + heater_power*heater_status[:-1]*R/time_step_per_hour - (T_out[1:] + heater_power*heater_status[:-1]*R/time_step_per_hour - T)*np.exp(-1*(4*60)/(R*C)),
                  t_lower_slack <= 0, t_lower_slack <= temperature-T_lower_bound, t_upper_slack <= 0, t_upper_slack <= T_upper_bound - temperature, 
                  solar_charge>= zero_array, solar_charge <= heater_power*heater_status/1000, solar_charge <= solar_data]
    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'MOSEK', verbose = True)

    return heater_status, T_lower_bound, T_upper_bound, T_out, temperature, solar_charge, solar_data