# the model utilizes similar input and modeling strategies for EV and heating, and the similar parts have been skipped in the comments.

# import necessary libraries
import numpy as np
import pandas as pd
from datetime import date
import streamlit as st
import os
from pathlib import Path
import plotly.express as px
from plot_script import plot_graphs, st_plt_template
from base_case_heating_EV import base_solar_consumption, bang_bang_heating, uncontrolled_EV
from optimization_function import optimal_scheduler

# Set directories and paths
this_dir = Path(os.getcwd())
data_dir = f'{this_dir.parents[0]}\Data'

st.set_page_config(layout="wide")
filename_cwd = os.getcwd()
hour = pd.date_range(date.today(), periods=24, freq="H")
header = st.container()
dataset = st.container()
user_inputs = st.container()

left_col, left_mid_col, right_mid_col, right_col = st.columns(4)
with header:
    st.title('Mutli home - multi device optimization')
    st.header('Optimal appliance scheduling in energy community')

    csv_name = left_col.selectbox("Day ahead prices in €/MWh (60-min)", ('Price','Price_high',))
    day_ahead = pd.read_csv(f'{data_dir}\{csv_name}.csv', header = None)
    day_ahead.index = hour
    day_ahead = day_ahead.resample('15T').ffill()
    prices = day_ahead[0].values 
    prices = np.append(prices, np.array(3*[prices[-1]]))

    solar_csv_name = left_mid_col.selectbox("Solar base profile", ('PV_zurich',))
    solar_data = pd.read_csv(f'{data_dir}\{solar_csv_name}.csv', skiprows=3, index_col = 0, parse_dates=True)
    solar_data = solar_data.resample('15T').mean().interpolate(method='linear')
    solar_data = solar_data['electricity'].values
    solar_data = np.append(solar_data, np.array(3*[solar_data[-1]]))

    inflexible_load_csv = right_mid_col.selectbox("Schedule of inflexible load", ('inflexible_load',))
    inflexible_load = pd.read_csv(f'{data_dir}\{inflexible_load_csv}.csv', header = None).values

    EV_schedule_csv = right_col.selectbox("Schedule of EV", ('EV_schedule',))
    EV_schedule = pd.read_csv(f'{data_dir}\{EV_schedule_csv}.csv')

    heater_power_csv = right_col.selectbox("Heater power file", ('heater_power',))
    heater_power = pd.read_csv(f'{data_dir}\{heater_power_csv}.csv', header = None).values

    T_out_csv = left_col.selectbox("Ambient temperature °C (60-min)", ('T_out_Zurich',))
    T_out = pd.read_csv(f'{data_dir}\{T_out_csv}.csv', skiprows=3, index_col = 0, parse_dates=True)
    T_out = T_out.resample('15T').mean().interpolate(method='linear')
    T_out = T_out['temperature'].values
    T_out_array = np.append(T_out, np.array(3*[T_out[-1]]))
    
    T_set_csv = left_mid_col.selectbox("Setpoint Temperature file", ('T_set_community',))
    T_set = pd.read_csv(f'{data_dir}\{T_set_csv}.csv', header = None).values

    T_start_csv = right_mid_col.selectbox("Start Temperature file", ('T_start',))
    T_start = pd.read_csv(f'{data_dir}\{T_start_csv}.csv', header = None)

    R_csv = left_mid_col.selectbox("Heating resistivity file", ('R_community',))
    R = pd.read_csv(f'{data_dir}\{R_csv}.csv', header = None).values

    tao_csv = left_col.selectbox("Time constant file", ('tao_community',))
    tao = pd.read_csv(f'{data_dir}\{tao_csv}.csv', header = None).values

    allow_deadband_flexibility = right_mid_col.selectbox("Allow DB flexibility (DBF)?", ('Yes', 'No'))
    allow_deadband_flexibility = 1 if allow_deadband_flexibility == 'Yes' else 0

    dead_band = right_col.text_input("Input tolerance deadband (DB) in °C", value = 2)
    dead_band = float(dead_band)

    allow_deadband_flexibility_price = left_col.text_input("DBF price threshold (€/MWh)", value = 600)
    allow_deadband_flexibility_price = float(allow_deadband_flexibility_price)

    range_anxiety = left_mid_col.selectbox("Activate for range anxiety: ", ('No', 'Yes')) # activate range anxiety for EV
    range_anxiety = 1 if range_anxiety == 'Yes' else 0

    v2g_feasibility = right_mid_col.selectbox("V2G functionality availablity: ", ('Yes', 'No'))
    v2g_feasibility = 1 if v2g_feasibility == 'Yes' else 0

    end_soc = right_col.selectbox('Charge to ',('Next day driving deadline', 'Full')) # choice between charging to deadline and to maximum
    if end_soc == 'Next day driving deadline':
        meet_deadline = 1
        charge_to_max = 0
    else:
        meet_deadline = 0
        charge_to_max = 1

    force_stop = left_col.selectbox("Force discharge EV during high prices?", ('Yes', 'No')) 
    force_stop = 1 if force_stop == 'Yes' else 0
    
    force_charge_price = left_mid_col.text_input("EV force charge threshold (€/MWh)", value = 250)
    force_charge_price = int(force_charge_price)

    force_charge = right_col.selectbox("Force charge EV during low prices?", ('Yes', 'No'))
    force_charge = 1 if force_charge == 'Yes' else 0
   
    force_stop_price = right_mid_col.text_input("EV force discharge threshold(€/MWh)", value = 600)
    force_stop_price = int(force_stop_price)

    onsite_resources = left_col.selectbox("Make use of onsite resources?", ('Yes', 'No'))
    onsite_resources = 1 if onsite_resources == 'Yes' else 0   

    comm_batt = left_mid_col.selectbox("Use community battery?", ('Yes', 'No')) # Availability of community battery
    comm_batt = 1 if comm_batt == 'Yes' else 0

    comm_battery_size = right_mid_col.text_input("Community battery size", value = 120) # Size of community battery
    comm_battery_size = int(comm_battery_size)

    save_comm_batt = right_col.selectbox("Community battery energy anxiety?", ('No', 'Yes')) # Energy anxiety for community battery
    save_comm_batt = 1 if save_comm_batt == 'Yes' else 0

    comm_battery_init_soc = left_col.text_input("Initial community battery SoC (>= 20% battery capacity)", value = int(comm_battery_size*0.2))  # Initialize SoC of community battery
    comm_battery_init_soc = float(comm_battery_init_soc)
    comm_battery_init_soc = max(comm_battery_init_soc, 20*comm_battery_size/100)
    
    charge_option = left_mid_col.selectbox('In a high price scenario',('Use Community battery', 'Use Community battery + V2g', 'Charge to full anyway', 'No action')) # Action during high priced hours - not relevant to masters thesis
    charge_option_1, charge_option_2, charge_option_3 = 0, 0, 0
    if charge_option == 'Charge to full anyway':
        charge_option_1 = 1
    elif charge_option == 'Use Community battery + V2g':
        charge_option_2 = 1
    elif charge_option == 'No action':
        charge_option_3 = 1    

    ceiling = right_mid_col.selectbox("Max load penalty", ('No', 'Yes')) # Penalty on max power consumption
    ceiling = 1 if ceiling == 'Yes' else 0

    peak_house_load = left_col.text_input("Peak houseload: ", value = 10) # Peak house load
    peak_house_load = float(peak_house_load)

    peak_network = left_mid_col.text_input("Peak network load: ", value = 100) # Peak network load
    peak_network = float(peak_network)

    time_granularity = right_col.text_input("Time granularity", value = 15)
    time_granularity = float(time_granularity)

    day_of_year = right_col.slider("Day of year", 0,364,50)
    day_of_year = int(day_of_year) 
    
