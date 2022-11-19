"""
This script is to generate EV plots
Inputs:
EV charge pattern
EV discharge pattern
SoC uncontrolled behavior
SoC deadline
SoC max
SoC min
Prices
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import numpy as np

def EV_plot_gen(simlength, soc, soc_min, soc_max, soc_deadline, EV_power, EV_status, V2G_status, battery_size, EV_flexible_window_timesteps, 
            solar_charge, solar_data, inflexible_load, optimize_mode, price):
    time_axis = pd.date_range(start = '2022-11-12', periods=simlength, freq="15min")

    def fig_format(fig):
        fig.update_layout({'plot_bgcolor': 'rgba(255,255,255,0)', 'paper_bgcolor': 'rgba(255,255,255,0)',})
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black', showgrid = True, gridcolor='rgba(224,224,224,50)',)
        fig.update_xaxes(showline=True, linewidth=2, linecolor='black', showgrid = False, gridcolor='rgba(224,224,224,30)',)
        fig.update_layout(autosize=False, width=900, height=500, font_family = 'Computer Modern', font_size = 18)
        fig.update_layout(legend=dict(orientation="h",yanchor="top", y = -0.2))

    fig_soc = make_subplots(specs=[[{"secondary_y": True}]])
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),battery_size), name = 'Battery size', line=dict(color='black')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_min), name = 'SoC min', line=dict(color='black', dash = 'dot')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_max),  name = 'SoC max', line=dict(color='black', dash = 'dash')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=np.full((simlength,),soc_deadline), name = 'SoC deadline', line=dict(color='#7f7f7f', dash = 'dash')))
    fig_soc.add_trace(go.Scatter(x=time_axis, y=soc.value, name = 'SoC optimal charging', line=dict(color='olivedrab')))
    # fig_soc.add_trace(go.Scatter(x=time_axis, y=soc_uncontrolled, name = 'SOC Uncontrolled Max', line=dict(color='#2ca02c', dash='dash')))
    # fig_soc.add_trace(go.Scatter(x=time_axis, y=soc_uncontrolled_to_optimal_soc, name = 'SoC uncontrolled charging', line=dict(color='olivedrab', dash='dot')))
    # fig_soc.add_trace(go.Scatter(x=time_axis, y=prices/1000, name = 'Prices', line=dict(color='#8c564b')), secondary_y=True)
    fig_soc.add_vrect(x0=time_axis[EV_flexible_window_timesteps[0]], x1=time_axis[EV_flexible_window_timesteps[1]], fillcolor="#7f7f7f", opacity=0.25, line_width=0)
    fig_soc.update_yaxes(title_text="SOC in kWh", secondary_y=False)
    fig_soc.update_yaxes(title_text="Price Level in €/kWh", secondary_y=True)
    fig_format(fig_soc)
    fig_soc.update_layout(title = 'SOC under different scenario')

    if optimize_mode == 'MILP':
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

    return fig_soc, fig_status

