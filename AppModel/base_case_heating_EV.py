# Base case function
import numpy as np
import pandas as pd
from datetime import date

def downsample_array(SimLength, numbers_of_house, input_array):
    new_array = np.zeros((SimLength,numbers_of_house))
    for i in range(SimLength):
        for j in range(numbers_of_house):
            new_array[i,j] = np.mean(input_array[4*i:4*(i+4), j])
    return new_array

def bang_bang_heating(SimLength, numbers_of_house, R, C, T_start, T_upper_bound, T_lower_bound, heater_power,
    time_step_per_hour, T_out):

    bang_bang_control_status = np.zeros((int(SimLength), numbers_of_house))
    bang_bang_control_temp = np.zeros((int(SimLength), numbers_of_house))
    bang_bang_control_temp[0,:] = T_start[0].values

    for col in range(numbers_of_house):
        if bang_bang_control_temp[0, col] >= T_upper_bound[0, col]:
            bang_bang_control_status[0, col] = 0
        elif bang_bang_control_temp[0, col] <= T_lower_bound[0, col]:
            bang_bang_control_status[0, col] = heater_power[0, col]
        else:
            bang_bang_control_status[0, col] = np.random.choice([0,1])

    for row in range(1,SimLength):
        for col in range(numbers_of_house):
            bang_bang_control_temp[row, col] = T_out[row, col] + bang_bang_control_status[row-1, col]*R[row, col]/time_step_per_hour - (T_out[row, col] + bang_bang_control_status[row-1, col]*R[row, col]/time_step_per_hour - bang_bang_control_temp[row-1, col])*np.exp(-1*(4*60)/(R[row, col]*C[row, col]))
            if bang_bang_control_temp[row, col] >= T_upper_bound[row, col]:
                bang_bang_control_status[row, col] = 0
            elif bang_bang_control_temp[row, col] <= T_lower_bound[row, col]:
                bang_bang_control_status[row, col] = heater_power[0, col]
            else:
                bang_bang_control_status[row, col] = bang_bang_control_status[row-1, col]

    return bang_bang_control_temp, bang_bang_control_status
    
def uncontrolled_EV(SimLength, numbers_of_house, time_step_per_hour, EV_schedule, end_soc, soc_max, eta, one_plus_deadline, start_times, end_times):
    soc_max_plugin = EV_schedule['SOC Max Plugin'].values
    EV_power = EV_schedule['Plugin Power'].values
    soc_start = EV_schedule['SOC Start'].values

    soc_uncontrolled_status = np.zeros((SimLength, numbers_of_house))
    soc_uncontrolled_evolution = np.zeros((SimLength, numbers_of_house))
    soc_uncontrolled_evolution[0,:] = soc_start

    if end_soc == 'Next day driving deadline':
        soc_target = one_plus_deadline
    else:
        soc_target = soc_max_plugin

    for col in range(numbers_of_house):
        if start_times[col] > 0 or end_times[col] < 0:
            soc_uncontrolled_status[0,col] = 0
        elif soc_uncontrolled_evolution[0, col] >= soc_target[col]:
            soc_uncontrolled_status[0, col] = 0
        else:
            soc_uncontrolled_status[0, col] = EV_power[col]

    for row in range(1,SimLength):
        for col in range(numbers_of_house):
            soc_uncontrolled_evolution[row, col] = soc_uncontrolled_evolution[row-1, col] + eta[col]*soc_uncontrolled_status[row-1, col]/time_step_per_hour
            if row<start_times[col] or row>end_times[col]:
                soc_uncontrolled_status[row,col] = 0
            elif (soc_uncontrolled_evolution[row, col] >= soc_target[col]) or (soc_uncontrolled_evolution[row, col] >= soc_max[0,col]):
                    soc_uncontrolled_status[row, col] = 0
            else:
                soc_uncontrolled_status[row, col] = EV_power[col]

    return soc_uncontrolled_status, soc_uncontrolled_evolution

def base_solar_consumption(solar_data_multi_home, soc_uncontrolled_status, bang_bang_control_status, inflexible_load, time_step_per_hour, onsite_resources):
    solar_base_case = onsite_resources*np.minimum(solar_data_multi_home, soc_uncontrolled_status+bang_bang_control_status/1000+inflexible_load)

    return np.sum(solar_base_case, axis = 0)/time_step_per_hour, solar_base_case
    