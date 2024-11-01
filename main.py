"""Optimization Model Generator"""

from pyomo.environ import *

def get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm, time_periods=24, num_scenarios=1,
             num_nodes=0, num_lines=0, num_uncert=0, num_demands=0):
    """
    Define the sets for the optimization model.
    """
    total_therm = num_existing_therm + num_therm

    # Define generator sets based on addition order
    model.Gtherm = Set(initialize=range(1, total_therm + 1))
    model.Ghydro = Set(initialize=range(total_therm + 1, total_therm + num_hydro + 1))
    model.Gsolar = Set(initialize=range(total_therm + num_hydro + 1, total_therm + num_hydro + num_solar + 1))
    model.Gwind = Set(
        initialize=range(total_therm + num_hydro + num_solar + 1, total_therm + num_hydro + num_solar + num_wind + 1))
    model.Gbatt = Set(initialize=range(total_therm + num_hydro + num_solar + num_wind + 1,
                                       total_therm + num_hydro + num_solar + num_wind + num_batt + 1))

    # All generators
    model.G = model.Gtherm | model.Ghydro | model.Gsolar | model.Gwind | model.Gbatt

    # Renewable generators (Solar + Wind)
    model.Grenew = model.Gsolar | model.Gwind

    # Other sets
    model.T = RangeSet(1, time_periods)
    model.T0 = RangeSet(0, time_periods)
    model.S = RangeSet(1, max(1, num_scenarios))
    model.O = RangeSet(1, max(1, num_uncert))
    model.N = RangeSet(1, num_nodes)
    model.L = RangeSet(1, num_lines)
    model.D = RangeSet(1, num_demands)


def get_parameters(model):
    """
    Define the parameters for the optimization model.
    """
    model.CapEx = Param(model.G)
    model.OpEx = Param(model.G)
    model.CSU = Param(model.G)
    model.CSD = Param(model.G)
    model.Pi = Param(model.S)
    model.Pmin = Param(model.G)
    model.Pmax = Param(model.G)
    model.RU = Param(model.G)
    model.RD = Param(model.G)
    model.Dd = Param(model.T)
    model.Pchg = Param(model.Gbatt)
    model.Pdchg = Param(model.Gbatt)
    model.Hchg = Param(model.Gbatt)
    model.Hdchg = Param(model.Gbatt)
    model.SoCmin = Param(model.Gbatt)
    model.SoCmax = Param(model.Gbatt)
    model.Ecap = Param(model.Gbatt)
    model.DODmax = Param(model.Gbatt)
    model.Einit = Param(model.Ghydro)
    model.Efinal = Param(model.Ghydro)
    model.Fmax = Param(model.L)
    model.line_from = Param(model.L)
    model.line_to = Param(model.L)
    model.X = Param(model.L)
    model.X_pu = Param(model.L)
    model.S_base = Param(initialize=100)
    model.Initial_SoC = Param(initialize=0.55)
    model.u_init = Param(model.G, model.S, initialize=lambda model, g, s: 0)
    model.Inflow = Param(model.Ghydro, model.T, model.S)
    model.Emin = Param(model.Ghydro)
    model.Emax = Param(model.Ghydro)
    model.Qmin = Param(model.Ghydro)
    model.Qmax = Param(model.Ghydro)
    model.H = Param(model.Ghydro)
    model.Hbase = Param(model.Ghydro)
    model.Ebase = Param(model.Ghydro)
    model.A = Param(model.Ghydro)
    model.B = Param(model.Ghydro)
    model.Smax = Param(model.Ghydro)
    model.Xs = Param(model.O, model.T, default=0)
    model.Xw = Param(model.T, model.O)
    model.PXsmax = Param(model.Gsolar, model.T, model.O)
    model.Gam = Param(model.Gwind)
    model.SU = Param(model.G)
    model.SD = Param(model.G)
    model.UT = Param(model.G)
    model.DT = Param(model.G)
    model.Rup = Param(model.T)
    model.Rdn = Param(model.T)
    model.Lg = Param(model.G, model.N, default=0)
    model.Ll = Param(model.L, model.N)
    model.Ld = Param(model.D, model.N)
    model.Xdemand = Param(model.T, model.D, default=0)
    model.uD = Param(model.D, model.T, model.S, model.O, default=0)
    model.Dl = Param(model.D)
    model.Dt = Param(initialize=1)
    model.slack_bus = Param()


