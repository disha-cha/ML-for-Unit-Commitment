"""Optimization Model Generator"""

from pyomo.environ import *


def get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm, time_periods=24, num_scenarios=1,
             num_nodes=0, num_lines=0, num_uncert=0, num_demands=0):
    """
    Initializes all the necessary sets for the optimization model based on the provided parameters.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the sets will be added.
        num_solar (int): Number of solar generators.
        num_wind (int): Number of wind generators.
        num_batt (int): Number of battery storage units.
        num_hydro (int): Number of hydro generators.
        num_therm (int): Number of new thermal generators.
        num_existing_therm (int): Number of existing thermal generators.
        time_periods (int): Number of time periods (default is 24).
        num_scenarios (int): Number of scenarios (default is 1, deterministic).
        num_nodes (int): Number of nodes in the network.
        num_lines (int): Number of transmission lines.
        num_uncert (int): Number of uncertainty realizations.
        num_demands (int): Number of demand points.

    Sets Defined:
        Gtherm: Set of thermal generators (existing and new).
        Ghydro: Set of hydro generators.
        Gsolar: Set of solar generators.
        Gwind: Set of wind generators.
        Gbatt: Set of battery storage units.
        G: All generators.
        Grerenew: Renewable generators (solar and wind).
        T: Time periods.
        T0: Time periods including time 0.
        S: Scenarios.
        O: Uncertainty realizations.
        N: Network nodes.
        L: Transmission lines.
        D: Demand points.
    """
    total_therm = num_existing_therm + num_therm

    # Define generator sets based on their types and sequential indexing
    model.Gtherm = Set(initialize=range(1, total_therm + 1))
    model.Ghydro = Set(initialize=range(total_therm + 1, total_therm + num_hydro + 1))
    model.Gsolar = Set(initialize=range(total_therm + num_hydro + 1, total_therm + num_hydro + num_solar + 1))
    model.Gwind = Set(
        initialize=range(total_therm + num_hydro + num_solar + 1, total_therm + num_hydro + num_solar + num_wind + 1))
    model.Gbatt = Set(initialize=range(total_therm + num_hydro + num_solar + num_wind + 1,
                                       total_therm + num_hydro + num_solar + num_wind + num_batt + 1))

    # Union of all generator types
    model.G = model.Gtherm | model.Ghydro | model.Gsolar | model.Gwind | model.Gbatt

    # Union of renewable generator types (solar and wind)
    model.Grenew = model.Gsolar | model.Gwind

    # Define other relevant sets
    model.T = RangeSet(1, time_periods)               # Time periods (1 to time_periods)
    model.T0 = RangeSet(0, time_periods)              # Time periods including time 0
    model.S = RangeSet(1, max(1, num_scenarios))      # Scenarios (1 to num_scenarios)
    model.O = RangeSet(1, max(1, num_uncert))         # Uncertainty realizations
    model.N = RangeSet(1, num_nodes)                  # Network nodes
    model.L = RangeSet(1, num_lines)                  # Transmission lines
    model.D = RangeSet(1, num_demands)                # Demand points


