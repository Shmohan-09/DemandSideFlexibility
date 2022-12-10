import cvxpy as cp
import numpy as np

def unint_scheduler(SimLength, power_inflexible_load, time_of_run, flexible_window_timesteps, price, time_granularity, solar_capacity, solar_data, day, optimization_horizon):

    prices = price[:SimLength]
    time_steps_per_hour = 60//time_granularity
    solar_data = solar_data[day*24*time_steps_per_hour:SimLength+day*24*time_steps_per_hour]*solar_capacity
    appliance_run_timesteps = int(np.ceil(time_of_run*60/time_granularity))

    p = (power_inflexible_load/(60/time_granularity))/1000 # kW
    # an appliance stack is created such that each row contains the load profile
    appliance_profile_stack = np.zeros((flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1,SimLength))
    for row in range(flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1):
        appliance_profile_stack[row,flexible_window_timesteps[0] + row:flexible_window_timesteps[0] + row + appliance_run_timesteps] = p*4
    appliance_profile_stack = appliance_profile_stack.transpose()
    # a base profile array is defined such that it gives usual operation of the device
    base_profile = np.zeros(SimLength)
    base_profile[flexible_window_timesteps[0]:flexible_window_timesteps[0]+appliance_run_timesteps] = p*4

    solar_charge = cp.Variable(SimLength)
    print(flexible_window_timesteps)

    # The status stack is an integer variable array, which chooses a profile from the appliance profile stack so as to minimize the power consumption costs.
    status_stack = cp.Variable((flexible_window_timesteps[1] - flexible_window_timesteps[0] - appliance_run_timesteps + 1,), integer = True)

    obj_fn_0 = appliance_profile_stack@status_stack


    objective = cp.Minimize(cp.sum((obj_fn_0/4-solar_charge/4)@prices)) # minimize power consumption costs considering solar power consumption and electricity prices.
    constraints = [status_stack >= 0, status_stack <= 1, cp.sum(status_stack) == 1, 
                  solar_charge>= 0, solar_charge<=solar_data, solar_charge <= appliance_profile_stack@status_stack, # solar consumption is always greater than equal to zero, and less than what is available due to irradiation and required by the appliance]
                  ]

    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'GUROBI', verbose = True)
    energy_consumption_cost_optimal = (cp.sum((obj_fn_0/4-solar_charge/4)@prices)).value/1000
    energy_consumption_cost_base = base_profile@prices/4000
    return status_stack, appliance_profile_stack, prices, solar_charge, solar_data, base_profile, energy_consumption_cost_optimal, energy_consumption_cost_base