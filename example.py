#!/usr/bin/env python
import sys

"""Example code to generate and solve a Unit Commitment (UC) MILP model."""

import pyomo.environ as pyo
from helpers import parsecase, add_gens_to_case
import pickle
import main as ucml
import pandapower
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.opt import SolverStatus, TerminationCondition
import json
import os
from datetime import datetime  # For timestamping model names

# Ensure the 'data' directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Read command-line arguments for the number of each generator type
if len(sys.argv) != 6:
    print("Usage: python example.py num_solar num_wind num_hydro num_batt num_therm")
    sys.exit(1)

num_solar = int(sys.argv[1])    # Number of solar generators to add
num_wind = int(sys.argv[2])     # Number of wind generators to add
num_hydro = int(sys.argv[3])    # Number of hydro generators to add
num_batt = int(sys.argv[4])     # Number of battery storage units to add
num_therm = int(sys.argv[5])    # Number of thermal generators to add

# Load the IEEE 30-bus test case network
net = pandapower.networks.case30()
original_therm = len(net.gen)  # Number of existing thermal generators

# Add specified generators to the network
net = add_gens_to_case(net, num_solar, num_wind, num_batt, num_hydro, num_therm)

# Define parameters for parsing and model generation
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

def get_next_output_id():
    counter_file = 'data/output_counter.txt'
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as f:
            output_id = int(f.read()) + 1
    else:
        output_id = 1
    with open(counter_file, 'w') as f:
        f.write(str(output_id))
    return output_id

output_id = get_next_output_id()
model_name = f"output_{output_id}"

# Parse the network case and generate data for the optimization model
db = parsecase(net, **kwargs)

# Load model data from the generated pickle file
with open("UCdata.p", "rb") as f:
    p_data = pickle.loads(pickle.load(f))

# Update parameters for model generation
opt_model_kwargs = kwargs.copy()
num_existing_therm = original_therm  # Number of original thermal generators
opt_model_kwargs['num_existing_therm'] = num_existing_therm

# Get slack bus ID from data
slack_bus = p_data[None].get("slack_bus")
opt_model_kwargs['slack_bus_id'] = slack_bus

# Generate the optimization model with the specified parameters
model = ucml.opt_model_generator(**opt_model_kwargs)

# Create an instance of the model with the data
instance = model.create_instance(data=p_data)

# Save the model as an MPS file for record-keeping or debugging
instance.write("data/" + model_name + ".mps")

# Solve the model using Gurobi solver
solver = pyo.SolverFactory('gurobi')
result = solver.solve(instance, tee=False)

# Check solver status and retrieve objective value
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
    sys.exit(1)  # Exit if no optimal solution is found

# Extract and plot results

# Define generator groups based on their IDs
Gtherm = range(1, original_therm + num_therm + 1)
Ghydro = range(Gtherm.stop, Gtherm.stop + num_hydro)
Gsolar = range(Ghydro.stop, Ghydro.stop + num_solar)
Gwind = range(Gsolar.stop, Gsolar.stop + num_wind)
Gbatt = range(Gwind.stop, Gwind.stop + num_batt)
Grenew = list(Gsolar) + list(Gwind)
G = list(Gtherm) + list(Ghydro) + list(Gsolar) + list(Gwind) + list(Gbatt)

# Calculate net battery power for each time period
battery_net = [
    sum(pyo.value(instance.pdchg[g, t, 1]) - pyo.value(instance.pchg[g, t, 1]) for g in Gbatt)
    for t in range(1, kwargs['time_periods'] + 1)
]

# Separate battery charging and discharging for plotting
battery_discharge = [max(0, x) for x in battery_net]  # Positive values indicate discharging
battery_charge = [min(0, x) for x in battery_net]     # Negative values indicate charging

# Create a DataFrame for plotting generation over time
df = pd.DataFrame({
    'thermal': [sum(pyo.value(instance.p[g, t, 1]) for g in Gtherm) for t in range(1, kwargs['time_periods'] + 1)],
    'solar': [sum(pyo.value(instance.p[g, t, 1]) for g in Gsolar) for t in range(1, kwargs['time_periods'] + 1)],
    'wind': [sum(pyo.value(instance.p[g, t, 1]) for g in Gwind) for t in range(1, kwargs['time_periods'] + 1)],
    'hydro': [sum(pyo.value(instance.p[g, t, 1]) for g in Ghydro) for t in range(1, kwargs['time_periods'] + 1)],
    'battery_discharge': battery_discharge,
    'battery_charge': battery_charge,
})

# Save the generation data to a CSV file
df.to_csv("data/" + model_name + "_results.csv", index=False)

# Plot the generation results
ax = df[['thermal', 'solar', 'wind', 'hydro', 'battery_discharge']].plot.area(stacked=True, figsize=(12, 6))
# Plot battery charging (negative values)
ax.fill_between(df.index, df['battery_charge'], 0, color='purple', step='mid', label='Battery Charging')
plt.xlabel('Time Period')
plt.ylabel('Power Output (MW)')
plt.title('Unit Commitment Results')
plt.legend(title='Generator Type')
plt.savefig("data/" + model_name + "_plot.png")
plt.show()
