# this script gives function for all the input file read and process actions to be used by the optimizer for EV

import numpy as np

def process_EV_schedule(EV_schedule, time_step_per_hour, time_granularity, numbers_of_house, range_anxiety):
    # EV parameters are processed for all the 10 households
    EV_schedule['Start Minute'] = EV_schedule['Start'].map(lambda x: int(x.split(':')[0])*time_step_per_hour + int(np.ceil(int(x.split(':')[1])/time_granularity)))
    EV_schedule['End Minute'] = EV_schedule['End'].map(lambda x: int(x.split(':')[0])*time_step_per_hour + int(np.floor(int(x.split(':')[1])/time_granularity)))
    EV_schedule['End Minute'] = EV_schedule['End Minute'] + 24*time_step_per_hour*(EV_schedule['Start Minute'] > EV_schedule['End Minute'])
    
    SimLength = 24*time_step_per_hour

    EV_schedule['SOC min'] = EV_schedule['Battery Size']*0.2
    EV_schedule['SOC max'] = EV_schedule['Battery Size']*0.9
    EV_schedule['SOC Deadline plus One'] = (EV_schedule['Next Distance'].values + range_anxiety*EV_schedule['Range Anxiety'].values)*(EV_schedule['Average kWh per km'].values) + EV_schedule['SOC min'].values + (((EV_schedule['Plugin Power'].values)*(EV_schedule['Eta'].values))/10)
    EV_schedule['SOC Deadline'] = (EV_schedule['Next Distance'].values)*(EV_schedule['Average kWh per km'].values) + EV_schedule['SOC min'].values 
    EV_schedule['SOC Max Plugin'] = (EV_schedule['SOC Start'].values) + (EV_schedule['Plugin Power'].values)*(EV_schedule['Eta'].values)*((EV_schedule['End Minute'].values) - (EV_schedule['Start Minute'].values))/time_step_per_hour
    EV_schedule['SOC Max Plugin'] = np.minimum(EV_schedule['SOC max'], EV_schedule['SOC Max Plugin'])
    EV_schedule['SOC Deadline plus One'] = np.minimum(EV_schedule['SOC Max Plugin'], EV_schedule['SOC Deadline plus One'])
    EV_schedule['SOC Deadline'] = np.minimum(EV_schedule['SOC Max Plugin'], EV_schedule['SOC Deadline'])
    EV_schedule['Timesteps to Deadline'] = np.minimum(np.ceil(EV_schedule['SOC Deadline']/(EV_schedule['Plugin Power']/time_step_per_hour)), EV_schedule['End Minute'] - EV_schedule['Start Minute'])
    EV_schedule['Timesteps to Maximum'] = np.minimum(np.ceil(EV_schedule['SOC Max Plugin']/(EV_schedule['Plugin Power']/time_step_per_hour)), EV_schedule['End Minute'] - EV_schedule['Start Minute'])

    start_times = EV_schedule['Start Minute'].values
    end_times = EV_schedule['End Minute'].values

    one_plus_deadline = EV_schedule['SOC Deadline plus One'].values # considering an inherent tendency of range anxiety to meet the soc deadline

    EV_power = np.zeros((SimLength, numbers_of_house))
    EV_power[:] = EV_schedule['Plugin Power'].values

    battery_size = np.zeros((SimLength, numbers_of_house))
    battery_size[:] = EV_schedule['Battery Size'].values

    eta = np.zeros((SimLength, numbers_of_house))
    eta[:] = EV_schedule['Eta'].values

    soc_max = np.zeros((SimLength, numbers_of_house))
    soc_max[:] = EV_schedule['SOC max'].values

    soc_min = np.zeros((SimLength, numbers_of_house))
    soc_min[:] = EV_schedule['SOC min'].values

    soc_deadline = np.zeros((SimLength, numbers_of_house))
    soc_deadline[:] = EV_schedule['SOC Deadline'].values

    soc_start = EV_schedule['SOC Start'].values

    return EV_power, battery_size, eta, soc_max, soc_min, soc_deadline, soc_start, one_plus_deadline, start_times, end_times