def get_variables(model):
    """
    Define the variables for the optimization model.
    """
    model.u = Var(model.G, model.T0, model.S, within=Binary)
    model.y = Var(model.G, model.T, model.S, within=Binary, initialize=0)
    model.z = Var(model.G, model.T, model.S, within=Binary, initialize=0)
    model.p = Var(model.G, model.T0, model.S, within=NonNegativeReals, initialize=0)
    model.rU = Var(model.G, model.T, model.S, within=NonNegativeReals)
    model.rD = Var(model.G, model.T, model.S, within=NonNegativeReals)
    model.soc = Var(model.Gbatt, model.T0, model.S, within=NonNegativeReals)
    model.pchg = Var(model.Gbatt, model.T, model.S, within=NonNegativeReals, initialize=0)
    model.pdchg = Var(model.Gbatt, model.T, model.S, within=NonNegativeReals, initialize=0)
    model.uchg = Var(model.Gbatt, model.T, model.S, within=Binary)
    model.udchg = Var(model.Gbatt, model.T, model.S, within=Binary)
    model.ps = Var(model.G, model.T0, model.S, model.O, within=NonNegativeReals)
    model.f = Var(model.L, model.T, model.S, model.O, within=Reals)
    model.th = Var(model.N, model.T, model.S, model.O, within=Reals)
    model.e = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)
    model.q = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)
    model.s = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)
    model.h = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)


def get_objective(model, penalty=10000):
    """
    Define the objective function for the optimization model.
    """
    def total_cost(model):
        # Fixed and variable costs for all generators
        total_fixed_cost = sum(model.CapEx[g] for g in model.G for t in model.T for s in model.S)
        total_variable_cost = sum(model.OpEx[g] * model.p[g, t, s] for g in model.G for t in model.T for s in model.S)

        # Start-up and shut-down costs for thermal generators
        thermal_startup_shutdown_cost = sum(
            model.CSU[g] * model.y[g, t, s] + model.CSD[g] * model.z[g, t, s]
            for g in model.Gtherm for t in model.T for s in model.S
        )

        # Battery operation and state change costs
        battery_operation_cost = sum(
            model.OpEx[g] * (model.pchg[g, t, s] + model.pdchg[g, t, s])
            for g in model.Gbatt for t in model.T for s in model.S
        )

        battery_state_change_cost = sum(
            (model.CSU[g] * (model.uchg[g, t, s] - (0 if t == model.T.first() else model.uchg[g, t - 1, s])) +
             model.CSD[g] * (model.udchg[g, t, s] - (0 if t == model.T.first() else model.udchg[g, t - 1, s])))
            for g in model.Gbatt for t in model.T for s in model.S
        )

        # Penalty for unserved demand
        unserved_demand_cost = sum(
            penalty * model.uD[d, t, s, o]
            for d in model.D for t in model.T for s in model.S for o in model.O
        )

        # Total cost combining all components
        return (total_fixed_cost + total_variable_cost + thermal_startup_shutdown_cost +
                battery_operation_cost + battery_state_change_cost + unserved_demand_cost)

    model.obj = Objective(rule=total_cost, sense=minimize)


