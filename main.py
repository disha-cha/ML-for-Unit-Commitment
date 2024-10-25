"""Optimization Model Generator"""

from pyomo.environ import *

def get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm, time_periods=24, num_scenarios=1,
             num_nodes=0, num_lines=0, num_uncert=0, num_demands=0):
    """
    G_solar = set of solar generators (first num_solar, from 1)
    G_wind = set of wind generators (next num_wind)
    G_hydro = set of hydro generators (next num_hydro)
    G_batt = set of battery storage units (next num_batt)
    G_therm = set of thermal generators (next G_therm)
    G = set of all generators
    G_renew = set of solar and wind generators (first num_renew generators, from 1)
    T = set of time periods
    S = set of scenarios (0 if deterministic, else indexed 1 to num_scenarios)
    N = set of nodes
    L = set of transmission lines
    O = set of uncertainty realizations (0 if deterministic, else indexed 1 to num_uncert)
    D = set of demands
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
    CapEx[g] = fixed cost of generator g
    OpEx[g] = variable cost of generator g
    CSU[g] = start up cost of generator g
    CSD[g] = shut down cost of generator g
    Pi[s] = probability of scenario s
    Pmin[g], Pmax[g] = min and max power output of generator g
    RU[g], RD[g] = ramp up and down rate of generator g
    Dd[t] = demand curve at time t
    Pchg[g] = max charging power for battery g
    Pdchg[g] = max discharging power for battery g
    Hchg[g] = charging efficiency of battery g
    Hdchg[g] = discharging efficiency of battery g
    SoCmin[g], SoCmax[g] = min and max state of charge for battery g
    Fmax[l] = max power flower on line l
    PTDF[n, l] = Power Transfer Distribution Factor for node n and line l
    # Xs[t, o] = realized solar power availability for scenario w and time t
    Xw[t, o] = realized wind power availability for scenario w and time t
    Xd[t, o, d] = realized electric demand for scenario w and time t
    PXsmax[g, t, o] = max available power from solar generator g based on realized solar availability
    Gam[g] = wind distribution factor for wind generator g
    SU[g], SD[g] = start-up and shut-down rates of generator g
    UT[g], DT[g] = min up and down times of generator g
    Rup[t], Rdn[t] = system-wide up and downward reserve requirements at time t
    L[g, i], L[l, i], L[d, i] = incidence matrices for generators, lines and loads
    X[l] = reactance of line l
    Dl[d] = load distribution factor for demand d
    Dt = time step duration
    Ecap[g] = energy capacity of battery g
    DODmax[g] = max allowable depth of discharge for battery g
    Inflow[g, t, s] = water inflow for hydro generator g at time t in scenario s
    Emin[g], Emax[g] = min and max reservoir levels for hydro generator g
    Qmin[g], Qmax[g] = min and max water discharge for hydro generator g
    Smax[g] = max water spillage for hydro generator g
    Hbase[g] = base head for hydro generator g
    Ebase[g] = base reservoir level for hydro generator g
    A[g], B[g] = initial and final reservoir levels for ghydro generator g
    H[g] = efficiency of hydro generator g
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
    model.PTDF = Param(model.N, model.L)
    # model.Xs = Param(model.T, model.O)  # Uncomment if Xs is used
    model.Xw = Param(model.T, model.O)
    model.Xdemand = Param(model.T, model.D, default=0)
    model.Xd_uncert = Param(model.T, model.O, default=0)
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
    model.line_from = Param(model.L)
    model.line_to = Param(model.L)
    model.X = Param(model.L)
    model.Dl = Param(model.D)
    model.Dt = Param(initialize=1)
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
    model.X_pu = Param(model.L)
    model.S_base = Param(initialize=100)
    model.Initial_SoC = Param(initialize=0.55)
    model.u_init = Param(model.G, model.S, initialize=lambda model, g, s: 0)


def get_variables(model):
    """
    u[g, t, s] = iff generator g is on at time t in scenario s (binary)
    y[g, t, s] = iff gneerator g starts up at time t in scenario s (binary)
    z[g, t, s] = iff generator g shuts down at time t in scenario s (binary)
    p[g, t, s] = power output of generator g at time t in scenario s
    r[g, t, s] = reserve provided by generator g at time t in scenario s
    soc[g, t, s] = state of charge for battery g at time t in scenario s
    pchg[g, t, s], pdchg[g, t, s] = charging and discharging power for battery g at time t in scenario s
    uchg[g, t, s], udchg[g, t, s] = charging and discharging of battery g at time t in scenario s (binary)
    ps[g, t, s, o] = second-stage adjustment of generator g at time t in scenario s and realization o
    pmax[g, t, s] = maximum available capacity of generator g at time t in scenario s
    rU[g, t, s], rD[g, t, s] = up and down reserves provided by generator g at time t in scenario s
    uD[d, t, s, o] = unserved demand at bus d at time t in scenario s and realization o
    f[l, t, s, o] = power flow on line l at time t in scenario s and realization o
    th[i, t, s, o] = voltage angle at bus i at time t in scenario s and realization o
    e[g, t, s] = reservoir level of hydro generator g at tiem t in scenario s
    q[g, t, s] = water discharge of hydro generator g at time t in scenario s
    s[g, t, s] = water spillage of hydro generator g at time t in scenario s
    h[g, t, s] = net head of hydro generator g at time t in scenario s
    """
    model.u = Var(model.G, model.T0, model.S, within = Binary)
    model.y = Var(model.G, model.T, model.S, within = Binary, initialize=0) ###
    model.z = Var(model.G, model.T, model.S, within = Binary, initialize=0) ###
    model.p = Var(model.G, model.T0, model.S, within = NonNegativeReals, initialize=0)
    model.r = Var(model.G, model.T, model.S, within = NonNegativeReals)
    model.soc = Var(model.Gbatt, model.T0, model.S, within = NonNegativeReals)
    model.pchg = Var(model.Gbatt, model.T, model.S, within = NonNegativeReals, initialize=0)
    model.pdchg = Var(model.Gbatt, model.T, model.S, within = NonNegativeReals, initialize=0)
    model.uchg = Var(model.Gbatt, model.T, model.S, within = Binary)
    model.udchg = Var(model.Gbatt, model.T, model.S, within = Binary)
    model.ps = Var(model.G, model.T0, model.S, model.O, within = NonNegativeReals)
    model.pmax = Var(model.G, model.T, model.S, within = NonNegativeReals)
    model.rU = Var(model.G, model.T, model.S, within = NonNegativeReals)
    model.rD = Var(model.G, model.T, model.S, within = NonNegativeReals)
    model.uD = Var(model.D, model.T, model.S, model.O, within = NonNegativeReals)
    model.f = Var(model.L, model.T, model.S, model.O, within = Reals)
    model.th = Var(model.N, model.T, model.S, model.O, within = Reals)
    model.e = Var(model.Ghydro, model.T, model.S, within = NonNegativeReals)
    model.q = Var(model.Ghydro, model.T, model.S, within = NonNegativeReals)
    model.s = Var(model.Ghydro, model.T, model.S, within = NonNegativeReals)
    model.h = Var(model.Ghydro, model.T, model.S, within = NonNegativeReals)

def get_objective(model, penalty=10000):
    def total_cost(model):
        # Fixed and variable costs for all generators
        total_fixed_cost = sum(model.CapEx[g]
                               for g in model.G for t in model.T for s in model.S)
        total_variable_cost = sum(model.OpEx[g] * model.p[g, t, s]
                                  for g in model.G for t in model.T for s in model.S)

        # Start-up and shut-down costs for thermal generators
        thermal_startup_shutdown_cost = sum(model.CSU[g] * model.y[g, t, s]
                                           + model.CSD[g] * model.z[g, t, s]
                                           for g in model.Gtherm for t in model.T for s in model.S)

        # Battery operation and state change costs
        battery_operation_cost = sum(model.OpEx[g] * (model.pchg[g, t, s] + model.pdchg[g, t, s])
                                     for g in model.Gbatt for t in model.T for s in model.S)

        battery_state_change_cost = sum(
            (model.CSU[g] * (model.uchg[g, t, s] - (0 if t == model.T.first() else model.uchg[g, t-1, s])) +
             model.CSD[g] * (model.udchg[g, t, s] - (0 if t == model.T.first() else model.udchg[g, t-1, s])))
            for g in model.Gbatt for t in model.T for s in model.S
        )

        # Penalty for unserved demand
        unserved_demand_cost = sum(penalty * model.uD[d, t, s, o]
                                   for d in model.D for t in model.T
                                   for s in model.S for o in model.O)
        # Total cost combining all components
        return (total_fixed_cost + total_variable_cost + thermal_startup_shutdown_cost +
                battery_operation_cost + battery_state_change_cost + unserved_demand_cost)
    model.obj = Objective(rule=total_cost, sense=minimize)



def get_renewable_constraints(model):
    def solar_limit_rule(model, g, t, s, o):
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.PXsmax[g, t, o]

    def solar_forecast_rule(model, g, t, s, o):
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Wind Generation Limits based on Availability
    def wind_limit_rule(model, g, t, s, o):
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.Gam[g] * model.Xw[t, o]

    def wind_forecast_rule(model, g, t, s, o):
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Apply constraints to the model
    model.solarlimit = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_limit_rule)
    model.solarforecast = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_forecast_rule)
    model.windlimit = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_limit_rule)
    model.windforecast = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_forecast_rule)



def get_hydro_constraints(model):
    """
    Defines constraints specific to Hydro Generators.
    """
    # Water Balance Constraint
    def water_balance_rule(model, g, t, s):
        if t == model.T.first():
            return model.e[g, t, s] == model.Einit[g] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]
        return model.e[g, t, s] == model.e[g, t-1, s] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]

    # Power Output based on Water Discharge and Head
    def power_output_rule(model, g, t, s):
        return model.p[g, t, s] == model.H[g] * model.q[g, t, s] * model.h[g,t,s]


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
        return model.h[g, t, s] == model.Hbase[g] + model.A[g] * (model.e[g, t, s] - model.Ebase[g]) - model.B[g] * \
            model.q[g, t, s] ** 2

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
    def soc_min(model, g, t, s):
        return model.SoCmin[g] <= model.soc[g, t, s]

    def soc_max(model, g, t, s):
        return model.soc[g, t, s] <= model.SoCmax[g]

    def charge_power_min(model, g, t, s):
        return 0 <= model.pchg[g, t, s]

    def charge_power_max(model, g, t, s):
        return model.pchg[g, t, s] <= model.Pchg[g]

    def discharge_power_min(model, g, t, s):
        return 0 <= model.pdchg[g, t, s]

    def discharge_power_max(model, g, t, s):
        return model.pdchg[g, t, s] <= model.Pdchg[g]

    def soc_update(model, g, t, s):
        return model.soc[g, t, s] == model.soc[g, t-1, s] + \
               (model.Hchg[g] * model.pchg[g, t, s] - model.pdchg[g, t, s] / model.Hdchg[g]) * model.Dt

    def exclusivity(model, g, t, s):
        return model.uchg[g, t, s] + model.udchg[g, t, s] <= 1

    def initial_soc_rule(model, g, s):
        return model.soc[g, 0, s] == model.Initial_SoC

    model.initial_soc = Constraint(model.Gbatt, model.S, rule=initial_soc_rule)

    # Initial Generator Status Constraint
    def initial_gen_status_rule(model, g, s):
        return model.u[g, 0, s] == model.u_init[g, s]

    model.initial_gen_status = Constraint(model.G, model.S, rule=initial_gen_status_rule)

    # Apply constraints to the model
    model.socmin = Constraint(model.Gbatt, model.T, model.S, rule=soc_min)
    model.socmax = Constraint(model.Gbatt, model.T, model.S, rule=soc_max)
    model.chargemin = Constraint(model.Gbatt, model.T, model.S, rule=charge_power_min)
    model.chargemax = Constraint(model.Gbatt, model.T, model.S, rule=charge_power_max)
    model.dischargemin = Constraint(model.Gbatt, model.T, model.S, rule=discharge_power_min)
    model.dischargemax = Constraint(model.Gbatt, model.T, model.S, rule=discharge_power_max)
    model.soc_update = Constraint(model.Gbatt, model.T, model.S, rule=soc_update)
    model.exclusivity = Constraint(model.Gbatt, model.T, model.S, rule=exclusivity)


def get_power_DCPF_constraints(model):
    """
    Defines nodal balance and DC power flow constraints using the reference node.
    """

    # Reference node: Fix voltage angle to 0
    def reference_node_rule(model, t, s, o):
        return model.th[model.ref_node, t, s, o] == 0  # For all time periods, scenarios, and uncertainties

    model.reference_constraint = Constraint(model.T, model.S, model.O, rule=reference_node_rule)


    # Nodal Power Balance
    def nodal_balance_rule(model, i, t, s, o):
        gen_sum = sum(model.Lg[g, i] * model.p[g, t, s] for g in model.G if model.Lg[g, i] != 0)
        batt_sum = sum(
            model.Lg[g, i] * (model.pdchg[g, t, s] - model.pchg[g, t, s]) for g in model.Gbatt if model.Lg[g, i] != 0)
        # Power flows on lines connected to node i
        flow_sum = sum(model.Ll[l, i] * model.f[l, t, s, o] for l in model.L if model.Ll[l, i] != 0)

        # Demand at node i
        demand = sum(model.Ld[d, i] * (model.Xdemand[t, d] - model.uD[d, t, s, o])
                     for d in model.D
                     if model.Ld[d, i] != 0)

        return gen_sum + batt_sum - flow_sum == demand

    model.nodal_balance = Constraint(model.N, model.T, model.S, model.O, rule=nodal_balance_rule)

    # DC Power Flow Equations
    def dc_power_flow_rule(model, l, t, s, o):
        from_bus = model.line_from[l]
        to_bus = model.line_to[l]
        return model.f[l, t, s, o] == (model.th[from_bus, t, s, o] - model.th[to_bus, t, s, o]) / model.X_pu[
            l] * model.S_base

    model.dc_power_flow = Constraint(model.L, model.T, model.S, model.O, rule=dc_power_flow_rule)

    # Transmission Line Limits
    def transmission_min_rule(model, l, t, s, o):
        return -model.Fmax[l] <= model.f[l, t, s, o]

    def transmission_max_rule(model, l, t, s, o):
        return model.f[l, t, s, o] <= model.Fmax[l]

    model.transmission_min = Constraint(model.L, model.T, model.S, model.O, rule=transmission_min_rule)
    model.transmission_max = Constraint(model.L, model.T, model.S, model.O, rule=transmission_max_rule)

    def system_balance_rule(model, t, s, o):
        total_gen = sum(model.p[g, t, s] for g in model.G)
        total_flow = sum(model.f[l, t, s, o] for l in model.L)
        total_demand = model.Dd[t]

        return total_gen - total_flow == total_demand

    model.system_balance = Constraint(model.T, model.S, model.O, rule=system_balance_rule)



def get_reserve_constraints(model):
    def reserve_up(model, t, s):
        # Reserve up constraint for all generator types
        return sum(model.rU[g, t, s] for g in model.G) >= model.Rup[t]

    def reserve_down(model, t, s):
        # Reserve down constraint for all generator types
        return sum(model.rD[g, t, s] for g in model.G) >= model.Rdn[t]

    def reserve_max(model, g, t, s, o):
        # Adjusting to account for battery charging/discharging in reserve
        return model.p[g, t, s] + model.rU[g, t, s] + model.ps[g, t, s, o] <= model.Pmax[g]

    def reserve_min(model, g, t, s, o):
        # Adjusting to account for battery charging/discharging in reserve
        return model.p[g, t, s] - model.rD[g, t, s] - model.ps[g, t, s, o] >= model.Pmin[g] * model.u[g, t, s]

    model.reserve_up = Constraint(model.T, model.S, rule=reserve_up)
    model.reserve_down = Constraint(model.T, model.S, rule=reserve_down)
    model.reserve_max = Constraint(model.G, model.T, model.S, model.O, rule=reserve_max)
    model.reserve_min = Constraint(model.G, model.T, model.S, model.O, rule=reserve_min)




def get_thermal_constraints(model):
    def min_up_time_rule(model, g, s):
        min_up = model.UT[g]
        return sum(model.y[g, t, s] for t in model.T if t <= min_up) >= model.u[g, 1, s]  # Simplified

    # Minimum Down Time
    def min_down_time_rule(model, g, s):
        min_down = model.DT[g]
        return sum(model.z[g, t, s] for t in model.T if t <= min_down) >= 1 - model.u[g, 1, s]  # Simplified

    # Logical relationship between on/off status and start-up/shut-down
    def logical_relationship_rule(model, g, t, s):
        if t == model.T.first():
            return Constraint.Skip  # Initial condition handled elsewhere
        return model.u[g, t, s] - model.u[g, t - 1, s] == model.y[g, t, s] - model.z[g, t, s]

    # Power Output Limits based on generator status
    def power_output_min_rule(model, g, t, s):
        return model.Pmin[g] * model.u[g, t, s] <= model.p[g, t, s]

    def power_output_max_rule(model, g, t, s):
        return model.p[g, t, s] <= model.Pmax[g] * model.u[g, t, s]

    # Ramp-Up Constraints
    def ramp_up_rule(model, g, t, s):
        if t == model.T.first():
            return Constraint.Skip  # Initial condition handled elsewhere
        return model.p[g, t, s] - model.p[g, t - 1, s] <= model.RU[g]

    # Ramp-Down Constraints
    def ramp_down_rule(model, g, t, s):
        if t == model.T.first():
            return Constraint.Skip  # Initial condition handled elsewhere
        return model.p[g, t - 1, s] - model.p[g, t, s] <= model.RD[g]

    # Start-Up and Shut-Down Constraints
    def start_shutdown_rule(model, g, t, s):
        return model.y[g, t, s] + model.z[g, t, s] <= 1

    # Apply constraints to the model
    model.min_up_time_rule = Constraint(model.Gtherm, model.S, rule=min_up_time_rule)
    model.min_down_time_rule = Constraint(model.Gtherm, model.S, rule=min_down_time_rule)
    model.logical_relationship = Constraint(model.Gtherm, model.T, model.S, rule=logical_relationship_rule)
    model.power_output_min = Constraint(model.Gtherm, model.T, model.S, rule=power_output_min_rule)
    model.power_output_max = Constraint(model.Gtherm, model.T, model.S, rule=power_output_max_rule)
    model.ramp_up = Constraint(model.Gtherm, model.T, model.S, rule=ramp_up_rule)
    model.ramp_down = Constraint(model.Gtherm, model.T, model.S, rule=ramp_down_rule)
    model.start_shutdown = Constraint(model.Gtherm, model.T, model.S, rule=start_shutdown_rule)


def opt_model_generator(num_solar=0, num_wind=0, num_batt=0, num_hydro=0, num_existing_therm=0, num_therm=0, time_periods=24,
                        num_scenarios=1, num_nodes=0, num_lines=0, num_uncert=1, num_demands=0, slack_bus_id=None):

    model_name = "UC Model"
    model = AbstractModel(model_name)


    # model set-up
    get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm,
             time_periods, num_scenarios, num_nodes, num_lines, num_uncert, num_demands)

    get_parameters(model)

    model.ref_node = Param(initialize=slack_bus_id)

    get_variables(model)

    # Define constraints
    if num_solar >0 or num_wind >0:
        get_renewable_constraints(model)
    if num_hydro > 0:
        get_hydro_constraints(model)
    if num_batt > 0:
        get_battery_constraints(model)
    if num_therm > 0:
        get_thermal_constraints(model)

    # Make sure to define the power flow constraints after ref_node is defined
    get_power_DCPF_constraints(model)
    get_reserve_constraints(model)
    get_objective(model)

    return model
