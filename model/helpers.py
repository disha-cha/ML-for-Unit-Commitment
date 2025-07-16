"""Helper functions for using generated optimization models"""

import pickle
import random
import pandapower as pp
import networkx as nx
import numpy as np


def parsecase(net, num_solar=0, num_wind=0, num_batt=0, num_hydro=0, num_therm=0, time_periods=24, num_scenarios=1,
             num_nodes=0, num_lines=0, num_uncert=1, num_demands=0):
    """
    Parses a pandapower network and generates parameter dictionaries required for the optimization model.

    Parameters:
        net (pandapower.Network): The pandapower network object to parse.
        num_solar (int): Number of solar generators to include.
        num_wind (int): Number of wind generators to include.
        num_batt (int): Number of battery storage units to include.
        num_hydro (int): Number of hydro generators to include.
        num_therm (int): Number of thermal generators to include.
        time_periods (int): Number of time periods (default is 24).
        num_scenarios (int): Number of scenarios for uncertainty (default is 1).
        num_nodes (int): Number of network nodes.
        num_lines (int): Number of transmission lines.
        num_uncert (int): Number of uncertainty realizations (default is 1).
        num_demands (int): Number of demand points.

    Returns:
        bytes: Serialized parameter data for the optimization model.
    """
    p = {}

    # Initialize generator ID offset for sequential indexing
    gen_offset = 1

    # Extract and index Thermal Generators
    thermal_gens = net.gen[net.gen.type == "Thermal"].reset_index(drop=True)
    Gtherm = list(range(gen_offset, gen_offset + len(thermal_gens)))
    gen_offset += len(Gtherm)

    # Extract and index Hydro Generators
    hydro_gens = net.gen[net.gen.type == "Hydro"].reset_index(drop=True)
    Ghydro = list(range(gen_offset, gen_offset + len(hydro_gens)))
    gen_offset += len(Ghydro)

    # Extract and index Solar Generators (PV)
    solar_sgens = net.sgen[net.sgen.type == "PV"].reset_index(drop=True)
    Gsolar = list(range(gen_offset, gen_offset + len(solar_sgens)))
    gen_offset += len(Gsolar)

    # Extract and index Wind Generators (WP)
    wind_sgens = net.sgen[net.sgen.type == "WP"].reset_index(drop=True)
    Gwind = list(range(gen_offset, gen_offset + len(wind_sgens)))
    gen_offset += len(Gwind)

    # Extract and index Battery Storage Units (BT)
    battery_storage = net.storage[net.storage.type == "BT"].reset_index(drop=True)
    Gbatt = list(range(gen_offset, gen_offset + len(battery_storage)))

    # Combine Renewable Generators (Solar + Wind)
    Grenew = Gsolar + Gwind

    # Combine All Generators
    G = Gtherm + Ghydro + Gsolar + Gwind + Gbatt

    # Define Sets for Time, Scenarios, Nodes, Lines, Uncertainties, and Demands
    T = range(1, time_periods + 1)                     # Time periods
    S = range(1, num_scenarios + 1)                    # Scenarios
    N = range(1, num_nodes + 1)                        # Network nodes
    L = range(1, num_lines + 1)                        # Transmission lines
    O = range(1, num_uncert + 1)                       # Uncertainty realizations
    D = range(1, num_demands + 1)                      # Demand points

    # Assign Generator Types to Thermal Generators
    therm_types = ['coal', 'ccgt']                      # Possible types for thermal generators
    gen_types = {g: random.choice(therm_types) for g in Gtherm}

    # Define Variable Operational Expenditure (OpEx) for Each Generator
    p["OpEx"] = {
        g: random_range(0, 1.05) if g in Gsolar else                     # Solar PV: $0-$1 per MWh
        random_range(0, 1.05) if g in Gwind else                         # Wind: $0-$1 per MWh
        random_range(1.9, 2.1) if g in Ghydro else                       # Hydro: $2 ±5% per MWh
        random_range(7.6, 8.4) if g in Gbatt else                        # Battery: $8 ±5% per MWh
        random_range(38, 42) if gen_types[g] == 'coal' else              # Coal: $40 ±5% per MWh
        random_range(28.5, 31.5)                                         # CCGT: $30 ±5% per MWh
        for g in G
    }

    # Define Start-Up Costs (CSU) for Each Generator
    p["CSU"] = {
        g: 0 if g in Grenew or g in Gbatt else
        random_range(1.9, 2.1) if g in Ghydro else                       # Hydro: $2 ±5% per MW per Start
        random_range(95, 105) if gen_types[g] == 'coal' else             # Coal: $100 ±5% per MW per Start
        random_range(47.5, 52.5)                                        # CCGT: $50 ±5% per MW per Start
        for g in G
    }

    # Define Shut-Down Costs (CSD) for Each Generator
    p["CSD"] = {
        g: 0 if g in Grenew or g in Gbatt else
        random_range(0.95, 1.05) if g in Ghydro else                     # Hydro: $1 ±5% per MW per Stop
        random_range(23.75, 26.25) if gen_types[g] == 'coal' else        # Coal: $25 ±5% per MW per Stop
        random_range(9.5, 10.5)                                         # CCGT: $10 ±5% per MW per Stop
        for g in G
    }

    # Define Scenario Probabilities (Assuming Equal Probability for Each Scenario)
    p["Pi"] = {s: 1 / len(S) for s in S}

    # Define Power Output Limits (Pmax and Pmin) for Each Generator
    p["Pmax"] = {}
    p["Pmin"] = {}
    for g in G:
        if g in Gsolar:
            sgen_idx = g - Gsolar[0]
            p["Pmax"][g] = solar_sgens.iloc[sgen_idx]['max_p_mw']
            p["Pmin"][g] = solar_sgens.iloc[sgen_idx]['min_p_mw']
        elif g in Gwind:
            sgen_idx = g - Gwind[0]
            p["Pmax"][g] = wind_sgens.iloc[sgen_idx]['max_p_mw']
            p["Pmin"][g] = wind_sgens.iloc[sgen_idx]['min_p_mw']
        elif g in Gbatt:
            storage_idx = g - Gbatt[0]
            p["Pmax"][g] = battery_storage.iloc[storage_idx]['max_p_mw']
            p["Pmin"][g] = battery_storage.iloc[storage_idx]['min_p_mw']
        elif g in Ghydro:
            gen_idx = g - Ghydro[0]
            p["Pmax"][g] = hydro_gens.iloc[gen_idx]['max_p_mw']
            p["Pmin"][g] = hydro_gens.iloc[gen_idx]['min_p_mw']
        elif g in Gtherm:
            gen_idx = g - Gtherm[0]
            p["Pmax"][g] = thermal_gens.iloc[gen_idx]['max_p_mw']
            p["Pmin"][g] = thermal_gens.iloc[gen_idx]['min_p_mw']

    # Define Ramp-Up (RU) and Ramp-Down (RD) Rates for Each Generator
    p["RU"] = {
        g: p["Pmax"][g] if g in Gbatt else
        p["Pmax"][g] if g in Grenew else
        p["Pmax"][g] if g in Ghydro else
        p["Pmax"][g] * 1.0 if gen_types[g] == 'coal' else              # Coal: 100% per hour
        p["Pmax"][g] * 2.85                                         # CCGT: 285% per hour
        for g in G
    }
    p["RD"] = p["RU"].copy()  # Ramp-Down rates are identical to Ramp-Up rates

    # Define Battery Parameters if Battery Storage Units Exist
    if len(Gbatt) > 0:
        p["Pchg"] = {g: p["Pmax"][g] for g in Gbatt}                    # Maximum charging power equals Pmax
        p["Pdchg"] = {g: p["Pmax"][g] for g in Gbatt}                   # Maximum discharging power equals Pmax
        p["Hchg"] = {g: random_range(0.95, 1.0) for g in Gbatt}        # Charging efficiency: 97.5% ±5%
        p["Hdchg"] = {g: random_range(0.95, 1.0) for g in Gbatt}       # Discharging efficiency: 97.5% ±5%
        p["SoCmin"] = {g: random_range(0.095, 0.105) for g in Gbatt}  # Minimum SoC: 10% ±5%
        p["SoCmax"] = {g: random_range(0.855, 0.945) for g in Gbatt}  # Maximum SoC: 90% ±5%
        p["Ecap"] = {g: p["Pmax"][g] * 4 for g in Gbatt}              # Energy capacity: 4-hour duration
        p["DODmax"] = {g: random_range(0.76, 0.84) for g in Gbatt}    # Depth of Discharge Max: 80% ±5%

    # Define Solar and Wind Parameters if Renewable Generators Exist
    if len(Grenew) > 0:
        # Solar Capacity Factor (CF)
        p["Xs"] = {
            (o, t): random_range(0.1425, 0.1575)  # Solar CF: 15% ±5%
            for o in O
            for t in T
        }
        # Maximum Available Solar Power based on Capacity Factor
        p["PXsmax"] = {
            (g, t, o): p["Xs"][o, t] * p["Pmax"][g]
            for g in Gsolar
            for t in T
            for o in O
        }
        # Wind Distribution Factor (Gam)
        p["Gam"] = {g: random_range(0.3325, 0.3675) for g in Gwind}  # Wind CF: 35% ±5%

    # Define Hydro Parameters if Hydro Generators Exist
    if len(Ghydro) > 0:
        # Efficiency Parameters for Hydro Generators
        p["H"] = {g: (9.81 * 1000 * 0.9) / 1e6 for g in Ghydro}  # Efficiency calculation
        p["Smax"] = {g: random_range(276.0, 304.5) for g in Ghydro}  # Maximum water spillage
        p["Hbase"] = {g: 110 for g in Ghydro}                        # Base head
        p["Emin"] = {g: 180 for g in Ghydro}                         # Minimum reservoir level
        p["Emax"] = {g: 220 for g in Ghydro}                         # Maximum reservoir level
        p["Ebase"] = {g: 190 for g in Ghydro}                        # Base reservoir level
        p["A"] = {g: 0.02 for g in Ghydro}                           # Coefficient for reservoir level calculation
        p["B"] = {g: 0.009 for g in Ghydro}                          # Coefficient for water discharge impact
        p["Qmin"] = {g: 15 for g in Ghydro}                          # Minimum water discharge
        p["Qmax"] = {g: 200 for g in Ghydro}                         # Maximum water discharge
        p["Inflow"] = {(g, t, s): 120 for g in Ghydro for t in T for s in S}  # Water inflow for hydro generators

    # Initialize Initial and Final Reservoir Levels for Hydro Generators
    p["Einit"] = {g: random_range(200, 220) for g in Ghydro}  # Initial reservoir levels
    p["Efinal"] = {g: p["Einit"][g] for g in Ghydro}          # Final reservoir levels (can be customized)

    # Define Demand Curve based on Time of Day
    p["Xdemand"] = {
        (t, d): random_range(0.8, 1.2) * net.load.at[d - 1, 'p_mw']
        for t in T
        for d in D
    }

    # Calculate Total Load in the Network
    total_load = net.load['p_mw'].sum()


    def demand_curve(t, total_load):
        """
        Generates a realistic electricity demand curve for a 24-hour period with hourly timesteps.

        Parameters:
            t (int): Hour of the day (0-23)
            total_load (float): Total system load capacity

        Returns:
            float: Calculated demand for hour t
        """
        # Base load varies by system size
        if total_load > 5000:  # Large systems (like 118 bus)
            base_load_factor = 0.4  # 40% of total load
            volatility = 0.3  # Less volatile
        elif total_load > 1000:  # Medium systems (like 30 bus)
            base_load_factor = 0.35  # 35% of total load
            volatility = 0.4  # Medium volatility
        else:  # Small systems (like 6 bus)
            base_load_factor = 0.3  # 30% of total load
            volatility = 0.5  # More volatile

        base_load = total_load * base_load_factor

        # Scale peak amplitudes based on system size
        peak_scale = volatility

        # Morning peak parameters (around 9 AM)
        morning_peak = gaussian_peak(t, mu=9, sigma=1.5, amplitude=0.4 * peak_scale)

        # Evening peak parameters (around 7 PM = 19h)
        evening_peak = gaussian_peak(t, mu=19, sigma=2.0, amplitude=0.5 * peak_scale)

        # Midday plateau (between peaks)
        midday = gaussian_peak(t, mu=14, sigma=4.0, amplitude=0.3 * peak_scale)

        # Night valley (early morning hours)
        night_valley = gaussian_valley(t, mu=4, sigma=2.5, amplitude=0.3 * peak_scale)

        # Combine all components
        daily_pattern = 1.0 + morning_peak + evening_peak + midday - night_valley

        # Add small random variations (scaled by system size)
        noise_scale = 0.02 if total_load <= 1000 else 0.01  # Smaller systems have more noise
        noise = noise_scale * np.random.normal()

        final_demand = base_load * daily_pattern * (1 + noise)

        # Dynamic bounds based on system size
        min_load = base_load * (0.5 if total_load > 5000 else 0.4)  # Larger systems have higher minimum
        max_load = base_load * (1.8 if total_load > 5000 else 2.0)  # Larger systems have lower peaks

        return max(min_load, min(final_demand, max_load))

    def gaussian_peak(x, mu, sigma, amplitude):
        """Helper function to create a Gaussian peak."""
        return amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    def gaussian_valley(x, mu, sigma, amplitude):
        """Helper function to create a Gaussian valley."""
        return amplitude * (1 - np.exp(-0.5 * ((x - mu) / sigma) ** 2))

    # Define Demand at Each Time Period
    p["Dd"] = {t: demand_curve(t, total_load) for t in T}

    # Define Reserve Requirements based on Demand and Renewable Capacity
    def reserve_requirement(t):
        """
        Calculates the reserve requirement for a given time period.

        Parameters:
            t (int): Time period.

        Returns:
            float: Reserve requirement for time period t.
        """
        base_reserve = 0.05 * p["Dd"][t]                  # 5% of demand as base reserve
        renewable_capacity = sum(p["Pmax"][g] for g in Grenew)
        additional_reserve = 0.105 * renewable_capacity   # 10% ±5% of renewable capacity
        return base_reserve + additional_reserve

    # Define Reserve Up (Rup) and Reserve Down (Rdn) for Each Time Period
    p["Rup"] = {t: reserve_requirement(t) for t in T}
    p["Rdn"] = {t: reserve_requirement(t) for t in T}

    # Define Maximum Power Flow (Fmax) for Each Transmission Line
    p["Fmax"] = {l: 250 for l in L}  # Example: 250 MW capacity for each line

    # Define Minimum Up Time (UT) for Thermal Generators
    p["UT"] = {
        g: random_range(9.5, 10.5) if gen_types[g] == 'coal' else   # Coal: 10 ±5% hours
        random_range(4.75, 5.25)                                  # CCGT: 5 ±5% hours
        for g in Gtherm
    }
    p["DT"] = p["UT"].copy()  # Minimum Down Time is identical to Minimum Up Time

    # Define Start-Up (SU) and Shut-Down (SD) Times for Thermal Generators
    p["SU"] = {
        g: random_range(4.75, 5.25) if gen_types[g] == 'coal' else  # Coal: 5 ±5% hours
        random_range(0.95, 1.05)                                  # CCGT: 1 ±5% hours
        for g in Gtherm
    }
    p["SD"] = p["SU"].copy()  # Shut-Down times are identical to Start-Up times

    # Define Generator-to-Node Incidence Matrix (Lg)
    p["Lg"] = {}
    for g in G:
        if g in Gsolar:
            sgen_idx = g - Gsolar[0]
            bus = solar_sgens.iloc[sgen_idx]['bus'] + 1  # 1-based indexing
        elif g in Gwind:
            sgen_idx = g - Gwind[0]
            bus = wind_sgens.iloc[sgen_idx]['bus'] + 1  # 1-based indexing
        elif g in Gbatt:
            storage_idx = g - Gbatt[0]
            bus = battery_storage.iloc[storage_idx]['bus'] + 1  # 1-based indexing
        elif g in Ghydro:
            gen_idx = g - Ghydro[0]
            bus = hydro_gens.iloc[gen_idx]['bus'] + 1  # 1-based indexing
        elif g in Gtherm:
            gen_idx = g - Gtherm[0]
            bus = thermal_gens.iloc[gen_idx]['bus'] + 1  # 1-based indexing
        else:
            raise ValueError(f"Unknown generator type for index: {g}")

        # Assign generator to its corresponding bus
        for n in N:
            p["Lg"][(g, n)] = 1 if n == bus else 0

    # Define Line-to-Node Incidence Matrix (Ll) (update indexing)
    p["Ll"] = {}
    for l in L:
        from_bus = net.line.at[l - 1, 'from_bus'] + 1  # 1-based indexing
        to_bus = net.line.at[l - 1, 'to_bus'] + 1      # 1-based indexing
        for n in N:
            if n == from_bus:
                p["Ll"][(l, n)] = 1
            elif n == to_bus:
                p["Ll"][(l, n)] = -1
            else:
                p["Ll"][(l, n)] = 0

    # Define Demand-to-Node Incidence Matrix (Ld)
    p["Ld"] = {}
    for d in D:
        bus = net.load.at[d - 1, 'bus'] + 1  # 1-based indexing
        for n in N:
            p["Ld"][(d, n)] = 1 if n == bus else 0

    # Define Load Distribution Factor (Dl)
    p["Dl"] = {d: 1 / num_demands for d in D} if num_demands > 0 else {}

    # Define Time Step Duration (Dt)
    p["Dt"] = {None: 1}  # Assuming each time step represents 1 hour

    # Define Transmission Line Parameters
    p["line_from"] = {l: net.line.at[l - 1, 'from_bus'] + 1 for l in L}  # From bus (1-based indexing)
    p["line_to"] = {l: net.line.at[l - 1, 'to_bus'] + 1 for l in L}      # To bus (1-based indexing)
    p["X"] = {l: net.line.at[l - 1, 'x_ohm_per_km'] * net.line.at[l - 1, 'length_km'] for l in L}  # Reactance in Ohms

    # Define Base Power (S_base) and Base Voltage (V_base) for Per-Unit System
    S_base = 100  # MVA
    V_base = net.bus['vn_kv'].mean()  # Average voltage base in kV
    Z_base = (V_base ** 2) / S_base  # Ohms

    # Convert Reactance from Ohms to Per-Unit
    p["X_pu"] = {l: p["X"][l] / Z_base for l in L}

    # Define Wind and Battery Uncertainty Parameters
    p["Xw"] = {
        (t, o): 100 * len(Gwind)
        for t in T
        for o in O
    }
    p["Xd_uncert"] = {
        (t, o): 100 * len(Gbatt)
        for t in T
        for o in O
    }

    # Extract Slack Bus ID from the Network
    slack_ext_grid = net.ext_grid[net.ext_grid.type == 'slack']
    if slack_ext_grid.empty:
        raise ValueError("No slack bus found in the network.")
    elif len(slack_ext_grid) > 1:
        raise ValueError("Multiple slack buses found in the network.")
    else:
        slack_bus = slack_ext_grid.at[slack_ext_grid.index[0], 'bus'] + 1  # 1-based indexing
        p["slack_bus"] = slack_bus

    # Serialize Parameter Data for the Optimization Model
    data = pickle.dumps({None: p})
    with open("UCdata.p", "wb") as f:
        pickle.dump(data, f)

    return data