def get_renewable_constraints(model):
    """
    Define constraints specific to renewable generators (solar and wind).
    """

    # Solar Generation Limits
    def solar_limit_rule(model, g, t, s, o):
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.PXsmax[g, t, o]

    def solar_forecast_rule(model, g, t, s, o):
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Wind Generation Limits
    def wind_limit_rule(model, g, t, s, o):
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.Gam[g] * model.Xw[t, o] * model.Pmax[g]

    def wind_forecast_rule(model, g, t, s, o):
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Apply constraints to the model
    model.solarlimit = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_limit_rule)
    model.solarforecast = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_forecast_rule)
    model.windlimit = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_limit_rule)
    model.windforecast = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_forecast_rule)


def get_hydro_constraints(model):
    """
    Define constraints specific to Hydro Generators.
    """
    # Water Balance Constraint
    def water_balance_rule(model, g, t, s):
        if t == model.T.first():
            return model.e[g, t, s] == model.Einit[g] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]
        return model.e[g, t, s] == model.e[g, t - 1, s] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]

    # Power Output based on Water Discharge and Head
    def power_output_rule(model, g, t, s):
        return model.p[g, t, s] == model.H[g] * model.q[g, t, s] * model.h[g, t, s]

    # Reservoir Level Limits
    def reservoir_limits_rule(model, g, t, s):
        return (model.Emin[g], model.e[g, t, s], model.Emax[g])

    # Water Discharge Limits
    def discharge_limits_rule(model, g, t, s):
        return (model.Qmin[g], model.q[g, t, s], model.Qmax[g])

    # Spillage Limits
    def spillage_limits_rule(model, g, t, s):
        return (0, model.s[g, t, s], model.Smax[g])

    # Head Calculation
    def head_calculation_rule(model, g, t, s):
        return model.h[g, t, s] == model.Hbase[g] + model.A[g] * (model.e[g, t, s] - model.Ebase[g]) - \
               model.B[g] * model.q[g, t, s] ** 2

    # Initial and Final Reservoir Level
    def initial_hydro_rule(model, g, s):
        return model.e[g, model.T.first(), s] == model.Einit[g]

    def final_hydro_rule(model, g, s):
        return model.e[g, model.T.last(), s] == model.Efinal[g]

    # Apply constraints to the model
    model.water_balance = Constraint(model.Ghydro, model.T, model.S, rule=water_balance_rule)
    model.hydropower_output = Constraint(model.Ghydro, model.T, model.S, rule=power_output_rule)
    model.reservoir_limits = Constraint(model.Ghydro, model.T, model.S, rule=reservoir_limits_rule)
    model.discharge_limits = Constraint(model.Ghydro, model.T, model.S, rule=discharge_limits_rule)
    model.spillage_limits = Constraint(model.Ghydro, model.T, model.S, rule=spillage_limits_rule)
    model.head_calculation = Constraint(model.Ghydro, model.T, model.S, rule=head_calculation_rule)
    model.initial_hydro = Constraint(model.Ghydro, model.S, rule=initial_hydro_rule)
    model.final_hydro = Constraint(model.Ghydro, model.S, rule=final_hydro_rule)


def get_battery_constraints(model):
    """
    Define constraints specific to Battery Storage Units.
    """
    def soc_min(model, g, t, s):
        return model.SoCmin[g] * model.Ecap[g] <= model.soc[g, t, s]

    def soc_max(model, g, t, s):
        return model.soc[g, t, s] <= model.SoCmax[g] * model.Ecap[g]

    def charge_power_limits(model, g, t, s):
        return model.pchg[g, t, s] <= model.Pchg[g] * model.uchg[g, t, s]

    def discharge_power_limits(model, g, t, s):
        return model.pdchg[g, t, s] <= model.Pdchg[g] * model.udchg[g, t, s]

    def soc_update(model, g, t, s):
        if t == model.T.first():
            return model.soc[g, t, s] == model.Initial_SoC * model.Ecap[g] + \
                   (model.Hchg[g] * model.pchg[g, t, s] - model.pdchg[g, t, s] / model.Hdchg[g]) * model.Dt
        else:
            return model.soc[g, t, s] == model.soc[g, t - 1, s] + \
                   (model.Hchg[g] * model.pchg[g, t, s] - model.pdchg[g, t, s] / model.Hdchg[g]) * model.Dt

    def exclusivity(model, g, t, s):
        return model.uchg[g, t, s] + model.udchg[g, t, s] <= 1

    # Apply constraints to the model
    model.soc_min = Constraint(model.Gbatt, model.T, model.S, rule=soc_min)
    model.soc_max = Constraint(model.Gbatt, model.T, model.S, rule=soc_max)
    model.charge_limits = Constraint(model.Gbatt, model.T, model.S, rule=charge_power_limits)
    model.discharge_limits = Constraint(model.Gbatt, model.T, model.S, rule=discharge_power_limits)
    model.soc_update = Constraint(model.Gbatt, model.T, model.S, rule=soc_update)
    model.exclusivity = Constraint(model.Gbatt, model.T, model.S, rule=exclusivity)


