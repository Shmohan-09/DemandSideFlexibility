"""
This code is to implement the functions for EV-flexibility using optimization (MILP and LP) for single vehicle
The functions are quite similar apart from the use of the variables related to power consumption - ev and v2h
ev - EV charging
v2h - EV discharging using vehicle to home (or vehicle to grid operation)
Imputs for the functions are:
EV size
EV charge power
EV plugin time
EV plugout time
Solar power integration power
Solar profile
Day for solar power use
Allowability of use of v2h and solar power
Input for an inflexible load (use time and power consumption)
"""
import cvxpy as cp

def EV_optimize_LP(SimLength, prices, inflexible_load, force_charge, reward_force_charge, ultra_high, reward_ultra_high_v2g,
                EV_power, soc_start, soc_max, soc_min, v2g_feasibility, solar_data, onsite_resource, eta, peak_house_load,
                EV_flexible_window_timesteps, soc_deadline):
    # declare variables
    solar_charge = cp.Variable(SimLength)
    EV_status = cp.Variable(SimLength) # a value of 1 implies that car is charging and 0 means that is it not being charged, irrespective of state of plugin
    V2G_status = cp.Variable(SimLength)
    soc = cp.Variable(SimLength) # defines the state of charge of the EV
    soc_t = soc[:-1] # simulation variable setup to define SOC
    soc_tplus1 = soc[1:] # simulation variable setup to define SOC
    solar_charge = cp.Variable(SimLength)
    EV_slack = cp.Variable(SimLength)
    EV_slack_deadline = cp.Variable()

    objective = cp.Minimize(cp.sum(prices@(EV_status - V2G_status + inflexible_load - solar_charge)/4) 
                - 1000*cp.sum(EV_slack_deadline) - 100000*cp.sum(EV_slack) + cp.sum(EV_status + V2G_status) 
                + force_charge*cp.sum(reward_force_charge@EV_status) + ultra_high*cp.sum(reward_ultra_high_v2g@(EV_status-V2G_status))
                ) 

    constraints = constraints = [
                  EV_status>=0, EV_status<=EV_power, soc[0] == soc_start, soc <= soc_max,
                  V2G_status <= EV_power*v2g_feasibility, V2G_status >= 0,
                  soc_tplus1 == soc_t + EV_status[:-1]*eta/4 - V2G_status[:-1]/eta/4,
                  EV_status[:EV_flexible_window_timesteps[0]] == 0, EV_status[EV_flexible_window_timesteps[1]:] == 0,
                  V2G_status[:EV_flexible_window_timesteps[0]] == 0, V2G_status[EV_flexible_window_timesteps[1]:] == 0,
                  EV_status - V2G_status + inflexible_load - solar_charge >= 0,
                  EV_slack <=0, EV_slack<= soc-soc_min,
                  solar_charge <= solar_data*onsite_resource, solar_charge >= 0,
                  peak_house_load >= EV_status + inflexible_load-V2G_status-solar_charge,
                  EV_slack_deadline <=0, EV_slack_deadline<= soc[-1]-soc_deadline,
                  ]
    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'ECOS', verbose = True)
    return EV_status, V2G_status, solar_charge, soc


def EV_optimize_MILP(SimLength, prices, inflexible_load, force_charge, reward_force_charge, ultra_high, reward_ultra_high_v2g,
                EV_power, soc_start, soc_max, soc_min, v2g_feasibility, solar_data, onsite_resource, eta, peak_house_load,
                EV_flexible_window_timesteps, soc_deadline, time_step_per_hour):
    # declare variables
    solar_charge = cp.Variable(SimLength)
    EV_status = cp.Variable(SimLength, integer = True) # a value of 1 implies that car is charging and 0 means that is it not being charged, irrespective of state of plugin
    V2G_status = cp.Variable(SimLength, integer = True)
    soc = cp.Variable(SimLength) # defines the state of charge of the EV
    soc_t = soc[:-1] # simulation variable setup to define SOC
    soc_tplus1 = soc[1:] # simulation variable setup to define SOC
    solar_charge = cp.Variable(SimLength)
    EV_slack = cp.Variable(SimLength)
    EV_slack_deadline = cp.Variable()

    objective = cp.Minimize(cp.sum(prices@(EV_power*EV_status + inflexible_load - v2g_feasibility*EV_power*V2G_status - onsite_resource*solar_charge)/4) 
                - 1000*cp.sum(EV_slack_deadline) - 100000*cp.sum(EV_slack) + force_charge*cp.sum(reward_force_charge@EV_status) 
                + ultra_high*cp.sum(reward_ultra_high_v2g@(EV_status -V2G_status))) 

    constraints = constraints = [
                  EV_status>=0, EV_status<=1, soc[0] == soc_start, soc <= soc_max, soc>=0,
                  V2G_status>=0, V2G_status<=1*v2g_feasibility, EV_status + V2G_status <= 1,
                  soc_tplus1 == soc_t + EV_status[:-1]*eta*EV_power/time_step_per_hour - V2G_status[:-1]*EV_power/time_step_per_hour,
                  EV_status[:EV_flexible_window_timesteps[0]] == 0, EV_status[EV_flexible_window_timesteps[1]:] == 0,
                  V2G_status[:EV_flexible_window_timesteps[0]] == 0, V2G_status[EV_flexible_window_timesteps[1]:] == 0,
                  EV_status + V2G_status <= 1,
                  (EV_status - V2G_status)*EV_power + inflexible_load - solar_charge >= 0,
                  EV_slack <=0, EV_slack<= soc-soc_min,
                  solar_charge <= solar_data*onsite_resource, solar_charge >= 0,
                  peak_house_load >= (EV_status - V2G_status)*EV_power + inflexible_load - solar_charge,
                  EV_slack_deadline <=0, EV_slack_deadline<= soc[-1]- soc_deadline,
                  ]
    prob = cp.Problem(objective, constraints)
    result = prob.solve(solver = 'GUROBI', verbose = True)
    return EV_status, V2G_status, solar_charge, soc