def get_parameters(model):
    """
    Initializes all the necessary parameters for the optimization model.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the parameters will be added.

    Parameters Defined:
        CapEx[g]: Fixed capital expenditure for generator g.
        OpEx[g]: Operational expenditure for generator g.
        CSU[g]: Start-up cost for generator g.
        CSD[g]: Shut-down cost for generator g.
        Pi[s]: Probability of scenario s.
        Pmin[g], Pmax[g]: Minimum and maximum power output of generator g.
        RU[g], RD[g]: Ramp-up and ramp-down rates for generator g.
        Dd[t]: Demand at time t.
        Pchg[g], Pdchg[g]: Maximum charging and discharging power for battery g.
        Hchg[g], Hdchg[g]: Charging and discharging efficiencies for battery g.
        SoCmin[g], SoCmax[g]: Minimum and maximum state of charge for battery g.
        Ecap[g]: Energy capacity of battery g.
        DODmax[g]: Maximum depth of discharge for battery g.
        Fmax[l]: Maximum power flow on line l.
        PTDF[n, l]: Power Transfer Distribution Factor for node n and line l.
        Xw[t, o]: Realized wind power availability for time t and uncertainty o.
        Xdemand[t, d]: Realized electric demand at demand point d and time t.
        Xd_uncert[t, o]: Uncertainty-adjusted demand at time t and uncertainty o.
        PXsmax[g, t, o]: Maximum available solar power for generator g, time t, and uncertainty o.
        Gam[g]: Wind distribution factor for wind generator g.
        SU[g], SD[g]: Start-up and shut-down rates for generator g.
        UT[g], DT[g]: Minimum up and down times for generator g.
        Rup[t], Rdn[t]: System-wide reserve up and reserve down requirements at time t.
        Lg[g, i], Ll[l, i], Ld[d, i]: Incidence matrices for generators, lines, and demands at node i.
        X[l]: Reactance of line l.
        Dl[d]: Load distribution factor for demand d.
        Dt: Time step duration.
        Inflow[g, t, s]: Water inflow for hydro generator g at time t in scenario s.
        Emin[g], Emax[g]: Minimum and maximum reservoir levels for hydro generator g.
        Qmin[g], Qmax[g]: Minimum and maximum water discharge for hydro generator g.
        Smax[g]: Maximum water spillage for hydro generator g.
        Hbase[g]: Base head for hydro generator g.
        Ebase[g]: Base reservoir level for hydro generator g.
        A[g], B[g]: Coefficients for reservoir level calculation for hydro generator g.
        H[g]: Efficiency of hydro generator g.
        X_pu[l]: Per-unit reactance for line l.
        S_base: Base power for the system (initialized to 100).
        Initial_SoC: Initial state of charge for batteries (initialized to 0.55).
        u_init[g, s]: Initial on/off status for generator g in scenario s (initialized to 0).
    """
    # Generator cost parameters
    model.CapEx = Param(model.G)
    model.OpEx = Param(model.G)
    model.CSU = Param(model.G)
    model.CSD = Param(model.G)

    # Scenario probability
    model.Pi = Param(model.S)

    # Power output limits
    model.Pmin = Param(model.G)
    model.Pmax = Param(model.G)

    # Ramp rates
    model.RU = Param(model.G)
    model.RD = Param(model.G)

    # Demand parameters
    model.Dd = Param(model.T)

    # Battery parameters
    model.Pchg = Param(model.Gbatt)
    model.Pdchg = Param(model.Gbatt)
    model.Hchg = Param(model.Gbatt)
    model.Hdchg = Param(model.Gbatt)
    model.SoCmin = Param(model.Gbatt)
    model.SoCmax = Param(model.Gbatt)
    model.Ecap = Param(model.Gbatt)
    model.DODmax = Param(model.Gbatt)

    # Hydro parameters
    model.Einit = Param(model.Ghydro)
    model.Efinal = Param(model.Ghydro)

    # Transmission line parameters
    model.Fmax = Param(model.L)
    model.PTDF = Param(model.N, model.L)

    # Renewable availability parameters
    # model.Xs = Param(model.T, model.O)  # Uncomment if solar availability is used
    model.Xw = Param(model.T, model.O)

    # Demand and uncertainty parameters
    model.Xdemand = Param(model.T, model.D, default=0)
    model.Xd_uncert = Param(model.T, model.O, default=0)

    # Solar availability based on uncertainty
    model.PXsmax = Param(model.Gsolar, model.T, model.O)

    # Wind distribution factors
    model.Gam = Param(model.Gwind)

    # Generator operational parameters
    model.SU = Param(model.G)
    model.SD = Param(model.G)
    model.UT = Param(model.G)
    model.DT = Param(model.G)

    # Reserve requirements
    model.Rup = Param(model.T)
    model.Rdn = Param(model.T)

    # Incidence matrices
    model.Lg = Param(model.G, model.N, default=0)  # Generator to node
    model.Ll = Param(model.L, model.N)             # Line to node
    model.Ld = Param(model.D, model.N)             # Demand to node

    # Transmission line connections and properties
    model.line_from = Param(model.L)
    model.line_to = Param(model.L)
    model.X = Param(model.L)                         # Reactance of line l
    model.Dl = Param(model.D)                        # Load distribution factor for demand d

    # Time step duration
    model.Dt = Param(initialize=1)

    # Hydro inflow and reservoir parameters
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

    # Additional power system parameters
    model.X_pu = Param(model.L)
    model.S_base = Param(initialize=100)            # Base power for per-unit calculations
    model.Initial_SoC = Param(initialize=0.55)      # Initial state of charge for batteries
    model.u_init = Param(model.G, model.S, initialize=lambda model, g, s: 0)  # Initial generator status


