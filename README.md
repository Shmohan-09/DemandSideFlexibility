# DemandSideFlexibility

The work looks into the integration of Demand-side Flexibility in Energy Communities.

## Folder description

### **AppModel**
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
- heat_share_man: This helps create interface of the webapp, and the possibility of taking inputs from the user (use this as filename to launch the WebApp)
- heat_share: The script contains the optimization function for heat planning in MILP and linear programming formulation, there is a choice to use between heat sharing and no heat sharing option by selecting option in the WebApp

**Energy community system**

**Data**