# Energy planner
prices, solar_data, solar_charge, soc, EV_status, V2G_status, soc_min, soc_max, soc_deadline, numbers_of_house, SimLength, start_times, end_times, \
    inflexible_load, EV_schedule, time_step_per_hour, temperature, heater_status, T_lower_bound, \
        T_upper_bound, C, R, solar_data_multi_home, community_battery, community_battery_discharge, solar_to_community, low_price_charge_community, T_out, soc_start, one_plus_deadline = \
    optimal_scheduler(prices = prices, solar_data = solar_data, time_granularity = time_granularity,
                    onsite_resource = onsite_resources, v2g_feasibility = v2g_feasibility, inflexible_load = inflexible_load,
                    force_charge_price = force_charge_price, force_stop_price = force_stop_price, force_charge = force_charge,
                    force_stop = force_stop, peak_house_load = peak_house_load, EV_schedule = EV_schedule,
                    T_start = T_start, T_set = T_set, dead_band = dead_band, heater_power = heater_power, T_out = T_out_array, R = R, tao = tao,
                    allow_deadband_flexibility = allow_deadband_flexibility, allow_deadband_flexibility_price = allow_deadband_flexibility_price,
                    day_of_year = day_of_year, comm_batt = comm_batt, comm_battery_size = comm_battery_size, comm_battery_init_soc = comm_battery_init_soc, 
                    charge_option_1 = charge_option_1, charge_option_2 =  charge_option_2, charge_option_3 = charge_option_3, peak_network = peak_network,
                    meet_deadline = meet_deadline, charge_to_max = charge_to_max, range_anxiety=range_anxiety, save_comm_batt=save_comm_batt, ceiling=ceiling)

