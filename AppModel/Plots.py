# This script is used to generate plots for heat, EV, and inflexible appliance planning
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import numpy as np
import streamlit as st

def fig_format(fig):
        fig.update_layout({'plot_bgcolor': 'rgba(255,255,255,0)', 'paper_bgcolor': 'rgba(255,255,255,0)',})
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black', showgrid = True, gridcolor='rgba(224,224,224,50)',)
        fig.update_xaxes(showline=True, linewidth=2, linecolor='black', showgrid = False, gridcolor='rgba(224,224,224,30)',)
        fig.update_layout(autosize=False, width=900, height=500, font_family = 'Computer Modern', font_size = 18)
        fig.update_layout(legend=dict(orientation="h",yanchor="top", y = -0.2))

def EV_plot_gen(simlength, soc, soc_min, soc_max, soc_deadline, EV_power, EV_status, V2G_status, battery_size, EV_flexible_window_timesteps, 
            solar_charge, solar_data, inflexible_load, solve_model, price, uncontrolled_to_optimal_soc_status, soc_uncontrolled_to_optimal_soc, solar_uncontrolled_to_optimal_soc_status):
    time_axis = pd.date_range(start = '2022-11-12', periods=simlength, freq="15min")
    fig_soc = make_subplots(specs=[[{"secondary_y": True}]])
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),battery_size), name = 'Battery size', line=dict(color='black')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_min), name = 'SoC min', line=dict(color='black', dash = 'dot')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_max),  name = 'SoC max', line=dict(color='black', dash = 'dash')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_deadline), name = 'SoC deadline', line=dict(color='#7f7f7f', dash = 'dash')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=soc.value, name = 'SoC optimal charging', line=dict(color='olivedrab')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=soc_uncontrolled_to_optimal_soc, name = 'SoC uncontrolled charging', line=dict(color='olivedrab', dash='dot')))
    fig_soc.add_vrect(x0=time_axis[EV_flexible_window_timesteps[0]], x1=time_axis[EV_flexible_window_timesteps[1]], fillcolor="#7f7f7f", opacity=0.25, line_width=0)
    fig_soc.update_yaxes(title_text="SOC in kWh", secondary_y=False)
    fig_soc.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(fig_soc)
    fig_soc.update_layout(title = 'SOC under different scenario')

    if solve_model == 'MILP':
        EV_status = EV_status*EV_power
        V2G_status = EV_power*V2G_status

    # to eliminate energy burn case while plot
    charge_state = EV_status.value - V2G_status.value 
    charge = np.zeros(simlength)
    discharge = np.zeros(simlength)
    for i in range(simlength):
        if charge_state[i] < 0:
            discharge[i] = - charge_state[i]
        elif charge_state[i] > 0:
            charge[i] = charge_state[i]

    fig_status = make_subplots(specs=[[{"secondary_y": True}]])
    fig_status.add_trace(go.Scatter(x=time_axis, y=solar_data, name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    fig_status.add_trace(go.Scatter(x=time_axis, y=charge, name = 'EV charge', line=dict(color='navy')))
    fig_status.add_trace(go.Scatter(x=time_axis, y=discharge, name = 'EV discharge', line=dict(color='#d62728', width = 0), fill = 'tozeroy'))
    fig_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value, name = 'Solar Consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'))
    fig_status.add_trace(go.Scatter(x=time_axis, y=inflexible_load, name = 'Inflexible load', line=dict(color='#17becf')))
    fig_status.add_trace(go.Scatter(x=time_axis, y=price/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    fig_status.add_vrect(x0=time_axis[EV_flexible_window_timesteps[0]], x1=time_axis[EV_flexible_window_timesteps[1]], fillcolor="#7f7f7f", opacity=0.25, line_width=0)
    fig_status.update_yaxes(title_text="Appliance status in kW", secondary_y=False)
    fig_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(fig_status)
    fig_status.update_layout(title = 'Appliance status in optimal charging condition', font_family = 'Computer Modern')

    fig_status_uncontrolled = make_subplots(specs=[[{"secondary_y": True}]])
    fig_status_uncontrolled.add_trace(go.Scatter(x=time_axis, y=solar_data, name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    fig_status_uncontrolled.add_trace(go.Scatter(x=time_axis, y=uncontrolled_to_optimal_soc_status, name = 'EV charge', line=dict(color='navy')))
    fig_status_uncontrolled.add_trace(go.Scatter(x=time_axis, y=solar_uncontrolled_to_optimal_soc_status, name = 'Solar Consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'))
    fig_status_uncontrolled.add_trace(go.Scatter(x=time_axis, y=inflexible_load, name = 'Inflexible load', line=dict(color='#17becf')))
    fig_status_uncontrolled.add_trace(go.Scatter(x=time_axis, y=price/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    fig_status_uncontrolled.add_vrect(x0=time_axis[EV_flexible_window_timesteps[0]], x1=time_axis[EV_flexible_window_timesteps[1]], fillcolor="#7f7f7f", opacity=0.25, line_width=0)
    fig_status_uncontrolled.update_yaxes(title_text="Appliance status in kW", secondary_y=False)
    fig_status_uncontrolled.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(fig_status_uncontrolled)
    fig_status_uncontrolled.update_layout(title = 'Appliance status in uncontrolled charging condition', font_family = 'Computer Modern')

    return fig_soc, fig_status, fig_status_uncontrolled

def heat_plots(temperature, bang_bang_control_temp, T_upper_bound, T_lower_bound, T_set, T_out, solar_data, solar_charge, heater_status, prices,
                bang_bang_control_status, bang_bang_solar, heater_power, solve_model):
    
    time_axis = pd.date_range(date.today(), periods=len(temperature.value), freq="15min")

    fig_temp = make_subplots(specs=[[{"secondary_y": True}]])
    fig_temp.add_trace(go.Scatter(x=time_axis, y=bang_bang_control_temp, name='Temperature bang-bang control', line=dict(color = 'pink', )), secondary_y=False)
    fig_temp.add_trace(go.Scatter(x=time_axis, y=temperature.value, name='Temperature optimal control', line=dict(color = 'red')), secondary_y=False)
    fig_temp.add_trace(go.Scatter(x=time_axis, y=T_out+15, name='Outside temperature + 15°C', line=dict(color='moccasin')), secondary_y=False)
    fig_temp.add_trace(go.Scatter(x=time_axis, y=T_upper_bound, name='Upper temperature bound', line=dict(color = 'black', dash = 'dash')), secondary_y=False)
    fig_temp.add_trace(go.Scatter(x=time_axis, y=T_lower_bound, name='Lower temperature bound', line=dict(color = 'black', dash = 'dot')), secondary_y=False)
    fig_temp.add_trace(go.Scatter(x=time_axis, y=T_set, name='Temperature set-point', line=dict(color = 'gray', dash = 'dot')), secondary_y=False)
    fig_temp.update_yaxes(title_text="Temperature in °C", secondary_y=False)
    fig_format(fig_temp)
    fig_temp.update_layout(title = 'Temperature evolution')
    if solve_model == 'Constant power':
        heater_status = heater_power*heater_status
    optimal_status = make_subplots(specs=[[{"secondary_y": True}]])
    optimal_status.add_trace(go.Scatter(x=time_axis, y=solar_data, name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    optimal_status.add_trace(go.Scatter(x=time_axis, y=heater_status.value/1000, name='Heater Status', line=dict(color='orchid')), secondary_y=False)
    optimal_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value, name='Solar power consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    optimal_status.add_trace(go.Scatter(x=time_axis, y=prices/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
    optimal_status.update_yaxes(title_text="Power in kW", secondary_y=False)
    optimal_status.update_yaxes(title_text="Price in €/kWh", secondary_y=True)
    fig_format(optimal_status)
    optimal_status.update_layout(title = 'Heater Optimal Control')


    bangbangcontrol = make_subplots(specs=[[{"secondary_y": True}]])
    bangbangcontrol.add_trace(go.Scatter(x=time_axis, y=solar_data, name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    bangbangcontrol.add_trace(go.Scatter(x=time_axis, y=bang_bang_control_status/1000,  name = 'Heater Status', line=dict(color='orchid')), secondary_y=False)
    bangbangcontrol.add_trace(go.Scatter(x=time_axis, y=bang_bang_solar, name='Solar power consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    bangbangcontrol.add_trace(go.Scatter(x=time_axis, y=prices/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
    bangbangcontrol.update_yaxes(title_text="Power in kW", secondary_y=False)
    bangbangcontrol.update_yaxes(title_text="Prices in €/kWh", secondary_y=True)
    fig_format(bangbangcontrol)
    bangbangcontrol.update_layout(title = 'Heater Bang-bang Control')
    return fig_temp, optimal_status, bangbangcontrol

def multi_heater_plot(price, T_upper_bound, T_lower_bound, temperature, house_number, T_set, T_out, solar_data_multi_home, solar_charge, heater_status):
    time_axis = pd.date_range(date.today(), periods=len(temperature.value), freq="15min")    

    heat_share_temp = make_subplots(specs=[[{"secondary_y": True}]])
    heat_share_temp = make_subplots(specs=[[{"secondary_y": True}]])
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=temperature.value[:,house_number], name='Temperature optimal control', line=dict(color = 'red')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_upper_bound[:,house_number], name='Upper temperature bound', line=dict(color = 'black', dash = 'dash')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_lower_bound[:,house_number], name='Lower temperature bound', line=dict(color = 'black', dash = 'dot')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_out[:,house_number]+15, name='Outside temperature + 15°C', line=dict(color='moccasin')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_set[:,house_number], name='Temperature set-point', line=dict(color = 'gray', dash = 'dot')), secondary_y=False)
    heat_share_temp.update_yaxes(title_text="Temperature in °C", secondary_y=False)
    fig_format(heat_share_temp)
    heat_share_temp.update_layout(title = 'Temperature Evolution Independent Setup')

    heat_share_status = make_subplots(specs=[[{"secondary_y": True}]])
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_number], name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=heater_status.value[:,house_number], name='Heater', line=dict(color='orchid')), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_number], name='Solar power consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=price/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
    heat_share_status.update_yaxes(title_text="Power in kW", secondary_y=False)
    heat_share_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(heat_share_status)
    heat_share_status.update_layout(title = 'Heater Status Independent Setup')

    return heat_share_temp, heat_share_status


def multi_heater_share_plot(price, T_upper_bound, T_lower_bound, temperature, house_number, T_set, T_out, solar_data_multi_home, solar_charge, heater_status, heater_status_ineff):
    time_axis = pd.date_range(date.today(), periods=len(temperature.value), freq="15min")  

    heat_share_temp = make_subplots(specs=[[{"secondary_y": True}]])
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=temperature.value[:,house_number], name='Temperature optimal control', line=dict(color = 'red')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_upper_bound[:,house_number], name='Upper temperature bound', line=dict(color = 'black', dash = 'dash')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_lower_bound[:,house_number], name='Lower temperature bound', line=dict(color = 'black', dash = 'dot')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_out[:,house_number]+15, name='Outside temperature + 15°C', line=dict(color='moccasin')), secondary_y=False)
    heat_share_temp.add_trace(go.Scatter(x=time_axis, y=T_set[:,house_number], name='Temperature set-point', line=dict(color = 'gray', dash = 'dot')), secondary_y=False)
    heat_share_temp.update_yaxes(title_text="Temperature in °C", secondary_y=False)
    fig_format(heat_share_temp)
    heat_share_temp.update_layout(title = 'Temperature Evolution Independent Setup')

    heat_share_status = make_subplots(specs=[[{"secondary_y": True}]])
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=solar_data_multi_home[:,house_number], name='Solar power generation', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=heater_status.value[:,house_number], name='Efficient heater', line=dict(color='orchid')), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=np.sum(heater_status.value, axis = 1), name='Net power efficient heater', line=dict(color='orchid', dash = 'dash')), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=heater_status_ineff.value[:,house_number], name='Inefficient heater', line=dict(color='mediumseagreen')), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value[:,house_number], name='Solar power consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    heat_share_status.add_trace(go.Scatter(x=time_axis, y=price/1000, name='Prices', line=dict(color = '#8c564b')), secondary_y=True)
    heat_share_status.update_yaxes(title_text="Power in kW", secondary_y=False)
    heat_share_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(heat_share_status)
    heat_share_status.update_layout(title = 'Heater Status Independent Setup')
    return heat_share_temp, heat_share_status

def plot_atomic(prices, appliance_status, base_profile, flexible_window_timesteps, solar_data, solar_charge):
    atomic_status = make_subplots(specs=[[{"secondary_y": True}]])
    time_axis = pd.date_range(date.today(), periods=len(prices), freq="15min")
    atomic_status.add_trace(go.Scatter(x=time_axis, y=solar_data, name='Solar Power Production', line=dict(color='mistyrose', width = 0), fill = 'tozeroy'), secondary_y=False)
    atomic_status.add_trace(go.Scatter(x=time_axis, y=appliance_status, name='Optimal appliance scheduling', line=dict(color='purple')), secondary_y=False)
    atomic_status.add_trace(go.Scatter(x=time_axis, y=base_profile, name='Base appliance scheduling', line=dict(color='purple', dash = 'dash')), secondary_y=False)
    # atomic_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value, name='Solar consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    atomic_status.add_trace(go.Scatter(x=time_axis, y=prices/1000, name='Prices', line=dict(color='#8c564b')), secondary_y=True)
    atomic_status.update_yaxes(title_text="Appliance Power Consumption in kW", secondary_y=False)
    atomic_status.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)    
    atomic_status.add_trace(go.Scatter(x=time_axis, y=solar_charge.value, name='Solar Power Consumption', line=dict(color='#bcbd22', width = 0), fill = 'tozeroy'), secondary_y=False)
    atomic_status.add_vrect(x0=time_axis[flexible_window_timesteps[0]], x1=time_axis[flexible_window_timesteps[1]], fillcolor="#7f7f7f", opacity=0.25, line_width=0)
    fig_format(atomic_status)

    return atomic_status
