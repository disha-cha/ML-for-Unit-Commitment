from pyomo.environ import *
import pyomo as pyo
import math

def benchmark_mip(D):
    model = ConcreteModel() # can be concrete?
    model.G = RangeSet(1, 3) # what is G?
    model.I = RangeSet(1, 3) # I = Icol union B
    model.x = Var(model.I, within = Binary)
    model.y = Var(model.K, within = NonNegativeReals)
    
    model.z = Var(within=(0, model.dmax))
    model.b = Param(model.I, initialize=1 + 1/20 * math.sqrt(min(model.t))) # min of t wi over w in W


    def beta_rule(model, i):
        min_time = min(solver_times[w][i] for w in solvers)
        return 1 + (1.0/20.0) * math.sqrt(min_time)
        
    model.beta = Param(model.I, initialize=beta_rule)
    model.obj = Objective(
        expr=sum(model.beta[i] * model.x[i] for i in model.I),
        sense=maximize
    )
    # model.obj = Objective(rule=summation(model.b, model.x), sense=maximize)
    
    def foura(k, l): # for all k, l in C - G
        return sum(model.x[i] for i in model.G) >= (1 - model.e) * model.d[k, l] * model.y[k]
    model.foura = Constraint(model.K, model.L, rule=foura)
    def fourb(k, l): # for all k, l in F - L
        return sum(model.x[i] for i in model.G) <= (1 + model.e) * model.d[k, l] * model.y[k]
    model.fourb = Constraint(model.K, model.L, rule=fourb)
    def fourg(r): # r in small, medium, is this important?
        return sum(model.x[i] for i in model.R[r]) <= model.p * sum(model.x[i] for i in model.I)
    model.fourg = Constraint(model.R, rule=fourg)
    # such that 4a, 4b, 4g and
    model.maxtwo = Constraint(rule=sum(model.x[i] for i in model.G) <= 2) # otherwise (no NEOS server)
    model.eightc = Constraint(rule=summation(model.tbar, model.x) <= model.tau) # otherwise (no NEOS server)
    
    solver = pyo.SolverFactory('gurobi')
    result = solver.solve(model, tee=False)
    return result.x # or whatever returns all the x[i], tells you which are selected to be the benchmark