time_axis = pd.date_range(date.today(), periods=len(prices), freq="15min")

# to take care of EV energy burn
eta = EV_schedule['Eta'].values
charge = np.zeros(soc.shape)
discharge = np.zeros(soc.shape)

net_ev_status = np.zeros(soc.shape)
for i in range(soc.shape[0]):
    for j in range(soc.shape[1]):
        net_ev_status[i,j] = (EV_status.value[i,j]*eta[j] - V2G_status.value[i,j]/eta[j])
        if net_ev_status[i, j] < 0:
            discharge[i, j] = net_ev_status[i, j]*eta[j]
        elif net_ev_status[i, j] > 0:
            charge[i, j] = net_ev_status[i, j]/eta[j]

solar_optimal_consumption = np.sum(solar_charge.value, axis = 0)/time_step_per_hour


# Base case device power consumption
bang_bang_control_temp, bang_bang_control_status = bang_bang_heating(SimLength, numbers_of_house,\
    R, C, T_start, T_upper_bound, T_lower_bound, heater_power, time_step_per_hour, T_out)

soc_uncontrolled_status, soc_uncontrolled_evolution = uncontrolled_EV(SimLength, numbers_of_house, \
    time_step_per_hour, EV_schedule, end_soc, soc_max, eta, one_plus_deadline, start_times, end_times)

solar_base_case_consumption, solar_base_case = base_solar_consumption(solar_data_multi_home, soc_uncontrolled_status,\
    bang_bang_control_status, inflexible_load, time_step_per_hour, onsite_resources)


# Result compilation for energy consumption and related costs for different devices/and the whole system
total_grid_energy_consumption_optimal = np.sum(EV_status.value - V2G_status.value + heater_status.value + inflexible_load - solar_charge.value - community_battery_discharge.value, axis = 0)/time_step_per_hour
total_grid_energy_base_case = np.sum(bang_bang_control_status/1000 + soc_uncontrolled_status + inflexible_load - solar_base_case, axis = 0)/time_step_per_hour
total_grid_energy_consumption_optimal_cost = prices@(EV_status.value - V2G_status.value + heater_status.value + inflexible_load - solar_charge.value - community_battery_discharge.value)/(1000*time_step_per_hour)
total_grid_energy_base_case_cost = prices@(bang_bang_control_status/1000 + soc_uncontrolled_status + inflexible_load - solar_base_case)/(1000*time_step_per_hour)

total_energy_consumption_optimal = np.sum(EV_status.value + heater_status.value + inflexible_load, axis = 0)/(time_step_per_hour)
total_energy_base_case = np.sum(bang_bang_control_status/1000 + soc_uncontrolled_status + inflexible_load, axis = 0)/(time_step_per_hour)