def get_variables(model):
    """
    Defines all the decision variables for the optimization model.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the variables will be added.

    Variables Defined:
        u[g, t, s]: Binary variable indicating if generator g is on at time t in scenario s.
        y[g, t, s]: Binary variable indicating if generator g starts up at time t in scenario s.
        z[g, t, s]: Binary variable indicating if generator g shuts down at time t in scenario s.
        p[g, t, s]: Non-negative real variable representing power output of generator g at time t in scenario s.
        r[g, t, s]: Non-negative real variable representing reserve provided by generator g at time t in scenario s.
        soc[g, t, s]: Non-negative real variable representing the state of charge for battery g at time t in scenario s.
        pchg[g, t, s], pdchg[g, t, s]: Non-negative real variables for charging and discharging power of battery g at time t in scenario s.
        uchg[g, t, s], udchg[g, t, s]: Binary variables indicating charging and discharging actions for battery g at time t in scenario s.
        ps[g, t, s, o]: Non-negative real variable for second-stage adjustment of generator g at time t in scenario s and uncertainty o.
        pmax[g, t, s]: Non-negative real variable for maximum available capacity of generator g at time t in scenario s.
        rU[g, t, s], rD[g, t, s]: Non-negative real variables for up and down reserves provided by generator g at time t in scenario s.
        uD[d, t, s, o]: Non-negative real variable for unserved demand at demand point d at time t in scenario s and uncertainty o.
        f[l, t, s, o]: Real variable representing power flow on line l at time t in scenario s and uncertainty o.
        th[i, t, s, o]: Real variable representing voltage angle at node i at time t in scenario s and uncertainty o.
        e[g, t, s]: Non-negative real variable representing reservoir level of hydro generator g at time t in scenario s.
        q[g, t, s]: Non-negative real variable for water discharge of hydro generator g at time t in scenario s.
        s[g, t, s]: Non-negative real variable for water spillage of hydro generator g at time t in scenario s.
        h[g, t, s]: Non-negative real variable for net head of hydro generator g at time t in scenario s.
    """
    # Generator operational variables
    model.u = Var(model.G, model.T0, model.S, within=Binary)  # On/off status
    model.y = Var(model.G, model.T, model.S, within=Binary, initialize=0)  # Start-up indicators
    model.z = Var(model.G, model.T, model.S, within=Binary, initialize=0)  # Shut-down indicators
    model.p = Var(model.G, model.T0, model.S, within=NonNegativeReals, initialize=0)  # Power output
    model.r = Var(model.G, model.T, model.S, within=NonNegativeReals)  # Reserve provided

    # Battery storage variables
    model.soc = Var(model.Gbatt, model.T0, model.S, within=NonNegativeReals)  # State of charge
    model.pchg = Var(model.Gbatt, model.T, model.S, within=NonNegativeReals, initialize=0)  # Charging power
    model.pdchg = Var(model.Gbatt, model.T, model.S, within=NonNegativeReals, initialize=0)  # Discharging power
    model.uchg = Var(model.Gbatt, model.T, model.S, within=Binary)  # Charging indicator
    model.udchg = Var(model.Gbatt, model.T, model.S, within=Binary)  # Discharging indicator

    # Adjustment and reserve variables
    model.ps = Var(model.G, model.T0, model.S, model.O, within=NonNegativeReals)  # Second-stage adjustment
    model.pmax = Var(model.G, model.T, model.S, within=NonNegativeReals)  # Maximum available capacity
    model.rU = Var(model.G, model.T, model.S, within=NonNegativeReals)  # Reserve up
    model.rD = Var(model.G, model.T, model.S, within=NonNegativeReals)  # Reserve down

    # Unserved demand and power flow variables
    model.uD = Var(model.D, model.T, model.S, model.O, within=NonNegativeReals)  # Unserved demand
    model.f = Var(model.L, model.T, model.S, model.O, within=Reals)  # Power flow on lines
    model.th = Var(model.N, model.T, model.S, model.O, within=Reals)  # Voltage angles

    # Hydro generator variables
    model.e = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)  # Reservoir level
    model.q = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)  # Water discharge
    model.s = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)  # Water spillage
    model.h = Var(model.Ghydro, model.T, model.S, within=NonNegativeReals)  # Net head