def get_power_DCPF_constraints(model):
    """
    Define nodal balance and DC power flow constraints using the reference node.
    """
    # Reference node: Fix voltage angle to 0
    def reference_node_rule(model, t, s, o):
        return model.th[model.slack_bus, t, s, o] == 0

    model.reference_constraint = Constraint(model.T, model.S, model.O, rule=reference_node_rule)

    # Nodal Power Balance
    def nodal_balance_rule(model, i, t, s, o):
        gen_sum = sum(model.Lg[g, i] * (model.p[g, t, s] + model.ps[g, t, s, o]) for g in model.G if model.Lg[g, i] != 0)
        batt_sum = sum(
            model.Lg[g, i] * (model.pdchg[g, t, s] - model.pchg[g, t, s]) for g in model.Gbatt if model.Lg[g, i] != 0)
        # Power flows on lines connected to node i
        flow_sum = sum(model.Ll[l, i] * model.f[l, t, s, o] for l in model.L if model.Ll[l, i] != 0)

        # Demand at node i
        demand = sum(model.Ld[d, i] * (model.Xdemand[t, d] - model.uD[d, t, s, o])
                     for d in model.D if model.Ld[d, i] != 0)

        return gen_sum + batt_sum - flow_sum == demand

    model.nodal_balance = Constraint(model.N, model.T, model.S, model.O, rule=nodal_balance_rule)

    # DC Power Flow Equations
    def dc_power_flow_rule(model, l, t, s, o):
        from_bus = model.line_from[l]
        to_bus = model.line_to[l]
        return model.f[l, t, s, o] == (model.th[from_bus, t, s, o] - model.th[to_bus, t, s, o]) / model.X_pu[l] * model.S_base

    model.dc_power_flow = Constraint(model.L, model.T, model.S, model.O, rule=dc_power_flow_rule)

    # Transmission Line Limits
    def transmission_limits_rule(model, l, t, s, o):
        return (-model.Fmax[l], model.f[l, t, s, o], model.Fmax[l])

    model.transmission_limits = Constraint(model.L, model.T, model.S, model.O, rule=transmission_limits_rule)


def get_reserve_constraints(model):
    """
    Define reserve constraints.
    """
    def reserve_up(model, t, s):
        return sum(model.rU[g, t, s] for g in model.G) >= model.Rup[t]

    def reserve_down(model, t, s):
        return sum(model.rD[g, t, s] for g in model.G) >= model.Rdn[t]

    def reserve_max(model, g, t, s):
        return model.p[g, t, s] + model.rU[g, t, s] <= model.Pmax[g] * model.u[g, t, s]

    def reserve_min(model, g, t, s):
        return model.p[g, t, s] - model.rD[g, t, s] >= model.Pmin[g] * model.u[g, t, s]

    model.reserve_up = Constraint(model.T, model.S, rule=reserve_up)
    model.reserve_down = Constraint(model.T, model.S, rule=reserve_down)
    model.reserve_max = Constraint(model.G, model.T, model.S, rule=reserve_max)
    model.reserve_min = Constraint(model.G, model.T, model.S, rule=reserve_min)