total_heat_energy_consumption_optimal = np.sum(heater_status.value, axis = 0)/time_step_per_hour
total_heat_energy_base_case = np.sum(bang_bang_control_status/1000, axis = 0)/time_step_per_hour

total_EV_energy_consumption_optimal = np.sum(EV_status.value - V2G_status.value, axis = 0)/time_step_per_hour
total_EV_energy_base_case = np.sum(soc_uncontrolled_status, axis = 0)/time_step_per_hour

result_csv = pd.DataFrame()
parameters_simulation = ['House number', 'Case type','Energy consumption cost (€)', 'Total energy consumption (kWh)', 
                        'Grid energy consumption (kWh)', 'Solar production (kWh)', 'Solar consumption (kWh)', 'Self-consumption solar end (%)', 'Self-consumption home end (%)', 'Total heat energy consumption (kWh)', 'Net EV energy consumption (kWh)']
for para_sim in parameters_simulation:
    result_csv[para_sim] = np.zeros(2*(numbers_of_house))

for house in range(0,numbers_of_house*2,2):
    result_csv.loc[house, 'House number'] = house/2+1
    result_csv.loc[house, 'Case type'] = 'Base case'
    result_csv.loc[house, 'Grid energy consumption (kWh)'] = np.round(total_grid_energy_base_case[int(house/2)], 2)
    result_csv.loc[house, 'Energy consumption cost (€)'] = np.round(total_grid_energy_base_case_cost[int(house/2)], 2)
    result_csv.loc[house, 'Total energy consumption (kWh)'] = np.round(total_energy_base_case[int(house/2)], 2)
    result_csv.loc[house, 'Solar production (kWh)'] = np.round(np.sum(solar_data_multi_home, axis = 0)[int(house/2)], 2)/time_step_per_hour
    result_csv.loc[house, 'Solar consumption (kWh)'] = solar_base_case_consumption[int(house/2)]*onsite_resources
    result_csv.loc[house, 'Solar to battery (kWh)'] = 0
    result_csv.loc[house, 'Self-consumption solar end (%)'] = np.round(100*result_csv.loc[house, 'Solar consumption (kWh)']/result_csv.loc[house, 'Solar production (kWh)'])
    result_csv.loc[house, 'Self-consumption home end (%)'] = np.round(100*result_csv.loc[house, 'Solar consumption (kWh)']/result_csv.loc[house, 'Total energy consumption (kWh)'])
    result_csv.loc[house, 'Total heat energy consumption (kWh)'] = np.round(total_heat_energy_base_case[int(house/2)], 2)
    result_csv.loc[house, 'Net EV energy consumption (kWh)'] = np.round(total_EV_energy_base_case[int(house/2)], 2)

    result_csv.loc[house+1, 'House number'] = house/2+1
    result_csv.loc[house+1, 'Case type'] = 'Optimal case'
    result_csv.loc[house+1, 'Grid energy consumption (kWh)'] = np.round(total_grid_energy_consumption_optimal[int(house/2)], 2)
    result_csv.loc[house+1, 'Energy consumption cost (€)'] = np.round(total_grid_energy_consumption_optimal_cost[int(house/2)], 2)
    result_csv.loc[house+1, 'Total energy consumption (kWh)'] = np.round(total_energy_consumption_optimal[int(house/2)], 2)
    result_csv.loc[house+1, 'Solar production (kWh)'] = np.round(np.sum(solar_data_multi_home, axis = 0)[int(house/2)], 2)/time_step_per_hour
    result_csv.loc[house+1, 'Solar consumption (kWh)'] = np.round(solar_optimal_consumption[int(house/2)], 2)
    result_csv.loc[house+1, 'Solar to battery (kWh)'] = np.round(np.sum(solar_to_community.value, axis =0)[int(house/2)], 2)/time_step_per_hour
    result_csv.loc[house+1, 'Self-consumption solar end (%)'] = np.round(100*(result_csv.loc[house+1, 'Solar consumption (kWh)']+result_csv.loc[house+1, 'Solar to battery (kWh)'])/result_csv.loc[house+1, 'Solar production (kWh)'])
    result_csv.loc[house+1, 'Self-consumption home end (%)'] = np.round(100*result_csv.loc[house+1, 'Solar consumption (kWh)']/result_csv.loc[house+1, 'Total energy consumption (kWh)'])
    result_csv.loc[house+1, 'Total heat energy consumption (kWh)'] = np.round(total_heat_energy_consumption_optimal[int(house/2)], 2)
    result_csv.loc[house+1, 'Net EV energy consumption (kWh)'] = np.round(total_EV_energy_consumption_optimal[int(house/2)], 2)

