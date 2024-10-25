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

# import time

def get_feature_vector(model, p):
    with open(p, "rb") as f:
        p_data = pickle.loads(pickle.load(f))  
    instance = model.create_instance(data=p_data)
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
    m = solver._solver_model
    v = np.zeros(105)
    A = np.matrix(m.getA())
    print(A)
    c = m.getObjective() # probably not a vector
    m, n = A.shape
    # size
    gsize = np.square(np.log10(np.array([m, n, m.getAttr("NumNZs")])))
    v[1] = gsize[0]
    v[2] = gsize[1]
    v[3] = gsize[2] # nonzero in A

    # variable types
    n = m.getAttr("NumVars")
    nb = m.getAttr("NumBinVars")
    ni = m.getAttr("NumIntVars")
    nc = n - ni - nb
    propb = nb/n
    propi = ni/n
    propc = nc/n
    v[4] = propb
    v[5] = propi
    v[6] = propc

    # objective coefficients
    cscale = m.getAttr("MaxObjCoeff")
    cnorm = c / cscale
    cmin = m.getAttr("MinObjCoeff")/cscale # or 0? NEED TO NORMALIZE
    cmax = 1
    cmean = np.mean(cnorm) # mean of c
    cmedian = np.median(cnorm) # median of c
    cstd = np.std(cnorm) # sd of c
    cdynamism = cmax / cmin # cmin not zero here
    v[12] = cmin
    v[13] = cmax
    v[14] = cmean
    v[15] = cmedian
    v[16] = cstd
    v[17] = cdynamism

    # variable bounds

    ub = None
    lb = None

    ustats = get_vector_statistics(ub)
    ulstats = get_vector_statistics(ub - lb)








    # https://www.gurobi.com/documentation/current/refman/attributes.html#sec:Attributes 

    # edit to include multiple solvers
    # check if gurobi has get time/runtime



def get_vector_statistics(v):
    vmin = np.min(v)
    vmax = np.max(v)
    vmean = np.mean(v) # mean of c
    vmedian = np.median(v) # median of c
    vstd = np.std(v) # sd of c
    return np.array([vmin, vmax, vmean, vmedian, vstd])

import math
def siglog(x):
    return np.sign(x) * math.log(abs(x) + 1)