# optimization function
from input_read_community import process_EV_schedule
import cvxpy as cp
import numpy as np
import streamlit as st
def optimal_scheduler(prices, solar_data, time_granularity, onsite_resource, v2g_feasibility, inflexible_load,
                    force_charge_price, force_stop_price, force_charge, force_stop, peak_house_load, EV_schedule,
                    T_start, T_set, dead_band, heater_power, T_out, R, tao, allow_deadband_flexibility, allow_deadband_flexibility_price,
                    day_of_year, comm_batt, comm_battery_size, comm_battery_init_soc,  charge_option_1, charge_option_2, charge_option_3,
                    meet_deadline, charge_to_max, peak_network,range_anxiety,save_comm_batt,ceiling):
    numbers_of_house = len(EV_schedule)   
    C = (tao*3600/R)
    time_step_per_hour = int(60/time_granularity)
    SimLength = 24*time_step_per_hour
    prices = prices[:SimLength]
    day_of_year_hour = day_of_year*24*time_step_per_hour

    solar_data = solar_data[day_of_year_hour:day_of_year_hour+SimLength]
    solar_data_multi_home = np.zeros((SimLength, numbers_of_house))
    for house_number in range(numbers_of_house):
        solar_data_multi_home[:, house_number] = solar_data
    solar_capacity = EV_schedule['Solar Capacity'].values
    solar_data_multi_home = solar_data_multi_home*solar_capacity

    T_out = T_out[day_of_year_hour:day_of_year_hour+SimLength]
    EV_power, battery_size, eta, soc_max, soc_min, soc_deadline, soc_start, one_plus_deadline, start_times, end_times \
        = process_EV_schedule(EV_schedule, time_step_per_hour, time_granularity, numbers_of_house, range_anxiety)

    reward_force_charge = np.array([])
    for price_value in prices:
        if price_value < force_charge_price:
            reward_force_charge = np.append(reward_force_charge, -10000)
        else:
            reward_force_charge = np.append(reward_force_charge, 0)

    reward_ultra_high_v2g = np.array([])
    for price_value in prices:
        if price_value > force_stop_price:
            reward_ultra_high_v2g = np.append(reward_ultra_high_v2g, 10000)
        else:
            reward_ultra_high_v2g = np.append(reward_ultra_high_v2g, 0)
    
    soc = cp.Variable((SimLength, numbers_of_house))
    soc_t = soc[:-1]
    soc_tplus1 = soc[1:]
    EV_status = cp.Variable((SimLength, numbers_of_house))
    V2G_status = cp.Variable((SimLength, numbers_of_house))
    EV_slack = cp.Variable((SimLength, numbers_of_house))
    EV_deadline_slack = cp.Variable((numbers_of_house))
    solar_charge = cp.Variable((SimLength, numbers_of_house))
    heater_power_array = np.zeros((SimLength, numbers_of_house))
    for timestep in range(SimLength):
        heater_power_array[timestep, :] = heater_power[0]

    heater_status = cp.Variable((SimLength, numbers_of_house))
    temperature = cp.Variable((SimLength, numbers_of_house))
    temperature = cp.Variable((SimLength, numbers_of_house))
    T = temperature[:-1]
    T_plus_1 = temperature[1:]
    t_lower_slack = cp.Variable((SimLength, numbers_of_house))
    t_upper_slack = cp.Variable((SimLength, numbers_of_house))
    T_upper_bound = T_set + dead_band/2
    T_lower_bound = T_set - dead_band/2
    T_out_array = T_out.copy()

    T_out = np.zeros((SimLength,numbers_of_house))
    for i in range(numbers_of_house):
        T_out[:,i] = T_out_array
    if allow_deadband_flexibility == 1:
        for i in range (len(prices)):
            if prices[i] > allow_deadband_flexibility_price:
                T_lower_bound[i] = T_lower_bound[i] - 1
    
    low_price_index = np.where(prices<force_charge_price)
    not_low_price_index = np.array(list(range(SimLength)))
    not_low_price_index = np.delete(not_low_price_index, low_price_index)
    solar_prod_index = np.where(solar_data)
    solar_prod_index = solar_prod_index[0]

    community_battery = cp.Variable(SimLength)
    low_price_charge_community = cp.Variable(SimLength)
    solar_to_community = cp.Variable((SimLength, numbers_of_house)) # two solar variable to avoid over consumption and avoid curtailment
    community_battery_discharge = cp.Variable((SimLength, numbers_of_house))

    objective = cp.Minimize(cp.sum(prices@(EV_status - V2G_status + heater_status + inflexible_load - solar_charge - solar_to_community - community_battery_discharge)/4) 
            + cp.sum(prices@(low_price_charge_community))/4
            - 1000000*cp.sum(EV_slack) - charge_option_1*cp.sum(reward_ultra_high_v2g@(EV_status)) + charge_option_2*force_stop*cp.sum(reward_ultra_high_v2g@( - V2G_status))
                + charge_option_3*force_stop*cp.sum(reward_ultra_high_v2g@(EV_status)) - 10000*cp.sum(t_lower_slack) - 10000*cp.sum(t_upper_slack)
            # - community_battery[-1]*280*save_comm_batt
            + ceiling*100*cp.sum((cp.sum(EV_status - V2G_status + heater_status + inflexible_load - solar_charge - community_battery_discharge, axis = 1)+ low_price_charge_community))
            - 1000*cp.sum(EV_deadline_slack)
            + cp.sum(EV_status + V2G_status)

            )

    constraints = constraints = [
                EV_status>=0, EV_status<=EV_power, 
                V2G_status>=0, V2G_status<=EV_power*v2g_feasibility, 
                soc[0] == soc_start, soc <= soc_max,
                soc_tplus1 == soc_t + cp.multiply(EV_status[:-1],eta[:-1])/time_step_per_hour - cp.multiply(V2G_status[:-1],1/eta[:-1])/time_step_per_hour,
                EV_slack <=0, EV_slack<= soc-soc_min,
                EV_deadline_slack <= 0, EV_deadline_slack<= soc[-1]-one_plus_deadline,
                

                solar_charge + solar_to_community<= solar_data_multi_home*onsite_resource, solar_charge >= 0, solar_to_community >= 0, solar_to_community <= 0.5*comm_batt*comm_battery_size,
                inflexible_load + EV_status - V2G_status + heater_status - solar_charge - community_battery_discharge >= 0,
                inflexible_load + EV_status - V2G_status + heater_status - solar_charge - community_battery_discharge <= peak_house_load,
                cp.sum(heater_status + EV_status + inflexible_load - solar_charge - community_battery_discharge, axis = 1) + low_price_charge_community <=peak_network,

                heater_status >= 0, heater_status <= heater_power_array/1000,
                temperature[0,:] == T_start[0].values, 
                T_plus_1 == T_out[1:] + cp.multiply(heater_status[:-1], R[:-1])*1000/time_step_per_hour - cp.multiply((T_out[1:] + cp.multiply(heater_status[:-1], R[:-1])*1000/time_step_per_hour - T), np.exp(-1*(time_step_per_hour*60)/(R[:-1]*C[:-1]))),
                t_lower_slack <= 0, t_lower_slack <= temperature-T_lower_bound, t_upper_slack <= 0, t_upper_slack <= T_upper_bound - temperature, 
                
                community_battery_discharge >= 0, cp.sum(community_battery_discharge, axis = 1) <= 0.9*comm_batt*comm_battery_size, cp.sum(community_battery_discharge, axis = 1) <= community_battery,
                community_battery[0] == cp.minimum(comm_battery_init_soc,comm_battery_size)*comm_batt , community_battery <= comm_battery_size*comm_batt, community_battery >= comm_battery_size*comm_batt*20/100,
                
                community_battery[1:] == community_battery[:-1] + cp.sum(cp.multiply(-community_battery_discharge[:-1],1/eta[:-1]) + cp.multiply(solar_to_community[:-1], eta[:-1])*comm_batt, axis = 1)/4 + low_price_charge_community[:-1]/4,
                low_price_charge_community >= 0, low_price_charge_community <= 0.9*comm_batt*comm_battery_size,
                # community_battery[-1] == save_comm_batt*0.5*comm_battery_size  
                ]
        
    
    for house_number in range(numbers_of_house):
        start_time = int(start_times[house_number])
        end_time = int(end_times[house_number])
        constraints.append(EV_status[:start_time, house_number] == 0)
        constraints.append(EV_status[end_time:, house_number] == 0)
        constraints.append(V2G_status[:start_time, house_number] == 0)
        constraints.append(V2G_status[end_time:, house_number] == 0)
    if onsite_resource == 1:
        constraints.append(community_battery_discharge[solar_prod_index] == 0) 

    # if (low_price_index[0].size < SimLength/2) and (low_price_index[0].size > 0):
    #     constraints.append(community_battery_discharge[low_price_index] == 0)
    # if not_low_price_index.size != 0:
    #     constraints.append(low_price_charge_community[not_low_price_index] == 0)
    # else:
    #     constraints.append(low_price_charge_community == 0)

    if comm_batt > 0:
        constraints.append(solar_charge+solar_to_community <= solar_data_multi_home*comm_batt)
    if comm_batt == 0:
        constraints.append(solar_to_community[:,:] == 0)
        
    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'ECOS', verbose = True)

    return prices, solar_data, solar_charge, soc, EV_status, V2G_status, soc_min, soc_max, soc_deadline, numbers_of_house, SimLength, start_times, end_times, \
    inflexible_load, EV_schedule, time_step_per_hour, temperature, heater_status, T_lower_bound, \
        T_upper_bound, C, R, solar_data_multi_home, community_battery, community_battery_discharge, solar_to_community, low_price_charge_community, T_out, soc_start, one_plus_deadline