grid_load_optimal = EV_status.value - V2G_status.value + heater_status.value + inflexible_load - solar_charge.value - community_battery_discharge.value
grid_load_base = soc_uncontrolled_status + bang_bang_control_status/1000 + inflexible_load - solar_base_case

net_system_grid_load_optimal = np.sum(heater_status.value + EV_status.value - V2G_status.value + inflexible_load - solar_charge.value - community_battery_discharge.value, axis = 1) + low_price_charge_community.value
net_system_total_load_optimal = np.sum(heater_status.value + EV_status.value - V2G_status.value + inflexible_load + solar_to_community.value, axis = 1) + low_price_charge_community.value 
net_system_grid_cost_optimal = prices@(np.sum(heater_status.value + EV_status.value - V2G_status.value + inflexible_load - solar_charge.value - community_battery_discharge.value, axis = 1) + low_price_charge_community.value)/1000

net_system_grid_load_base = np.sum(bang_bang_control_status/1000 + soc_uncontrolled_status + inflexible_load - solar_base_case, axis = 1)

with right_mid_col:
    house_plot = st.selectbox("Plots for house", ('1','2','3','4', '5', '6', '7', '8', '9', '10'))
    house_plot = int(house_plot) 

system_results = pd.DataFrame()
for para_sim in parameters_simulation:
    system_results[para_sim] = np.zeros(2)

system_results.loc[0, 'Case type'] = 'Base case'
system_results.loc[0, 'Grid energy consumption (kWh)'] = np.round(np.sum(total_grid_energy_base_case), 2)
system_results.loc[0, 'Energy consumption cost (€)'] = np.round(np.sum(total_grid_energy_base_case_cost), 2)
system_results.loc[0, 'Total energy consumption (kWh)'] = np.round(np.sum(total_energy_base_case), 2)
system_results.loc[0, 'Solar production (kWh)'] = np.round(np.sum(solar_data_multi_home), 2)/time_step_per_hour
system_results.loc[0, 'Solar consumption (kWh)'] = np.sum(solar_base_case_consumption)*onsite_resources
system_results.loc[0, 'Self-consumption solar end (%)'] = np.round(100*np.sum(system_results.loc[0, 'Solar consumption (kWh)'])/np.sum(system_results.loc[0, 'Solar production (kWh)']))
system_results.loc[0, 'Self-consumption home end (%)'] = np.round(100*np.sum(system_results.loc[0, 'Solar consumption (kWh)'])/np.sum(system_results.loc[0, 'Total energy consumption (kWh)']))
system_results.loc[0, 'Total heat energy consumption (kWh)'] = np.sum(np.round(total_heat_energy_base_case, 2))
system_results.loc[0, 'Net EV energy consumption (kWh)'] = np.sum(np.round(total_EV_energy_base_case, 2))
system_results.loc[0, 'Peak load (kW)'] = np.max(total_grid_energy_base_case)