def get_thermal_constraints(model):
    """
    Define constraints specific to Thermal Generators.
    """
    # Minimum Up Time
    def min_up_time_rule(model, g, t, s):
        if t < model.UT[g]:
            return Constraint.Skip
        else:
            return sum(1 - model.u[g, tau, s] for tau in range(t - model.UT[g] + 1, t + 1)) <= model.z[g, t, s]

    # Minimum Down Time
    def min_down_time_rule(model, g, t, s):
        if t < model.DT[g]:
            return Constraint.Skip
        else:
            return sum(model.u[g, tau, s] for tau in range(t - model.DT[g] + 1, t + 1)) <= model.u[g, t - model.DT[g], s] + model.y[g, t, s]

    # Logical relationship between on/off status and start-up/shut-down
    def logical_relationship_rule(model, g, t, s):
        if t == model.T.first():
            return model.u[g, t, s] - model.u_init[g, s] == model.y[g, t, s] - model.z[g, t, s]
        else:
            return model.u[g, t, s] - model.u[g, t - 1, s] == model.y[g, t, s] - model.z[g, t, s]

    # Power Output Limits based on generator status
    def power_output_limits_rule(model, g, t, s):
        return (model.Pmin[g] * model.u[g, t, s], model.p[g, t, s], model.Pmax[g] * model.u[g, t, s])

    # Ramp-Up Constraints
    def ramp_up_rule(model, g, t, s):
        if t == model.T.first():
            return Constraint.Skip
        else:
            return model.p[g, t, s] - model.p[g, t - 1, s] <= model.RU[g] * model.u[g, t - 1, s] + model.Pmax[g] * model.y[g, t, s]

    # Ramp-Down Constraints
    def ramp_down_rule(model, g, t, s):
        if t == model.T.first():
            return Constraint.Skip
        else:
            return model.p[g, t - 1, s] - model.p[g, t, s] <= model.RD[g] * model.u[g, t, s] + model.Pmax[g] * model.z[g, t, s]

    # Apply constraints to the model
    model.min_up_time_rule = Constraint(model.Gtherm, model.T, model.S, rule=min_up_time_rule)
    model.min_down_time_rule = Constraint(model.Gtherm, model.T, model.S, rule=min_down_time_rule)
    model.logical_relationship = Constraint(model.Gtherm, model.T, model.S, rule=logical_relationship_rule)
    model.power_output_limits = Constraint(model.Gtherm, model.T, model.S, rule=power_output_limits_rule)
    model.ramp_up = Constraint(model.Gtherm, model.T, model.S, rule=ramp_up_rule)
    model.ramp_down = Constraint(model.Gtherm, model.T, model.S, rule=ramp_down_rule)


def opt_model_generator(num_solar=0, num_wind=0, num_batt=0, num_hydro=0, num_existing_therm=0, num_therm=0, time_periods=24,
                        num_scenarios=1, num_nodes=0, num_lines=0, num_uncert=1, num_demands=0, slack_bus_id=None):
    """
    Generates the optimization model for unit commitment.
    """
    model_name = "UC Model"
    model = AbstractModel(model_name)

    # Model set-up
    get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm,
             time_periods, num_scenarios, num_nodes, num_lines, num_uncert, num_demands)

    get_parameters(model)

    model.slack_bus = Param(initialize=slack_bus_id)

    get_variables(model)

    # Define constraints
    if num_solar > 0 or num_wind > 0:
        get_renewable_constraints(model)
    if num_hydro > 0:
        get_hydro_constraints(model)
    if num_batt > 0:
        get_battery_constraints(model)
    if num_therm > 0:
        get_thermal_constraints(model)

    # Power flow and reserve constraints
    get_power_DCPF_constraints(model)
    get_reserve_constraints(model)
    get_objective(model)

    return model
