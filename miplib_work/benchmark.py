"""
9 benchmark suitable tests
each returns true if it passes
instances must pass all 9 requirements to be
benchmark suitable
"""
import pickle
from pyomo.opt import SolverStatus, TerminationCondition
import json
import pyomo as pyo
import scipy
import numpy as np
import math

def benchmark_1(model):
    # solve with solver,
    pass

import time

"""
returns true if model is benchmark suitable
"""
def benchmark_suitable(model, p):
    with open(p, "rb") as f:
        p_data = pickle.loads(pickle.load(f))  
    instance = model.create_instance(data=p_data)
    solver = pyo.SolverFactory('gurobi')
    start_time = time.time()
    result = solver.solve(instance, tee=False)
    end_time = time.time()
    time_elapsed = end_time - start_time
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
    m = solver._solver_model
    v = np.zeros(105)
    A = np.matrix(m.getA())
    print(A)
    cdyn = abs(m.getAttr("MaxCoeff")/m.getAttr("MinCoeff"))
    odyn = abs(m.getAttr("MaxObjCoeff")/m.getAttr("MinObjCoeff"))
    maxcoeff = abs(m.getAttr("MaxCoeff"))
    infeasible = result.solver.termination_condition == TerminationCondition.infeasible
    unbounded = result.solver.termination_condition == TerminationCondition.unbounded

    optval = pyo.value(instance.obj)
    nonzero = m.getAttr("NumNZs")
    

    # https://www.gurobi.com/documentation/current/refman/attributes.html#sec:Attributes 

    # edit to include multiple solvers
    # check if gurobi has get time/runtime
    if time_elapsed > 4 * 60 * 60: # B1: too hard
        return False
    if time_elapsed < 10: # B2: too easy
        return False
    if cdyn > 10 ** 6 or odyn > 10 ** 6: # B3: constraint and obj dynamism at most 10 ^ 6
        return False
    if maxcoeff > 10 ** 10: # B4: abs value of all matrix coeff  10^10
        return False
    if 0: # B5: results are consistent
        return False
    if 0: # B6: no indicator constraints, should be true for given UC model
        return False
    if unbounded: # B7: infeasible or has finite optimum
        return False
    if optval > 10 ** 10: # B8: infeasible or obj solution is smlaler than 10^10
        return False
    if nonzero > 10 ** 6: # B9: at most 10^6 nonzero entries, just counts coefficient matrix for now, check if should include obj, etc.
        return False
    return True
