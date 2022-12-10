# Plot script for the simulation
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import streamlit as st
import os
import numpy as np

filename_cwd = os.getcwd()
def fig_format(fig):
    fig.update_layout({'plot_bgcolor': 'rgba(255,255,255,0)', 'paper_bgcolor': 'rgba(255,255,255,0)',})
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', showgrid = True, gridcolor='rgba(224,224,224,50)',)
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', showgrid = False, gridcolor='rgba(224,224,224,30)',)
    fig.update_layout(autosize=False, width=800, height=400)
    fig.update_layout(legend=dict(orientation="h",yanchor="top", y = -0.2))

def plot_graphs(time_axis, community_battery, prices, solar_to_community, low_price_charge_community, community_battery_discharge,
    net_system_grid_load_base, net_system_grid_load_optimal, result_csv, system_results, SimLength, soc_min, soc_max, house_plot,
    soc_deadline, one_plus_deadline, soc, soc_uncontrolled_evolution, start_times, end_times, T_upper_bound, T_lower_bound, T_set, temperature, T_out,
    bang_bang_control_temp, bang_bang_control_status, charge, discharge, heater_status, inflexible_load, solar_charge, 
    soc_uncontrolled_status, solar_base_case, solar_data_multi_home, grid_load_base, grid_load_optimal, comm_battery_init_soc, comm_batt, range_sharing, EV_status, V2G_status):
    EV_soc_fig = make_subplots(specs=[[{"secondary_y": True}]])
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),soc_min[:,house_plot-1]), name = 'SOC min', line=dict(color='black', dash = 'dot')))
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),soc_max[:,house_plot-1]),  name = 'SOC max', line=dict(color='black', dash = 'dash')))
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),soc_deadline[:,house_plot-1]), name = 'SOC deadline', line=dict(color='#7f7f7f', dash = 'dash')))
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),np.full(SimLength,one_plus_deadline[house_plot-1])), name = 'SOC end', line=dict(color='#7f7f7f', dash = 'dot')))
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=soc.value[:,house_plot-1], name = 'SOC', line=dict(color='olivedrab')))
    EV_soc_fig.add_trace(go.Scatter(x=time_axis, y=soc_uncontrolled_evolution[:,house_plot-1], name = 'SOC uncontrolled', line=dict(color='olivedrab', dash='dot')))
    EV_soc_fig.add_vrect(x0=time_axis[start_times[house_plot-1]], x1=time_axis[end_times[house_plot-1]], fillcolor="grey", opacity=0.25, line_width=0)
    EV_soc_fig.update_yaxes(title_text="State of Charge in kWh", secondary_y=False)
    fig_format(EV_soc_fig)
    EV_soc_fig.update_layout(title = f'SoC evolution for home {house_plot}')  

    temp_fig = make_subplots(specs=[[{"secondary_y": True}]])
    temp_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),T_upper_bound[:,house_plot-1]), name = 'Upper bound', line=dict(color='black')))
    temp_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),T_lower_bound[:,house_plot-1]),  name = 'Lower bound', line=dict(color='black')))
    temp_fig.add_trace(go.Scatter(x=time_axis, y=T_out[:,house_plot-1]+15,  name = 'Ambient temperature + 15°C', line=dict(color='burlywood')))
    temp_fig.add_trace(go.Scatter(x=time_axis, y=np.full((SimLength,),T_set[:,house_plot-1]), name = 'Setpoint', line=dict(color='gray')))
    temp_fig.add_trace(go.Scatter(x=time_axis, y=temperature.value[:,house_plot-1], name = 'Optimal control', line=dict(color='red')))
    temp_fig.add_trace(go.Scatter(x=time_axis, y=bang_bang_control_temp[:,house_plot-1], name = 'Bang-bang', line=dict(color='pink')))
    temp_fig.update_yaxes(title_text="Tempeature in °C", secondary_y=False)
    fig_format(temp_fig)
    temp_fig.update_layout(title = f'Temperature evolution for home {house_plot}')

    optimal_applicance_status = make_subplots(specs=[[{"secondary_y": True}]])
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=EV_status.value[:,house_plot-1], name = 'EV charge', line=dict(color='navy')))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=V2G_status.value[:,house_plot-1], name = 'EV discharge', line=dict(color='red', width = 0), fill='tozeroy'))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=heater_status.value[:,house_plot-1], name = 'Heater', line=dict(color='orchid')))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=inflexible_load[:,house_plot-1], name = 'Inflexible load', line=dict(color='#17becf')))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_plot-1], name = 'Solar to home', line=dict(color='darkgoldenrod', width = 0), fill='tozeroy'))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=community_battery_discharge.value[:,house_plot-1], name = 'Community supply', line=dict(color='lightgreen', width = 0), fill='tozeroy'))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=(heater_status.value + inflexible_load + charge)[:,house_plot-1], name = 'Total power load', line=dict(color='darkgrey', dash = 'dash')))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=(heater_status.value + inflexible_load + charge + discharge - community_battery_discharge.value)[:,house_plot-1], name = 'Net grid load', line=dict(color='darkgrey')))
    optimal_applicance_status.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    optimal_applicance_status.update_yaxes(title_text="Appliance status (optimal) in kW", secondary_y=False,)
    optimal_applicance_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(optimal_applicance_status)
    optimal_applicance_status.update_layout(title = f'Appliance status under optimal control for home {house_plot}')

    base_case_appliance_status = make_subplots(specs=[[{"secondary_y": True}]])
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=soc_uncontrolled_status[:,house_plot-1], name = 'EV charge', line=dict(color='navy')))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=bang_bang_control_status[:,house_plot-1]/1000, name = 'Heater', line=dict(color='orchid')))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=inflexible_load[:,house_plot-1], name = 'Inflexible load', line=dict(color='#17becf')))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=solar_base_case[:,house_plot-1], name = 'Solar to home', line=dict(color='gold', width = 0), fill='tozeroy'))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=(bang_bang_control_status/1000 + inflexible_load + soc_uncontrolled_status)[:,house_plot-1], name = 'Total power load', line=dict(color='darkgrey', dash = 'dash')))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=(bang_bang_control_status/1000 + inflexible_load + soc_uncontrolled_status - solar_base_case)[:,house_plot-1], name = 'Net grid load', line=dict(color='darkgrey')))
    base_case_appliance_status.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    base_case_appliance_status.update_yaxes(title_text="Appliance status (base) in kW", secondary_y=False,)
    base_case_appliance_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(base_case_appliance_status)    
    base_case_appliance_status.update_layout(title = f'Appliance status in base case for home {house_plot}')

    load_change_grid = make_subplots(specs=[[{"secondary_y": True}]])
    load_change_grid.add_trace(go.Scatter(x=time_axis, y=grid_load_base[:,house_plot-1], name = 'Base case', line=dict(color='aquamarine')))
    load_change_grid.add_trace(go.Scatter(x=time_axis, y=grid_load_optimal[:,house_plot-1], name = 'Optimal', line=dict(color='teal')))
    load_change_grid.add_trace(go.Scatter(x=time_axis, y=(grid_load_optimal-grid_load_base)[:,house_plot-1], name = 'change from base', line=dict(color='burlywood', width = 0), fill='tozeroy'))
    load_change_grid.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    load_change_grid.update_yaxes(title_text="Net grid load in kW", secondary_y=False)
    load_change_grid.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    load_change_grid.update_layout(title = f'Net grid load for home {house_plot}')
    fig_format(load_change_grid)

    solar_consumption = make_subplots(specs=[[{"secondary_y": True}]])
    solar_consumption.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_plot-1], name = 'Change from base', line=dict(color='mistyrose', width = 0), fill='tozeroy'))
    solar_consumption.add_trace(go.Scatter(x=time_axis, y=solar_base_case[:,house_plot-1], name = 'Base case', line=dict(color='gold', width = 0), fill='tozeroy'))
    solar_consumption.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_plot-1], name = 'Optimal', line=dict(color='darkgoldenrod', width = 0), fill='tozeroy'))
    solar_consumption.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    solar_consumption.update_yaxes(title_text="Power in kW", secondary_y=False)
    solar_consumption.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(solar_consumption)
    solar_consumption.update_layout(title = f'Solar production/consumption for home {house_plot}')

    solar_community = make_subplots(specs=[[{"secondary_y": True}]])
    solar_community.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_plot-1], name = 'Solar production', line=dict(color='mistyrose', width = 0), fill='tozeroy'))
    solar_community.add_trace(go.Scatter(x=time_axis, y=solar_to_community.value[:,house_plot-1], name = 'Community battery charge', line=dict(color='darkgoldenrod', width = 0), fill='tozeroy'))
    solar_community.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    solar_community.update_yaxes(title_text="Power in kW", secondary_y=False)
    solar_community.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(solar_community)
    solar_community.update_layout(title = f'Solar to community battery for home {house_plot} in optimal operation')

    fig_bar_comparison_grid_energy = px.bar(result_csv, x='House number', y='Grid energy consumption (kWh)', 
                 color='Case type', barmode="group")
    fig_format(fig_bar_comparison_grid_energy)

    fig_bar_comparison_energy = px.bar(result_csv, x='House number', y='Total energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(fig_bar_comparison_energy)

    fig_bar_comparison_cost = px.bar(result_csv, x='House number', y='Energy consumption cost (€)', 
                    color='Case type', barmode="group")        
    fig_format(fig_bar_comparison_cost)

    fig_bar_comparison_heat_energy = px.bar(result_csv, x='House number', y='Total heat energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(fig_bar_comparison_heat_energy)

    fig_bar_comparison_EV_energy = px.bar(result_csv, x='House number', y='Net EV energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(fig_bar_comparison_EV_energy)

    fig_bar_comparison_self_cons_sol = px.bar(result_csv, x='House number', y='Self-consumption solar end (%)', 
                    color='Case type', barmode="group") 
    fig_format(fig_bar_comparison_self_cons_sol)

    fig_bar_comparison_self_cons_home = px.bar(result_csv, x='House number', y='Self-consumption home end (%)', 
                    color='Case type', barmode="group")  
    fig_format(fig_bar_comparison_self_cons_home)

    system_fig_bar_comparison_grid_energy = px.bar(system_results, x='Case type', y='Grid energy consumption (kWh)', 
                    color='Case type', barmode="group")
    fig_format(system_fig_bar_comparison_grid_energy)
    system_fig_bar_comparison_grid_energy.update_layout(autosize=False, width=300, height=500, showlegend=False)

    system_fig_bar_comparison_energy = px.bar(system_results, x='Case type', y='Total energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(system_fig_bar_comparison_energy)
    system_fig_bar_comparison_energy.update_layout(autosize=False, width=300, height=500, showlegend=False)
    
    system_fig_bar_comparison_cost = px.bar(system_results, x='Case type', y='Energy consumption cost (€)', 
                    color='Case type', barmode="group")  
    fig_format(system_fig_bar_comparison_cost)
    system_fig_bar_comparison_cost.update_layout(autosize=False, width=300, height=500, showlegend=False)

    system_fig_bar_comparison_heat_energy = px.bar(system_results, x='Case type', y='Total heat energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(system_fig_bar_comparison_heat_energy)
    system_fig_bar_comparison_heat_energy.update_layout(autosize=False, width=300, height=500, showlegend=False)
    
    system_fig_bar_comparison_EV_energy = px.bar(system_results, x='Case type', y='Net EV energy consumption (kWh)', 
                    color='Case type', barmode="group") 
    fig_format(system_fig_bar_comparison_EV_energy)
    system_fig_bar_comparison_EV_energy.update_layout(autosize=False, width=300, height=500, showlegend=False)

    system_fig_bar_comparison_self_cons_sol = px.bar(system_results, x='Case type', y='Self-consumption solar end (%)', 
                    color='Case type', barmode="group")                  
    fig_format(system_fig_bar_comparison_self_cons_sol)
    system_fig_bar_comparison_self_cons_sol.update_layout(autosize=False, width=300, height=500, showlegend=False)

    system_fig_bar_comparison_self_cons_home = px.bar(system_results, x='Case type', y='Self-consumption home end (%)', 
                    color='Case type', barmode="group") 
    fig_format(system_fig_bar_comparison_self_cons_home)
    system_fig_bar_comparison_self_cons_home.update_layout(autosize=False, width=300, height=500, showlegend=False)

    community_soc = make_subplots(specs=[[{"secondary_y": True}]])
    community_soc.add_trace(go.Scatter(x=time_axis, y=community_battery.value, name = 'Battery SoC', line=dict(color='thistle', width = 4)))
    community_soc.update_yaxes(title_text="SoC in kWh", secondary_y=False, )
    fig_format(community_soc)
    community_soc.update_layout(title = 'Community battery SoC for System')
    

    community_status = make_subplots(specs=[[{"secondary_y": True}]])
    community_status.add_trace(go.Scatter(x=time_axis, y=np.sum(solar_data_multi_home, axis = 1), name = 'Solar production', line=dict(color='mistyrose', width = 0), fill='tozeroy'))
    community_status.add_trace(go.Scatter(x=time_axis, y=np.sum(solar_to_community.value, axis = 1), name = 'Solar charge', line=dict(color='darkgoldenrod', width = 0), fill='tozeroy'))
    community_status.add_trace(go.Scatter(x=time_axis, y=low_price_charge_community.value, name = 'Grid charge', line=dict(color='fuchsia', width = 0), fill='tozeroy'))
    community_status.add_trace(go.Scatter(x=time_axis, y=np.sum(community_battery_discharge.value, axis = 1), name = 'Battery discharge', line=dict(color='midnightblue', width = 0), fill='tozeroy'))
    community_status.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    community_status.update_yaxes(title_text="Power in kW", secondary_y=False, range = [0,85])
    community_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)   
    fig_format(community_status)
    community_status.update_layout(title = 'Community battery charge/discharge in kW')
    

    load_change_grid_system = make_subplots(specs=[[{"secondary_y": True}]])
    load_change_grid_system.add_trace(go.Scatter(x=time_axis, y=net_system_grid_load_base, name = 'Reference scenario load', line=dict(color='aquamarine')))
    load_change_grid_system.add_trace(go.Scatter(x=time_axis, y=net_system_grid_load_optimal, name = 'Optimal control load', line=dict(color='teal')))
    load_change_grid_system.add_trace(go.Scatter(x=time_axis, y=(net_system_grid_load_optimal-net_system_grid_load_base), name = 'Change in load from reference', line=dict(color='burlywood', width = 0), fill='tozeroy'))
    load_change_grid_system.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    load_change_grid_system.update_yaxes(title_text="Net grid load in kW", secondary_y=False, )#
    load_change_grid_system.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(load_change_grid_system)
    load_change_grid_system.update_layout(title = 'Net grid load for System')
  
    
    return EV_soc_fig, temp_fig, load_change_grid, solar_consumption, optimal_applicance_status, base_case_appliance_status, solar_community,\
        community_soc, community_status, load_change_grid_system, fig_bar_comparison_grid_energy, fig_bar_comparison_energy,\
        fig_bar_comparison_cost, fig_bar_comparison_heat_energy, fig_bar_comparison_EV_energy,\
        fig_bar_comparison_self_cons_sol, fig_bar_comparison_self_cons_home, system_fig_bar_comparison_grid_energy, \
        system_fig_bar_comparison_energy, system_fig_bar_comparison_cost, \
        system_fig_bar_comparison_heat_energy, system_fig_bar_comparison_EV_energy,\
        system_fig_bar_comparison_self_cons_home, system_fig_bar_comparison_self_cons_sol

def st_plt_template (EV_soc_fig, temp_fig, load_change_grid, solar_consumption, optimal_applicance_status, base_case_appliance_status, solar_community,\
        community_soc, community_status, load_change_grid_system, fig_bar_comparison_grid_energy, fig_bar_comparison_energy,
        fig_bar_comparison_cost, fig_bar_comparison_heat_energy, fig_bar_comparison_EV_energy,
        fig_bar_comparison_self_cons_sol, fig_bar_comparison_self_cons_home, system_fig_bar_comparison_grid_energy, \
        system_fig_bar_comparison_energy, system_fig_bar_comparison_cost, \
        system_fig_bar_comparison_heat_energy, system_fig_bar_comparison_EV_energy,\
        system_fig_bar_comparison_self_cons_home, system_fig_bar_comparison_self_cons_sol, comm_batt):

    plots_left, plots_right = st.columns(2)
    with plots_left:
        st.plotly_chart(EV_soc_fig)
        st.plotly_chart(base_case_appliance_status)
        st.plotly_chart(solar_consumption)
        st.plotly_chart(load_change_grid)
        st.plotly_chart(fig_bar_comparison_grid_energy)
        st.plotly_chart(fig_bar_comparison_self_cons_sol)
        

    with plots_right:
        st.plotly_chart(temp_fig)
        st.plotly_chart(optimal_applicance_status)
        if comm_batt != 0:
            st.plotly_chart(solar_community)
        st.plotly_chart(fig_bar_comparison_energy)
        st.plotly_chart(fig_bar_comparison_cost)
        st.plotly_chart(fig_bar_comparison_self_cons_home)

    community_plot_left, community_plot_right = st.columns(2)
    with community_plot_left:
        if comm_batt != 0:
            st.plotly_chart(community_soc)
        st.plotly_chart(load_change_grid_system)

    with community_plot_right:
        if comm_batt != 0:
            st.plotly_chart(community_status)

    system_level_left_col, system_level_left_mid_col, system_level_mid_col, system_level_right_mid_col, system_level_right_col = st.columns(5)
    with system_level_left_col:
        st.plotly_chart(system_fig_bar_comparison_grid_energy)
        st.plotly_chart(system_fig_bar_comparison_self_cons_home)

    with system_level_left_mid_col:
        st.plotly_chart(system_fig_bar_comparison_energy)
        st.plotly_chart(system_fig_bar_comparison_self_cons_sol)

    with system_level_mid_col:
        st.plotly_chart(system_fig_bar_comparison_cost)

    with system_level_right_mid_col:
        st.plotly_chart(system_fig_bar_comparison_heat_energy)

    with system_level_right_col:
        st.plotly_chart(system_fig_bar_comparison_EV_energy)

    
        
        
        

