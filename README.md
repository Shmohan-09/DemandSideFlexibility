# DemandSideFlexibility

The work looks into the integration of Demand-side Flexibility in Energy Communities.

## Folder description- AppModel
The **AppModel** folder has the scripts related to the demand side flexibility modeling.
The WebApps can be run with the help of command line with path in the folder using the command
_streamlit run filename.py_

The different models are related to 

**EV charging flexibility**
- EV_app_inputs: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- EV_model: The script contains the optimization function for EV charging flexibility in MILP and linear programming formulation, there is a choice to use between solve models by selecting option in the WebApp

**Heat planning flexibility**
- app_heating_main: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- app_heating_func: The script contains the optimization function for heat planning in MILP and linear programming formulation, there is a choice to use between solve models by selecting option in the WebApp

**Heat sharing flexibility**
- heat_share_main: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- heat_share: The script contains the optimization function for heat planning in MILP and linear programming formulation, there is a choice to use between heat sharing and no heat sharing option by selecting option in the WebApp

**Atomic devices**
- inflex_input: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- inflex_model: The script contains the optimization function for appliance scheduling

**Energy community system**
- app_community: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- input_read_community: Script to process EV schedule input file
- optimization_function: The script contains the optimization function for appliance scheduling
- plot_script: This gives the script to arrange and plot the different parameters for energy community
- base_case_heating_EV: This contains functions for uncontrolled EV charging, bang-bang heat control and solar power consumption

Plots: this script contains plot scripts for individual models

## Folder description- Data
The folder contains input data files for the models
- EV_schedule: File containing relevant inputs related to EV scheduling and solar capacity in Energy Community case
- heater_power_share, heater_power: Heater power for heat share case, and energy community case
- inflexibile_load: Profiles for energy community case
- Price and Price_high: Day ahead prices in €/kWh in hourly granularity for one day
- PV_Zürich: PV base generation data in Zürich for one year at hourly granularity
- R, R_share, R_community: Thermal resistivity for heating app, heat share case, and energy community case
- solar_capacity: For heat sharing case
- T_out_Zürich: Ambient data in Zürich for one year at hourly granularity
- T_set, T_set_share, T_set_community: Temperature setpoint for heating app, heat share case, and energy community case
- T_start_share, T_start: Initial temperature heat share case, and energy community case
- tao, tao_share, tao_community: Heat time constant for heating app, heat share case, and energy community case
