"""
This code is to implement the functions for EV-flexibility using optimization (MILP and LP) for single vehicle
The functions are quite similar apart from the use of the variables related to power consumption - ev and v2h
ev - EV charging
v2h - EV discharging using vehicle to home (or vehicle to grid operation)
Imputs for the functions are:
EV size
EV charge power
EV plugin time
EV plugout time
Solar power integration power
Solar profile
Day for solar power use
Allowability of use of v2h and solar power
Input for an inflexible load (use time and power consumption)
"""
import cvxpy as cp
import numpy as np

def unint_scheduler(SimLength, power_inflexible_load, time_of_run, flexible_window_timesteps, price, time_granularity, solar_capacity, solar_data, day):

    prices = price[:SimLength]
    time_steps_per_hour = 60//time_granularity
    solar_data = solar_data[day*24*time_steps_per_hour:SimLength+day*24*time_steps_per_hour]*solar_capacity
    appliance_run_timesteps = int(np.ceil(time_of_run*60/time_granularity))

    p = (power_inflexible_load/(60/time_granularity))/1000 # kW
    appliance_profile_stack = np.zeros((flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1,SimLength))
    for row in range(flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1):
        appliance_profile_stack[row,flexible_window_timesteps[0] + row:flexible_window_timesteps[0] + row + appliance_run_timesteps] = p*4
    appliance_profile_stack = appliance_profile_stack.transpose()
    base_profile = np.zeros(SimLength)
    base_profile[flexible_window_timesteps[0]:flexible_window_timesteps[0]+appliance_run_timesteps] = p*4

    solar_charge = cp.Variable(SimLength)
    print(flexible_window_timesteps)
    status_stack = cp.Variable((flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1,), integer = True)

    obj_fn_0 = appliance_profile_stack@status_stack


    objective = cp.Minimize(cp.sum((obj_fn_0/4-solar_charge/4)@prices))
    constraints = [status_stack >= 0, status_stack <= 1, cp.sum(status_stack) == 1, 
                  solar_charge>= 0, solar_charge<=solar_data, solar_charge <= appliance_profile_stack@status_stack, # solar consumption is always greater than equal to zero, and less than what is available due to irradiation and required by the appliance]
                  ]

    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'GUROBI', verbose = True)
    energy_consumption_cost_optimal = (cp.sum((obj_fn_0/4-solar_charge/4)@prices)).value/1000
    energy_consumption_cost_base = base_profile@prices/4000
    return status_stack, appliance_profile_stack, prices, solar_charge, solar_data, base_profile, energy_consumption_cost_optimal, energy_consumption_cost_base

    st.write