def random_range(min_val, max_val):
    """
    Generates a random float within a specified range.

    Parameters:
        min_val (float): Minimum value of the range.
        max_val (float): Maximum value of the range.

    Returns:
        float: Randomly generated value within [min_val, max_val].
    """
    return min_val + random.random() * (max_val - min_val)


def add_gens_to_case(net, num_solar, num_wind, num_batt, num_hydro, num_thermal):
    """
    Adds specified numbers of different generator types to a pandapower network in a predefined order.

    Parameters:
        net (pandapower.Network): The pandapower network object to modify.
        num_solar (int): Number of solar generators to add.
        num_wind (int): Number of wind generators to add.
        num_batt (int): Number of battery storage units to add.
        num_hydro (int): Number of hydro generators to add.
        num_thermal (int): Number of thermal generators to add.

    Returns:
        pandapower.Network: The updated network with added generators.
    """
    # Retrieve list of existing buses in the network
    buses = net.bus.index.tolist()

    # Add dummy loads to ensure network connectivity and avoid isolated buses
    net = add_dummy_loads(net)

    # Ensure there is at least one slack bus in the network
    if 'type' not in net.ext_grid.columns or 'slack' not in net.ext_grid['type'].values:
        if not net.ext_grid.empty:
            # If ext_grid exists but lacks type, assign 'slack' to the first entry
            net.ext_grid.loc[net.ext_grid.index[0], 'type'] = 'slack'
        else:
            # If no ext_grid exists, create one and assign it as 'slack'
            slack_bus = random.choice(buses)
            pp.create_ext_grid(net, slack_bus, vm_pu=1.0, name="Slack")
            net.ext_grid.loc[net.ext_grid.index[-1], 'type'] = 'slack'

    # Assign 'Thermal' type to existing generators without a specified type
    if 'type' not in net.gen.columns:
        net.gen['type'] = 'Thermal'
    else:
        net.gen.loc[net.gen['type'].isnull(), 'type'] = 'Thermal'

    # Helper function to add a generator of a specified type to the network
    def add_generator(gen_type):
        """
        Adds a generator of a specific type to a randomly selected bus in the network.

        Parameters:
            gen_type (str): Type of generator to add ('Solar', 'Wind', 'Battery', 'Hydro', 'Thermal').

        Raises:
            ValueError: If an unknown generator type is specified.
        """
        # Select a random bus from the list of buses
        bus = random.choice(buses)
        unique_id = f"{gen_type}_{len(net.sgen) + len(net.gen) + len(net.storage)}"

        if gen_type == "Solar":
            # Add a Solar PV generator
            pp.create_sgen(net, bus, min_p_mw=0, max_p_mw=30, p_mw=30, q_mvar=0,
                          name=unique_id, type="PV")
        elif gen_type == "Wind":
            # Add a Wind Power generator
            pp.create_sgen(net, bus, min_p_mw=0, max_p_mw=50, p_mw=50, q_mvar=0,
                          name=unique_id, type="WP")
        elif gen_type == "Battery":
            # Add a Battery Storage unit
            pp.create_storage(net, bus, min_e_mwh=0, max_e_mwh=20,
                             min_p_mw=-80, max_p_mw=80, p_mw=0, q_mvar=0,
                             name=unique_id, type="BT")
        elif gen_type == "Hydro":
            # Add a Hydro generator
            gen_idx = pp.create_gen(net, bus, min_p_mw=10, max_p_mw=100,
                                    p_mw=50, vm_pu=1.0, name=unique_id)
            net.gen.at[gen_idx, "type"] = "Hydro"
        elif gen_type == "Thermal":
            # Add a Thermal generator
            gen_idx = pp.create_gen(net, bus, min_p_mw=20, max_p_mw=200,
                                    p_mw=100, vm_pu=1.0, name=unique_id)
            net.gen.at[gen_idx, "type"] = "Thermal"
        else:
            raise ValueError(f"Unknown generator type: {gen_type}")

    # Add Thermal Generators
    for _ in range(num_thermal):
        add_generator("Thermal")

    # Add Hydro Generators
    for _ in range(num_hydro):
        add_generator("Hydro")

    # Add Solar Generators
    for _ in range(num_solar):
        add_generator("Solar")

    # Add Wind Generators
    for _ in range(num_wind):
        add_generator("Wind")

    # Add Battery Storage Units
    for _ in range(num_batt):
        add_generator("Battery")

    return net