def get_objective(model, penalty=10000):
    """
    Defines the objective function for the optimization model, aiming to minimize the total operational cost.

    Components of the Objective Function:
        1. Variable costs of all generators.
        2. Start-up and shut-down costs for thermal generators.
        3. Operation and state change costs for battery storage units.
        4. Penalty costs for unserved demand.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the objective will be added.
        penalty (float): Penalty multiplier for unserved demand (default is 10,000).

    Returns:
        None: Adds the objective to the model.
    """
    def total_cost(model):
        # Variable costs: Operational expenditure multiplied by power output
        total_variable_cost = sum(model.OpEx[g] * model.p[g, t, s]
                                  for g in model.G for t in model.T for s in model.S)

        # Start-up and shut-down costs for thermal generators
        thermal_startup_shutdown_cost = sum(model.CSU[g] * model.y[g, t, s]
                                           + model.CSD[g] * model.z[g, t, s]
                                           for g in model.Gtherm for t in model.T for s in model.S)

        # Battery operation costs: Operational expenditure for charging and discharging
        battery_operation_cost = sum(model.OpEx[g] * (model.pchg[g, t, s] + model.pdchg[g, t, s])
                                     for g in model.Gbatt for t in model.T for s in model.S)

        # Battery state change costs: Costs associated with charging/discharging actions
        battery_state_change_cost = sum(
            (model.CSU[g] * (model.uchg[g, t, s] - (0 if t == model.T.first() else model.uchg[g, t-1, s])) +
             model.CSD[g] * (model.udchg[g, t, s] - (0 if t == model.T.first() else model.udchg[g, t-1, s])))
            for g in model.Gbatt for t in model.T for s in model.S
        )

        # Penalty for unserved demand to discourage unmet loads
        unserved_demand_cost = sum(penalty * model.uD[d, t, s, o]
                                   for d in model.D for t in model.T
                                   for s in model.S for o in model.O)

        # Total cost combines all components
        return (total_variable_cost + thermal_startup_shutdown_cost +
                battery_operation_cost + battery_state_change_cost + unserved_demand_cost)

    # Define the objective to minimize the total cost
    model.obj = Objective(rule=total_cost, sense=minimize)


