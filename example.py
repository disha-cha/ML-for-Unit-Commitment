#!/usr/bin/env python
import sys

"""Example code to generate and solve UC MILP models"""

import pyomo.environ as pyo
from helpers import parsecase, add_gens_to_case
import pickle
import main as ucml
import pandapower
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.opt import SolverStatus, TerminationCondition
import json

net = pandapower.networks.case_ieee30()
original_therm = len(net.gen)

num_solar = 3
num_wind =3
num_hydro =3
num_batt = 3
num_therm = 3



# Usage
net = add_gens_to_case(net, num_solar, num_wind, num_batt, num_hydro, num_therm)

# single helper function so that the kwargs are the same
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

model_name = "UCModel" + "_".join([key + "=" + str(kwargs[key]) for key in kwargs])

db = parsecase(net, **kwargs)

with open("UCdata.p", "rb") as f:
    p_data = pickle.loads(pickle.load(f))


from main import opt_model_generator

opt_model_kwargs = kwargs.copy()

num_existing_therm = original_therm
opt_model_kwargs['num_existing_therm'] = num_existing_therm

slack_bus = p_data[None].get("slack_bus")


opt_model_kwargs = {
    'num_solar': num_solar,
    'num_wind': num_wind,
    'num_hydro': num_hydro,
    'num_batt': num_batt,
    'num_existing_therm': num_existing_therm,
    'num_therm': num_therm,
    'num_nodes': len(net.bus),
    'num_lines': len(net.line),
    'time_periods': 24,
    'num_scenarios': 1,
    'num_uncert': 1,
    'num_demands': len(net.load),
    'slack_bus_id': slack_bus
}

model = opt_model_generator(**opt_model_kwargs)
# model.pprint()

instance = model.create_instance(data=p_data)
# make into MPS file
# instance.write("data/" + model_name + ".mps")

solver = pyo.SolverFactory('gurobi')
result = solver.solve(instance, tee=False)

if result.solver.status == SolverStatus.ok and result.solver.termination_condition == TerminationCondition.optimal:
    if hasattr(result.problem, 'upper_bound') and hasattr(result.problem, 'lower_bound'):
        primal_bound = result.problem.upper_bound
        dual_bound = result.problem.lower_bound
        print("primal bound:", primal_bound)
        print("dual bound:", dual_bound)
    # with open("data/" + model_name + ".json", "w") as out:
    #     out.write(json.dumps({"dual_bound": dual_bound, "primal_bound": primal_bound}))
    print("optimal value:", pyo.value(instance.obj))
else:
    print("NO OPTIMAL VALUE FOUND")

# make a file with output json file, with name
# Extract and Plot Results
num_renew = num_solar + num_wind
num_gen = num_renew + num_hydro + num_batt + num_therm

# Define generator groups based on unique IDs
Gtherm = range(1, num_therm + 1)
Ghydro = range(num_therm + 1, num_therm + num_hydro + 1)
Gsolar = range(num_therm + num_hydro + 1, num_therm + num_hydro + num_solar + 1)
Gwind = range(num_therm + num_hydro + num_solar + 1, num_therm + num_hydro + num_solar + num_wind + 1)
Gbatt = range(num_therm + num_hydro + num_solar + num_wind + 1, num_gen + 1)
Grenew = list(Gsolar) + list(Gwind)
G = list(Gtherm) + list(Ghydro) + list(Gsolar) + list(Gwind) + list(Gbatt)


df = pd.DataFrame({
    'thermal': [sum(pyo.value(instance.p[g, t, s]) for g in Gtherm for s in range(1, kwargs['num_scenarios'] + 1)) for t in range(1, kwargs['time_periods'] + 1)],
    'solar': [sum(pyo.value(instance.p[g, t, s]) for g in Gsolar for s in range(1, kwargs['num_scenarios'] + 1)) for t in range(1, kwargs['time_periods'] + 1)],
    'wind': [sum(pyo.value(instance.p[g, t, s]) for g in Gwind for s in range(1, kwargs['num_scenarios'] + 1)) for t in range(1, kwargs['time_periods'] + 1)],
    'hydro': [sum(pyo.value(instance.p[g, t, s]) for g in Ghydro for s in range(1, kwargs['num_scenarios'] + 1)) for t in range(1, kwargs['time_periods'] + 1)],
    'battery': [sum(pyo.value(instance.p[g, t, s]) for g in Gbatt for s in range(1, kwargs['num_scenarios'] + 1)) for t in range(1, kwargs['time_periods'] + 1)],
})

ax = df.plot.area(stacked=True)
plt.xlabel('Time Period')
plt.ylabel('Power Output (MW)')
plt.title('Unit Commitment Results')
plt.legend(title='Generator Type')
plt.show()