system_results.loc[1, 'Case type'] = 'Optimal'
system_results.loc[1, 'Grid energy consumption (kWh)'] = np.round(np.sum(net_system_grid_load_optimal/time_step_per_hour), 2)
system_results.loc[1, 'Energy consumption cost (€)'] = np.round(np.sum(net_system_grid_cost_optimal/time_step_per_hour), 2)
system_results.loc[1, 'Total energy consumption (kWh)'] = np.round(np.sum(net_system_total_load_optimal/time_step_per_hour), 2)
system_results.loc[1, 'Solar production (kWh)'] = np.round(np.sum(solar_data_multi_home), 2)/time_step_per_hour
system_results.loc[1, 'Solar consumption (kWh)'] = np.sum(solar_optimal_consumption)
system_results.loc[1, 'Solar to battery (kWh)'] = np.round(np.sum(solar_to_community.value), 2)/time_step_per_hour
system_results.loc[1, 'Self-consumption solar end (%)'] = np.round(100*np.sum(system_results.loc[1, 'Solar consumption (kWh)']+system_results.loc[1, 'Solar to battery (kWh)'])/np.sum(system_results.loc[1, 'Solar production (kWh)']))
system_results.loc[1, 'Self-consumption home end (%)'] = np.round(100*np.sum(system_results.loc[1, 'Solar consumption (kWh)'])/np.sum(system_results.loc[1, 'Total energy consumption (kWh)']))
system_results.loc[1, 'Total heat energy consumption (kWh)'] = np.sum(np.round(total_heat_energy_consumption_optimal, 2))
system_results.loc[1, 'Net EV energy consumption (kWh)'] = np.sum(np.round(total_EV_energy_consumption_optimal, 2))
system_results.loc[1, 'Peak load (kW)'] = np.max(net_system_grid_load_optimal)
system_results.loc[1, 'Max pos (kW)'] = np.max(net_system_grid_load_optimal-net_system_grid_load_base)
system_results.loc[1, 'Max neg (kW)'] = np.min(net_system_grid_load_optimal-net_system_grid_load_base)


# Generate plots
EV_soc_fig, temp_fig, load_change_grid, solar_consumption, optimal_applicance_status, base_case_appliance_status, solar_community,\
        community_soc, community_status, load_change_grid_system, fig_bar_comparison_grid_energy, fig_bar_comparison_energy,\
        fig_bar_comparison_cost, fig_bar_comparison_heat_energy, fig_bar_comparison_EV_energy,\
        fig_bar_comparison_self_cons_sol, fig_bar_comparison_self_cons_home, system_fig_bar_comparison_grid_energy, \
        system_fig_bar_comparison_energy, system_fig_bar_comparison_cost, \
        system_fig_bar_comparison_heat_energy, system_fig_bar_comparison_EV_energy,\
        system_fig_bar_comparison_self_cons_home, system_fig_bar_comparison_self_cons_sol = plot_graphs(time_axis, community_battery, prices, solar_to_community, low_price_charge_community, community_battery_discharge,
    net_system_grid_load_base, net_system_grid_load_optimal, result_csv, system_results, SimLength, soc_min, soc_max, house_plot,
    soc_deadline, one_plus_deadline, soc, soc_uncontrolled_evolution, start_times, end_times, T_upper_bound, T_lower_bound, T_set, temperature,
    bang_bang_control_temp, bang_bang_control_status, charge, discharge, heater_status, inflexible_load, solar_charge, 
    soc_uncontrolled_status, solar_base_case, solar_data_multi_home, grid_load_base, grid_load_optimal, comm_battery_init_soc, comm_batt, range_anxiety, EV_status, V2G_status,)

# design of web app for plots
st_plt_template(EV_soc_fig, temp_fig, load_change_grid, solar_consumption, optimal_applicance_status, base_case_appliance_status, solar_community,\
        community_soc, community_status, load_change_grid_system, fig_bar_comparison_grid_energy, fig_bar_comparison_energy,
        fig_bar_comparison_cost, fig_bar_comparison_heat_energy, fig_bar_comparison_EV_energy,
        fig_bar_comparison_self_cons_sol, fig_bar_comparison_self_cons_home, system_fig_bar_comparison_grid_energy, \
        system_fig_bar_comparison_energy, system_fig_bar_comparison_cost, \
        system_fig_bar_comparison_heat_energy, system_fig_bar_comparison_EV_energy,\
        system_fig_bar_comparison_self_cons_home, system_fig_bar_comparison_self_cons_sol, comm_batt)