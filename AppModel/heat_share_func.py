# The function is quite similar to heat planning function and thus scarcely commented. Only the important parts are commented.
import numpy as np
import cvxpy as cp

# This function definies individual optimization of the households
def multi_heater_individual(T_start, T_set, dead_band, heater_power, T_out_array, prices, R, tao, 
              time_granularity, solar_data, solar_capacity, allow_deadband_flexibility, 
              allow_deadband_flexibility_price, onsite_resources, day, optimization_horizon):
    
    C = (tao*3600/R)

    time_step_per_hour = 60//time_granularity
    SimLength = T_start.shape[0]
    number_of_houses = T_start.shape[1]

    prices = prices[:SimLength]
    solar_data = solar_data[day*optimization_horizon*time_step_per_hour:day*optimization_horizon*time_step_per_hour+SimLength]
    T_out_array = T_out_array[day*optimization_horizon*time_step_per_hour:day*optimization_horizon*time_step_per_hour+SimLength]
    
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
                
    solar_charge = cp.Variable((SimLength, number_of_houses))

    objective = cp.Minimize(cp.sum(prices@(heater_status - solar_charge)/time_step_per_hour) - 100000*cp.sum(t_lower_slack) - 10000*cp.sum(t_upper_slack)) # objective is to minimize the energy consumption cosr as well as ensure that the battery is charge to be able to drive in the next driving instance. It must be ensured that there is always a tendency to overcharge than undercharge. Here the units are not matched, with power in kW and prices in EUR/MWh, must be corrected while actual price calculation
    constraints = [heater_status >= 0, heater_status <= heater_power_array/1000,
                   temperature[0] == T_start[0,:], 
                   T_plus_1[:, 0] == T_out[1:, 0] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - cp.multiply((T_out[1:, 0] + cp.multiply(heater_status[:-1, 0], R[:-1, 0])*1000/time_step_per_hour - T[:, 0]), np.exp(-1*(time_step_per_hour*60)/(R[:-1, 0]*C[:-1, 0]))),
                   T_plus_1[:, 1:] == T_out[1:, 1:] + cp.multiply(heater_status[:-1, 1:]*0.7, R[:-1, 1:])*1000/time_step_per_hour - cp.multiply((T_out[1:, 1:] + cp.multiply(heater_status[:-1, 1:]*0.7, R[:-1, 1:])*1000/time_step_per_hour - T[:, 1:]), np.exp(-1*(time_step_per_hour*60)/(R[:-1, 1:]*C[:-1, 1:]))),
                   t_lower_slack <= 0, t_lower_slack <= temperature-T_lower_bound, t_upper_slack <= 0, t_upper_slack <= T_upper_bound - temperature,  
                   solar_charge <= solar_data_multi_home, solar_charge <= heater_status*onsite_resources, solar_charge >= 0,
                  ]

    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'ECOS', verbose = True)

    return prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, number_of_houses, time_step_per_hour, T_start, solar_data_multi_home, T_out


# This function gives optimization
def multi_heater_share(T_start, T_set, dead_band, heater_power, T_out_array, prices, R, tao, time_granularity, solar_data, solar_capacity, allow_deadband_flexibility, 
              allow_deadband_flexibility_price, efficiency_other_dependents, onsite_resources, day, optimization_horizon):
    
    C = (tao*3600/R)

    time_step_per_hour = 60//time_granularity
    SimLength = T_start.shape[0]
    number_of_houses = T_start.shape[1]

    prices = prices[:SimLength]
    solar_data = solar_data[day*optimization_horizon*time_step_per_hour:day*optimization_horizon*time_step_per_hour+SimLength]
    T_out_array = T_out_array[day*optimization_horizon*time_step_per_hour:day*optimization_horizon*time_step_per_hour+SimLength]
    
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
    heater_status_ineff = cp.Variable((SimLength, number_of_houses))
    temperature = cp.Variable((SimLength, number_of_houses))
    T = temperature[:-1]
    T_plus_1 = temperature[1:]
    t_lower_slack_share = cp.Variable((SimLength, number_of_houses))
    t_upper_slack_share = cp.Variable((SimLength, number_of_houses))
    T_upper_bound = T_set + dead_band/2
    T_lower_bound = T_set - dead_band/2

    if allow_deadband_flexibility == 1:
        for i in range (len(prices)):
            if prices[i] > allow_deadband_flexibility_price:
                T_lower_bound[i] = T_lower_bound[i] - 1
                

    solar_charge = cp.Variable((SimLength, number_of_houses))

    objective_share = cp.Minimize(cp.sum(prices@(heater_status + heater_status_ineff - solar_charge)/time_step_per_hour) # energy consumption of both the efficient and inefficient heaters is considered
                    - 100000*cp.sum(t_lower_slack_share) - 10000*cp.sum(t_upper_slack_share)) # slack variables ensure that temperature boundaries of all homes is respected.
    constraints_share = [heater_status >= 0, cp.sum(heater_status, axis = 1) <= heater_power_array[:,0]/1000,
                   heater_status_ineff >= 0, heater_status_ineff[:,1:] <= heater_power_array[:,1:]/1000, heater_status_ineff[:,0] == 0,
                   temperature[0] == T_start[0,:], 
                   T_plus_1[:, :] == T_out[1:, :] + cp.multiply(heater_status[:-1, :] + heater_status_ineff[:-1, :]*efficiency_other_dependents, R[:-1, :])*1000/4 - cp.multiply((T_out[1:, :] + cp.multiply(heater_status[:-1, :] + heater_status_ineff[:-1, :]*efficiency_other_dependents, R[:-1, :])*1000/4 - T[:, :]), np.exp(-1*(4*60)/(R[:-1, :]*C[:-1, :]))),
                   # the temperature of individual homes depend both on the efficient heater and inefficient heateres, except for the 0th house which has the efficient heater and does not derive power from inefficient households
                   t_lower_slack_share <= 0, t_lower_slack_share <= temperature-T_lower_bound, t_upper_slack_share <= 0, t_upper_slack_share <= T_upper_bound - temperature,  
                   solar_charge <= solar_data_multi_home*onsite_resources, solar_charge[:, 0] <=  cp.sum(heater_status, axis = 1), 
                   solar_charge[:, 1:] <= heater_status_ineff[:, 1:], solar_charge >= 0,
                  ]

    prob_share = cp.Problem(objective_share, constraints_share)
    result_share = prob_share.solve(solver = 'ECOS', verbose = True)



    return prices, heater_status, T_lower_bound, T_upper_bound, temperature, T_set, heater_power_array, solar_charge, \
        number_of_houses, time_step_per_hour, T_start, heater_status_ineff, solar_data_multi_home, T_out