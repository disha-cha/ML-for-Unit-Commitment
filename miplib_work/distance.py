from pyomo.environ import *
import pyomo as pyo

def diversity_preselect(D):
    model = ConcreteModel() # can be concrete?
    model.G = RangeSet(1, 3) # what is G?
    model.x = Var(model.G, within = Binary)
    
    model.z = Var(within=(0, model.dmax))
    model.dmax = 0 # what is dmax
    def distance(model, i, j):
        if i != j:
            return model.z <= (D[i, j] - model.dmax) * model.w[i]* model.x[j] + model.dmax
    model.distance = Constraint(model.G, model.G, rule=distance)
    model.maxk = Constraint(rule=sum(model.x[i] for i in model.G) == model.k)
    model.atleastone = Constraint(rule=sum(model.x[i] for i in model.G) >= 1) # if G intersect B is not null
    model.obj = Objective(rule=model.z, sense=maximize)

    # instance = model.create_instance()
    # # make into MPS file
    # instance.write("data/" + model_name + ".mps")

    solver = pyo.SolverFactory('gurobi')
    result = solver.solve(model, tee=False)
    return result.x # or whatever returns all the x[i], tells you which are preselected