def get_renewable_constraints(model):
    """
    Defines constraints related to renewable energy sources (solar and wind).

    Constraints Defined:
        1. Solar Generation Limits: Ensures solar power does not exceed maximum available based on availability.
        2. Solar Forecast Accuracy: Ensures power output adjustments do not result in negative surplus.
        3. Wind Generation Limits: Ensures wind power does not exceed maximum available based on wind distribution factor and availability.
        4. Wind Forecast Accuracy: Ensures power output adjustments do not result in negative surplus.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # Solar Generation Constraints
    def solar_limit_rule(model, g, t, s, o):
        """Ensure solar generation plus adjustments do not exceed maximum available solar power."""
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.PXsmax[g, t, o]

    def solar_forecast_rule(model, g, t, s, o):
        """Ensure that power output minus adjustments is non-negative."""
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Wind Generation Constraints
    def wind_limit_rule(model, g, t, s, o):
        """Ensure wind generation plus adjustments do not exceed maximum available wind power."""
        return model.p[g, t, s] + model.ps[g, t, s, o] <= model.Gam[g] * model.Xw[t, o]

    def wind_forecast_rule(model, g, t, s, o):
        """Ensure that wind power output minus adjustments is non-negative."""
        return model.p[g, t, s] - model.ps[g, t, s, o] >= 0

    # Apply constraints to the model for solar and wind generators
    model.solarlimit = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_limit_rule)
    model.solarforecast = Constraint(model.Gsolar, model.T, model.S, model.O, rule=solar_forecast_rule)
    model.windlimit = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_limit_rule)
    model.windforecast = Constraint(model.Gwind, model.T, model.S, model.O, rule=wind_forecast_rule)


def get_hydro_constraints(model):
    """
    Defines constraints specific to hydro generators, ensuring proper water and power balance.

    Constraints Defined:
        1. Water Balance: Ensures reservoir levels are maintained accounting for inflow, discharge, and spillage.
        2. Power Output: Links power output to water discharge and net head.
        3. Reservoir Limits: Keeps reservoir levels within minimum and maximum bounds.
        4. Discharge Limits: Restricts water discharge rates within operational limits.
        5. Spillage Limits: Restricts water spillage within operational limits.
        6. Head Calculation: Calculates net head based on reservoir levels and water discharge.
        7. Initial and Final Reservoir Levels: Ensures reservoir starts and ends at specified levels.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # Water Balance Constraint
    def water_balance_rule(model, g, t, s):
        """Ensure reservoir level accounts for inflow, discharge, and spillage."""
        if t == model.T.first():
            return model.e[g, t, s] == model.Einit[g] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]
        return model.e[g, t, s] == model.e[g, t - 1, s] + model.Inflow[g, t, s] - model.q[g, t, s] - model.s[g, t, s]

    # Power Output based on Water Discharge and Head
    def power_output_rule(model, g, t, s):
        """Link power output to water discharge and net head."""
        return model.p[g, t, s] == model.H[g] * model.q[g, t, s] * model.h[g, t, s]

    # Reservoir Level Limits
    def reservoir_limits_rule(model, g, t, s):
        """Keep reservoir levels within operational limits."""
        return (model.Emin[g], model.e[g, t, s], model.Emax[g])

    # Water Discharge Limits
    def discharge_limits_rule(model, g, t, s):
        """Restrict water discharge rates within operational limits."""
        return (model.Qmin[g], model.q[g, t, s], model.Qmax[g])

    # Spillage Limits
    def spillage_limits_rule(model, g, t, s):
        """Restrict water spillage within operational limits."""
        return (0, model.s[g, t, s], model.Smax[g])

    # Net Head Calculation
    def head_calculation_rule(model, g, t, s):
        """Calculate net head based on reservoir levels and water discharge."""
        return model.h[g, t, s] == model.Hbase[g] + model.A[g] * (model.e[g, t, s] - model.Ebase[g]) - model.B[g] * \
            model.q[g, t, s] ** 2

    # Initial Reservoir Level
    def initial_hydro_rule(model, g, s):
        """Set initial reservoir level for hydro generator."""
        return model.e[g, model.T.first(), s] == model.Einit[g]

    # Final Reservoir Level
    def final_hydro_rule(model, g, s):
        """Set final reservoir level for hydro generator."""
        return model.e[g, model.T.last(), s] == model.Efinal[g]

    # Apply all hydro-related constraints to the model
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
    Defines constraints specific to battery storage units, ensuring proper state of charge and operational limits.

    Constraints Defined:
        1. State of Charge (SoC) Limits: Keeps SoC within minimum and maximum bounds.
        2. Charging Power Limits: Restricts charging power within operational limits.
        3. Discharging Power Limits: Restricts discharging power within operational limits.
        4. SoC Update: Updates SoC based on charging and discharging actions.
        5. Exclusivity: Ensures that a battery cannot charge and discharge simultaneously.
        6. Initial SoC: Sets the initial state of charge for batteries.
        7. Initial Generator Status: Sets the initial on/off status for all generators.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # State of Charge Constraints
    def soc_min(model, g, t, s):
        """Ensure SoC is above the minimum threshold."""
        return model.SoCmin[g] <= model.soc[g, t, s]

    def soc_max(model, g, t, s):
        """Ensure SoC is below the maximum threshold."""
        return model.soc[g, t, s] <= model.SoCmax[g]

    # Charging Power Constraints
    def charge_power_min(model, g, t, s):
        """Ensure charging power is non-negative."""
        return 0 <= model.pchg[g, t, s]

    def charge_power_max(model, g, t, s):
        """Ensure charging power does not exceed maximum limit."""
        return model.pchg[g, t, s] <= model.Pchg[g]

    # Discharging Power Constraints
    def discharge_power_min(model, g, t, s):
        """Ensure discharging power is non-negative."""
        return 0 <= model.pdchg[g, t, s]

    def discharge_power_max(model, g, t, s):
        """Ensure discharging power does not exceed maximum limit."""
        return model.pdchg[g, t, s] <= model.Pdchg[g]

    # State of Charge Update
    def soc_update(model, g, t, s):
        """Update SoC based on charging and discharging actions."""
        return model.soc[g, t, s] == model.soc[g, t - 1, s] + \
               (model.Hchg[g] * model.pchg[g, t, s] - model.pdchg[g, t, s] / model.Hdchg[g]) * model.Dt

    # Exclusivity Constraint
    def exclusivity(model, g, t, s):
        """Ensure that a battery cannot charge and discharge at the same time."""
        return model.uchg[g, t, s] + model.udchg[g, t, s] <= 1

    # Initial State of Charge
    def initial_soc_rule(model, g, s):
        """Set the initial state of charge for each battery."""
        return model.soc[g, 0, s] == model.Initial_SoC

    # Initial Generator Status
    def initial_gen_status_rule(model, g, s):
        """Set the initial on/off status for each generator."""
        return model.u[g, 0, s] == model.u_init[g, s]

    # Apply all battery-related constraints to the model
    model.initial_soc = Constraint(model.Gbatt, model.S, rule=initial_soc_rule)
    model.initial_gen_status = Constraint(model.G, model.S, rule=initial_gen_status_rule)
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
    Defines nodal balance and DC Power Flow constraints using the reference node approach.

    Constraints Defined:
        1. Reference Node: Fixes the voltage angle of the reference node to zero.
        2. Nodal Power Balance: Ensures power generation, battery operations, and power flows satisfy demand at each node.
        3. DC Power Flow Equations: Relates power flows on transmission lines to voltage angle differences.
        4. Transmission Line Limits: Restricts power flows on lines within their capacity limits.
        5. System Balance: Ensures total generation minus total flow equals total demand system-wide.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # Reference node: Fix voltage angle to 0 to eliminate rotational symmetry
    def reference_node_rule(model, t, s, o):
        """Set the voltage angle of the reference node to zero."""
        return model.th[model.ref_node, t, s, o] == 0

    # Apply reference node constraint
    model.reference_constraint = Constraint(model.T, model.S, model.O, rule=reference_node_rule)

    # Nodal Power Balance Constraint
    def nodal_balance_rule(model, i, t, s, o):
        """
        Ensure that at each node, the sum of generated power, battery operations, and inflows equals
        the sum of power flows out and demand (including unserved demand).
        """
        # Sum of power generated by all generators connected to node i
        gen_sum = sum(model.Lg[g, i] * model.p[g, t, s] for g in model.G if model.Lg[g, i] != 0)

        # Sum of net battery discharging at node i
        batt_sum = sum(
            model.Lg[g, i] * (model.pdchg[g, t, s] - model.pchg[g, t, s]) for g in model.Gbatt if model.Lg[g, i] != 0)

        # Sum of power flows on all lines connected to node i
        flow_sum = sum(model.Ll[l, i] * model.f[l, t, s, o] for l in model.L if model.Ll[l, i] != 0)

        # Total demand at node i adjusted for unserved demand
        demand = sum(model.Ld[d, i] * (model.Xdemand[t, d] - model.uD[d, t, s, o])
                     for d in model.D
                     if model.Ld[d, i] != 0)

        # Power balance equation
        return gen_sum + batt_sum - flow_sum == demand

    # Apply nodal balance constraints to all nodes, time periods, scenarios, and uncertainties
    model.nodal_balance = Constraint(model.N, model.T, model.S, model.O, rule=nodal_balance_rule)

    # DC Power Flow Equations
    def dc_power_flow_rule(model, l, t, s, o):
        """
        Relate power flow on a transmission line to the voltage angle difference between its two ends.
        """
        from_bus = model.line_from[l]
        to_bus = model.line_to[l]
        return model.f[l, t, s, o] == (model.th[from_bus, t, s, o] - model.th[to_bus, t, s, o]) / model.X_pu[
            l] * model.S_base

    # Apply DC power flow constraints to all lines, time periods, scenarios, and uncertainties
    model.dc_power_flow = Constraint(model.L, model.T, model.S, model.O, rule=dc_power_flow_rule)

    # Transmission Line Limits
    def transmission_min_rule(model, l, t, s, o):
        """Ensure power flow on line l is not below its negative capacity."""
        return -model.Fmax[l] <= model.f[l, t, s, o]

    def transmission_max_rule(model, l, t, s, o):
        """Ensure power flow on line l does not exceed its maximum capacity."""
        return model.f[l, t, s, o] <= model.Fmax[l]

    # Apply transmission flow limits
    model.transmission_min = Constraint(model.L, model.T, model.S, model.O, rule=transmission_min_rule)
    model.transmission_max = Constraint(model.L, model.T, model.S, model.O, rule=transmission_max_rule)

    # System-Wide Power Balance
    def system_balance_rule(model, t, s, o):
        """Ensure total generation minus total flow equals total demand across the entire system."""
        total_gen = sum(model.p[g, t, s] for g in model.G)
        total_flow = sum(model.f[l, t, s, o] for l in model.L)
        total_demand = model.Dd[t]
        return total_gen - total_flow == total_demand

    # Apply system-wide balance constraints
    model.system_balance = Constraint(model.T, model.S, model.O, rule=system_balance_rule)