def add_dummy_loads(net, dummy_load_mw=1):
    """
    Adds dummy loads to isolated buses or buses without existing loads to ensure network connectivity.

    Parameters:
        net (pandapower.Network): The pandapower network object to modify.
        dummy_load_mw (float): Power of each dummy load in MW (default is 1).

    Returns:
        pandapower.Network: The updated network with dummy loads added.
    """
    # Create an undirected graph of the network using NetworkX
    graph = nx.Graph()
    for _, line in net.line.iterrows():
        graph.add_edge(line['from_bus'], line['to_bus'])

    # Identify all connected components in the network graph
    connected_components = list(nx.connected_components(graph))

    # Identify buses that already have loads
    buses_with_loads = set(net.load['bus'].values)
    all_buses = set(net.bus.index)
    buses_without_loads = all_buses - buses_with_loads

    # Initialize counter for dummy loads
    dummy_load_count = 0

    # Add dummy loads to buses without loads or to isolated buses
    for bus in buses_without_loads:
        # Check if the bus is isolated (only connected to itself)
        if any(len(component) == 1 and bus in component for component in connected_components):
            pp.create_load(net, bus=bus, p_mw=dummy_load_mw,
                          name=f"Dummy Load {dummy_load_count}")
            dummy_load_count += 1
        # Add dummy load to buses in larger connected components but without existing loads
        elif bus not in buses_with_loads:
            pp.create_load(net, bus=bus, p_mw=dummy_load_mw,
                          name=f"Dummy Load {dummy_load_count}")
            dummy_load_count += 1

    print(f"Added {dummy_load_count} dummy loads to the network.")
    return net
