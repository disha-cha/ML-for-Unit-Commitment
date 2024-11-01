#!/usr/bin/env python
"""Example code to generate and solve UC MILP models"""

import sys
import pyomo.environ as pyo
from helpers import parsecase, add_gens_to_case
import pickle
import main as ucml
import pandapower
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Read command-line arguments
num_solar = int(sys.argv[1])
num_wind = int(sys.argv[2])
num_hydro = int(sys.argv[3])
num_batt = int(sys.argv[4])
num_therm = int(sys.argv[5])

# Load the network
net = pandapower.networks.case_ieee30()
original_therm = len(net.gen)

# Add generators to the network
net = add_gens_to_case(net, num_solar, num_wind, num_batt, num_hydro, num_therm)

# Define kwargs for parsing and model generation
kwargs = {
    'num_solar': num_solar,
    'num_wind': num_wind,
    'num_hydro': num_hydro,
    'num_batt': num_batt,
    'num_therm': num_therm,
    'num_nodes': len(net.bus),
    'num_lines': len(net.line),
    'time_periods': 24,
    'num_scenarios': 1,
    'num_uncert': 1,
    'num_demands': len(net.load)
}

# Create model name
model_name = "UCModel" + "_".join([key + "=" + str(kwargs[key]) for key in kwargs])

# Parse case and get data
db = parsecase(net, **kwargs)

# Load data
with open("UCdata.p", "rb") as f:
    p_data = pickle.loads(pickle.load(f))

# Update kwargs for model generation
opt_model_kwargs = kwargs.copy()
num_existing_therm = original_therm
opt_model_kwargs['num_existing_therm'] = num_existing_therm

# Get slack bus ID
slack_bus = p_data[None].get("slack_bus")
opt_model_kwargs['slack_bus_id'] = slack_bus

# Generate the optimization model
model = ucml.opt_model_generator(**opt_model_kwargs)

# Create an instance of the model
instance = model.create_instance(data=p_data)

# Save the model as MPS file
instance.write("data/" + model_name + ".mps")

# Solve the model
solver = pyo.SolverFactory('gurobi')
result = solver.solve(instance, tee=False)

# Check solver status
if result.solver.status == SolverStatus.ok and result.solver.termination_condition == TerminationCondition.optimal:
    if hasattr(result.problem, 'upper_bound') and hasattr(result.problem, 'lower_bound'):
        primal_bound = result.problem.upper_bound
        dual_bound = result.problem.lower_bound
        print("Primal bound:", primal_bound)
        print("Dual bound:", dual_bound)
    else:
        primal_bound = pyo.value(instance.obj)
        dual_bound = None
    # Save results to JSON file
    with open("data/" + model_name + ".json", "w") as out:
        out.write(json.dumps({"dual_bound": dual_bound, "primal_bound": primal_bound}))
    print("Optimal value:", pyo.value(instance.obj))
else:
    print("No optimal value found")

# Extract and plot results
num_renew = num_solar + num_wind
num_gen = original_therm + num_therm + num_hydro + num_solar + num_wind + num_batt

# Define generator groups based on unique IDs
Gtherm = range(1, original_therm + num_therm + 1)
Ghydro = range(Gtherm.stop, Gtherm.stop + num_hydro)
Gsolar = range(Ghydro.stop, Ghydro.stop + num_solar)
Gwind = range(Gsolar.stop, Gsolar.stop + num_wind)
Gbatt = range(Gwind.stop, Gwind.stop + num_batt)
Grenew = list(Gsolar) + list(Gwind)
G = list(Gtherm) + list(Ghydro) + list(Gsolar) + list(Gwind) + list(Gbatt)

# Create a DataFrame for plotting
df = pd.DataFrame({
    'thermal': [sum(pyo.value(instance.p[g, t, 1]) for g in Gtherm) for t in range(1, kwargs['time_periods'] + 1)],
    'solar': [sum(pyo.value(instance.p[g, t, 1]) for g in Gsolar) for t in range(1, kwargs['time_periods'] + 1)],
    'wind': [sum(pyo.value(instance.p[g, t, 1]) for g in Gwind) for t in range(1, kwargs['time_periods'] + 1)],
    'hydro': [sum(pyo.value(instance.p[g, t, 1]) for g in Ghydro) for t in range(1, kwargs['time_periods'] + 1)],
    'battery': [sum(pyo.value(instance.pdchg[g, t, 1]) - pyo.value(instance.pchg[g, t, 1]) for g in Gbatt)
                for t in range(1, kwargs['time_periods'] + 1)],
})

# Plot the results
ax = df.plot.area(stacked=True)
plt.xlabel('Time Period')
plt.ylabel('Power Output (MW)')
plt.title('Unit Commitment Results')
plt.legend(title='Generator Type')
plt.show()