def get_reserve_constraints(model):
    """
    Defines constraints related to reserve requirements, ensuring system reliability.

    Constraints Defined:
        1. Reserve Up: Ensures that the total up reserves meet or exceed system-wide reserve up requirements.
        2. Reserve Down: Ensures that the total down reserves meet or exceed system-wide reserve down requirements.
        3. Reserve Max: Ensures that generation plus up reserves and adjustments do not exceed maximum capacity.
        4. Reserve Min: Ensures that generation minus down reserves and adjustments do not fall below minimum capacity.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # Reserve Up Constraint
    def reserve_up(model, t, s):
        """Ensure total up reserves meet system-wide requirements."""
        return sum(model.rU[g, t, s] for g in model.G) >= model.Rup[t]

    # Reserve Down Constraint
    def reserve_down(model, t, s):
        """Ensure total down reserves meet system-wide requirements."""
        return sum(model.rD[g, t, s] for g in model.G) >= model.Rdn[t]

    # Reserve Max Constraint
    def reserve_max(model, g, t, s, o):
        """
        Ensure that generator's power output plus up reserves and adjustments do not exceed its maximum capacity.
        This accounts for possible adjustments due to uncertainty.
        """
        return model.p[g, t, s] + model.rU[g, t, s] + model.ps[g, t, s, o] <= model.Pmax[g]

    # Reserve Min Constraint
    def reserve_min(model, g, t, s, o):
        """
        Ensure that generator's power output minus down reserves and adjustments does not fall below its minimum capacity.
        This accounts for possible adjustments due to uncertainty.
        """
        return model.p[g, t, s] - model.rD[g, t, s] - model.ps[g, t, s, o] >= model.Pmin[g] * model.u[g, t, s]

    # Apply reserve constraints to the model
    model.reserve_up = Constraint(model.T, model.S, rule=reserve_up)
    model.reserve_down = Constraint(model.T, model.S, rule=reserve_down)
    model.reserve_max = Constraint(model.G, model.T, model.S, model.O, rule=reserve_max)
    model.reserve_min = Constraint(model.G, model.T, model.S, model.O, rule=reserve_min)


def get_thermal_constraints(model):
    """
    Defines constraints specific to thermal generators, ensuring operational reliability and limits.

    Constraints Defined:
        1. Minimum Up Time: Ensures generators remain on for a minimum number of time periods after starting up.
        2. Minimum Down Time: Ensures generators remain off for a minimum number of time periods after shutting down.
        3. Logical Relationship: Links on/off status with start-up and shut-down actions.
        4. Power Output Limits: Ensures power output respects minimum and maximum limits based on generator status.
        5. Ramp-Up Constraints: Limits the rate at which power output can increase.
        6. Ramp-Down Constraints: Limits the rate at which power output can decrease.
        7. Start-Up and Shut-Down Limits: Prevents simultaneous start-up and shut-down actions.

    Parameters:
        model (AbstractModel): The Pyomo abstract model to which the constraints will be added.

    Returns:
        None: Adds the constraints to the model.
    """
    # Minimum Up Time Constraint
    def min_up_time_rule(model, g, s):
        """Ensure generators remain on for a minimum number of time periods after startup."""
        min_up = model.UT[g]
        # Simplified: Ensure that if generator is on at the first time period, it has been on for at least min_up periods
        return sum(model.y[g, t, s] for t in model.T if t <= min_up) >= model.u[g, 1, s]

    # Minimum Down Time Constraint
    def min_down_time_rule(model, g, s):
        """Ensure generators remain off for a minimum number of time periods after shutdown."""
        min_down = model.DT[g]
        # Simplified: Ensure that if generator is off at the first time period, it remains off for at least min_down periods
        return sum(model.z[g, t, s] for t in model.T if t <= min_down) >= 1 - model.u[g, 1, s]

    # Logical Relationship between on/off status and start-up/shut-down
    def logical_relationship_rule(model, g, t, s):
        """
        Link generator on/off status with start-up and shut-down actions.
        u[t] - u[t-1] = y[t] - z[t]
        """
        if t == model.T.first():
            return Constraint.Skip  # Initial condition is handled separately
        return model.u[g, t, s] - model.u[g, t - 1, s] == model.y[g, t, s] - model.z[g, t, s]

    # Power Output Minimum Constraint
    def power_output_min_rule(model, g, t, s):
        """Ensure power output is above minimum level if generator is on."""
        return model.Pmin[g] * model.u[g, t, s] <= model.p[g, t, s]

    # Power Output Maximum Constraint
    def power_output_max_rule(model, g, t, s):
        """Ensure power output does not exceed maximum capacity."""
        return model.p[g, t, s] <= model.Pmax[g] * model.u[g, t, s]

    # Ramp-Up Constraint
    def ramp_up_rule(model, g, t, s):
        """Limit the rate at which generator power output can increase."""
        if t == model.T.first():
            return Constraint.Skip  # No previous period to compare
        return model.p[g, t, s] - model.p[g, t - 1, s] <= model.RU[g]

    # Ramp-Down Constraint
    def ramp_down_rule(model, g, t, s):
        """Limit the rate at which generator power output can decrease."""
        if t == model.T.first():
            return Constraint.Skip  # No previous period to compare
        return model.p[g, t - 1, s] - model.p[g, t, s] <= model.RD[g]

    # Start-Up and Shut-Down Relationship
    def start_shutdown_rule(model, g, t, s):
        """Prevent simultaneous start-up and shut-down actions."""
        return model.y[g, t, s] + model.z[g, t, s] <= 1

    # Apply thermal generator constraints to the model
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
    """
    Generates the complete optimization model by initializing sets, parameters, variables, constraints, and the objective function.

    Parameters:
        num_solar (int): Number of solar generators (default is 0).
        num_wind (int): Number of wind generators (default is 0).
        num_batt (int): Number of battery storage units (default is 0).
        num_hydro (int): Number of hydro generators (default is 0).
        num_existing_therm (int): Number of existing thermal generators (default is 0).
        num_therm (int): Number of new thermal generators (default is 0).
        time_periods (int): Number of time periods (default is 24).
        num_scenarios (int): Number of scenarios (default is 1).
        num_nodes (int): Number of nodes in the network (default is 0).
        num_lines (int): Number of transmission lines (default is 0).
        num_uncert (int): Number of uncertainty realizations (default is 1).
        num_demands (int): Number of demand points (default is 0).
        slack_bus_id (int): Identifier for the slack/reference bus (default is None).

    Returns:
        AbstractModel: The fully constructed Pyomo abstract model ready for data instantiation and solving.
    """
    model_name = "Unit Commitment Model"
    model = AbstractModel(model_name)

    # Initialize sets based on the provided numbers of different generator types and system components
    get_sets(model, num_solar, num_wind, num_batt, num_hydro, num_therm, num_existing_therm,
             time_periods, num_scenarios, num_nodes, num_lines, num_uncert, num_demands)

    # Initialize all parameters required by the model
    get_parameters(model)

    # Set the reference node (slack bus) for the power flow constraints
    model.ref_node = Param(initialize=slack_bus_id)

    # Define all decision variables
    get_variables(model)

    # Define constraints based on the presence of renewable sources, hydro, batteries, and thermal generators
    if num_solar > 0 or num_wind > 0:
        get_renewable_constraints(model)
    if num_hydro > 0:
        get_hydro_constraints(model)
    if num_batt > 0:
        get_battery_constraints(model)
    if num_therm > 0:
        get_thermal_constraints(model)

    # Define power flow and reserve constraints irrespective of generator types
    get_power_DCPF_constraints(model)
    get_reserve_constraints(model)

    # Define the objective function to minimize total operational costs
    get_objective(model)

    return model

