# This is the script for EV charging Optimization - Capability of only one way energy transfer (Grid to Vehicle)
# import necessary libraries
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

def heat_plots(temperature, bang_bang_control_temp, T_upper_bound, T_lower_bound, T_set, T_out, solar_data, solar_charge, heater_status, prices,
                bang_bang_control_status, bang_bang_solar, heater_power, solve_model):
    
    time_axis = pd.date_range(date.today(), periods=len(temperature.value), freq="15min")
    def fig_format(fig):
        fig.update_layout({'plot_bgcolor': 'rgba(255,255,255,0)', 'paper_bgcolor': 'rgba(255,255,255,0)',})
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black', showgrid = True, gridcolor='rgba(224,224,224,50)',)
        fig.update_xaxes(showline=True, linewidth=2, linecolor='black', showgrid = False, gridcolor='rgba(224,224,224,30)',)
        fig.update_layout(autosize=False, width=1000, height=500, font_family = 'Arial', font_size = 18)
        fig.update_layout(legend=dict(orientation="h",yanchor="top", y = -0.2))

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
    if solve_model == 'MILP':
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
    # bangbangcontrol.write_image(f"{filename_cwd}/figures/fig9_non_var_setpoint.pdf")
    bangbangcontrol.update_layout(title = 'Heater Bang-bang Control')

    return fig_temp, optimal_status, bangbangcontrol