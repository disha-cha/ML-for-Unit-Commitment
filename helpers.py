"""Helper functions for using generated optimization models"""

import pickle
import random
import pandapower as pp
import networkx as nx
import numpy as np

def parsecase(net, num_solar=0, num_wind=0, num_batt=0, num_hydro=0, num_therm=0, time_periods=24, num_scenarios=1,
              num_nodes=0, num_lines=0, num_uncert=1, num_demands=0):
    """
    Parses the pandapower network and prepares the parameters for the optimization model.
    """
    p = {}

    # Initialize generator ID offset
    gen_offset = 1

    # Thermal Generators
    thermal_gens = net.gen[net.gen.type == "Thermal"]
    Gtherm = list(range(gen_offset, gen_offset + len(thermal_gens)))
    gen_offset += len(Gtherm)

    # Hydro Generators
    hydro_gens = net.gen[net.gen.type == "Hydro"]
    Ghydro = list(range(gen_offset, gen_offset + len(hydro_gens)))
    gen_offset += len(Ghydro)

    # Solar Generators
    solar_sgens = net.sgen[net.sgen.type == "PV"]
    Gsolar = list(range(gen_offset, gen_offset + len(solar_sgens)))
    gen_offset += len(Gsolar)

    # Wind Generators
    wind_sgens = net.sgen[net.sgen.type == "WP"]
    Gwind = list(range(gen_offset, gen_offset + len(wind_sgens)))
    gen_offset += len(Gwind)

    # Battery Storage Units
    battery_storage = net.storage[net.storage.type == "BT"]
    Gbatt = list(range(gen_offset, gen_offset + len(battery_storage)))

    # Renewable Generators (Solar + Wind)
    Grenew = Gsolar + Gwind

    # All Generators
    G = Gtherm + Ghydro + Gsolar + Gwind + Gbatt

    T = range(1, time_periods + 1)
    S = range(1, num_scenarios + 1)
    N = range(1, num_nodes + 1)
    L = range(1, num_lines + 1)
    O = range(1, num_uncert + 1)
    D = range(1, num_demands + 1)

    # Assign generator types to thermal generators
    therm_types = ['coal', 'ccgt']
    gen_types = {g: random.choice(therm_types) for g in Gtherm}

    # Fixed costs
    p["CapEx"] = {
        g: random_range(902.5, 997.5) if g in Gsolar else  # Solar PV: $950 ±5% per kW
        random_range(1425, 1575) if g in Gwind else        # Onshore Wind: $1500 ±5% per kW
        random_range(3800, 4200) if g in Ghydro else       # Hydro: $4000 ±5% per kW
        random_range(1235, 1365) if g in Gbatt else        # Battery Storage: $1300 ±5% per kW
        random_range(3800, 4200) if gen_types[g] == 'coal' else  # Coal: $4000 ±5% per kW
        random_range(950, 1050)  # For 'ccgt', CCGT: $1000 ±5% per kW
        for g in G
    }

    # Variable costs
    p["OpEx"] = {
        g: random_range(0, 1.05) if g in Gsolar else         # Solar PV: $0-$1 per MWh
        random_range(0, 1.05) if g in Gwind else             # Wind: $0-$1 per MWh
        random_range(1.9, 2.1) if g in Ghydro else           # Hydro: $2 ±5% per MWh
        random_range(7.6, 8.4) if g in Gbatt else            # Battery: $8 ±5% per MWh
        random_range(38, 42) if gen_types[g] == 'coal' else  # Coal: $40 ±5% per MWh
        random_range(28.5, 31.5)  # For 'ccgt', CCGT: $30 ±5% per MWh
        for g in G
    }

    # Start-up costs
    p["CSU"] = {
        g: 0 if g in Grenew or g in Gbatt else
        random_range(1.9, 2.1) if g in Ghydro else                       # Hydro: $2 ±5% per MW per Start
        random_range(95, 105) if gen_types[g] == 'coal' else             # Coal: $100 ±5% per MW per Start
        random_range(47.5, 52.5)  # For 'ccgt', CCGT: $50 ±5% per MW per Start
        for g in G
    }

    # Shut-down costs
    p["CSD"] = {
        g: 0 if g in Grenew or g in Gbatt else
        random_range(0.95, 1.05) if g in Ghydro else                     # Hydro: $1 ±5% per MW per Stop
        random_range(23.75, 26.25) if gen_types[g] == 'coal' else        # Coal: $25 ±5% per MW per Stop
        random_range(9.5, 10.5)  # For 'ccgt', CCGT: $10 ±5% per MW per Stop
        for g in G
    }

    # Scenario probabilities
    p["Pi"] = {s: 1 / len(S) for s in S}

    # Generator limits
    p["Pmax"] = {}
    p["Pmin"] = {}
    for g in G:
        if g in Gsolar or g in Gwind:
            sgen_idx = g - len(Gtherm) - len(Ghydro)  # Adjusted index for sgen
            p["Pmax"][g] = solar_sgens.at[sgen_idx - 1, 'max_p_mw'] if g in Gsolar else wind_sgens.at[
                sgen_idx - 1, 'max_p_mw']
            p["Pmin"][g] = solar_sgens.at[sgen_idx - 1, 'min_p_mw'] if g in Gsolar else wind_sgens.at[
                sgen_idx - 1, 'min_p_mw']
        elif g in Gbatt:
            storage_idx = g - len(Gtherm) - len(Ghydro) - len(Gsolar) - len(Gwind) - 1  # Adjusted index for storage
            p["Pmax"][g] = battery_storage.at[storage_idx, 'max_p_mw']
            p["Pmin"][g] = battery_storage.at[storage_idx, 'min_p_mw']
        elif g in Ghydro or g in Gtherm:
            gen_idx = g - 1  # Adjusted for 1-based indexing
            p["Pmax"][g] = net.gen.at[gen_idx, 'max_p_mw']
            p["Pmin"][g] = net.gen.at[gen_idx, 'min_p_mw']

    # Ramp up and down rates
    p["RU"] = {
        g: p["Pmax"][g] if g in Gbatt else
        p["Pmax"][g] if g in Grenew else
        p["Pmax"][g] if g in Ghydro else
        p["Pmax"][g] * 1.0 if gen_types[g] == 'coal' else   # Coal: 100% per hour
        p["Pmax"][g] * 2.85  # For 'ccgt', CCGT: 285% per hour
        for g in G
    }
    p["RD"] = p["RU"].copy()

    # Battery parameters
    if len(Gbatt) > 0:
        p["Pchg"] = {g: p["Pmax"][g] for g in Gbatt}  # Max charge rate equals Pmax
        p["Pdchg"] = {g: p["Pmax"][g] for g in Gbatt}  # Max discharge rate equals Pmax
        p["Hchg"] = {g: random_range(0.925, 1.025) for g in Gbatt}     # Charge efficiency 97.5% ±5%
        p["Hdchg"] = {g: random_range(0.925, 1.025) for g in Gbatt}    # Discharge efficiency 97.5% ±5%
        p["SoCmin"] = {g: random_range(0.095, 0.105) for g in Gbatt}   # Minimum SoC 10% ±5%
        p["SoCmax"] = {g: random_range(0.855, 0.945) for g in Gbatt}   # Maximum SoC 90% ±5%
        p["Ecap"] = {g: p["Pmax"][g] * 4 for g in Gbatt}  # Assuming 4-hour duration
        p["DODmax"] = {g: random_range(0.76, 0.84) for g in Gbatt}     # DODmax 80% ±5%

    # Solar and wind parameters
    if len(Grenew) > 0:
        p["Xs"] = {
            (o, t): random_range(0.1425, 0.1575)  # Solar CF: 15% ±5%
            for o in O
            for t in T
        }
        p["PXsmax"] = {
            (g, t, o): p["Xs"][o, t] * p["Pmax"][g]
            for g in Gsolar
            for t in T
            for o in O
        }
        p["Xw"] = {
            (t, o): random_range(0.3325, 0.3675)  # Wind CF: 35% ±5%
            for t in T
            for o in O
        }
        p["Gam"] = {g: 1.0 for g in Gwind}  # Assuming full availability scaled by CF

    # Hydro parameters
    if len(Ghydro) > 0:
        p["H"] = {g: (9.81 * 1000 * 0.9) / 1e6 for g in Ghydro}
        p["Smax"] = {g: random_range(276.0, 304.5) for g in Ghydro}
        p["Hbase"] = {g: 110 for g in Ghydro}
        p["Emin"] = {g: 180 for g in Ghydro}
        p["Emax"] = {g: 220 for g in Ghydro}
        p["Ebase"] = {g: 190 for g in Ghydro}
        p["A"] = {g: 0.02 for g in Ghydro}
        p["B"] = {g: 0.009 for g in Ghydro}
        p["Qmin"] = {g: 15 for g in Ghydro}
        p["Qmax"] = {g: 200 for g in Ghydro}
        p["Inflow"] = {(g, t, s): 120 for g in Ghydro for t in T for s in S}

        # Initialize Einit and Efinal for Hydro Generators
        p["Einit"] = {g: random_range(200, 220) for g in Ghydro}  # Initial reservoir levels
        p["Efinal"] = {g: p["Einit"][g] for g in Ghydro}  # Final reservoir levels

    # Demand curve
    total_load = net.load['p_mw'].sum()

    def demand_curve(t):
        base_load = total_load
        peak_factor = 1.1  # 10% above average
        off_peak_factor = 0.9  # 10% below average
        time_of_day = (t - 1) % 24
        variation = np.sin(np.pi * time_of_day / 12)  # Variation over the day

        if 6 <= time_of_day <= 18:  # Peak hours
            return base_load * peak_factor * (1 + 0.05 * variation)
        else:  # Off-peak hours
            return base_load * off_peak_factor * (1 + 0.05 * variation)

    p["Dd"] = {t: demand_curve(t) for t in T}

    # Reserve requirement
    def reserve_requirement(t):
        base_reserve = 0.05 * p["Dd"][t]  # 5% of demand as base reserve
        renewable_capacity = sum(p["Pmax"][g] for g in Grenew)
        additional_reserve = 0.10 * renewable_capacity  # 10% of renewable capacity
        return base_reserve + additional_reserve

    p["Rup"] = {t: reserve_requirement(t) for t in T}
    p["Rdn"] = {t: reserve_requirement(t) for t in T}

    # Transmission line parameters
    p["Fmax"] = {l: 250 for l in L}

    # Minimum up and down times
    p["UT"] = {
        g: random_range(9.5, 10.5) if gen_types[g] == 'coal' else  # Coal: 10 ±5% hours
        random_range(4.75, 5.25)  # For 'ccgt', CCGT: 5 ±5% hours
        for g in Gtherm
    }
    p["DT"] = p["UT"].copy()

    # Start-up and Shut-down times
    p["SU"] = {
        g: random_range(4.75, 5.25) if gen_types[g] == 'coal' else  # Coal: 5 ±5% hours
        random_range(0.95, 1.05)  # For 'ccgt', CCGT: 1 ±5% hours
        for g in Gtherm
    }
    p["SD"] = p["SU"].copy()

    # Location mapping for generators
    p["Lg"] = {}
    for g in G:
        if g in Gsolar:
            sgen_idx = g - len(Gtherm) - len(Ghydro) - 1
            bus = solar_sgens.iloc[sgen_idx]['bus'] + 1
        elif g in Gwind:
            sgen_idx = g - len(Gtherm) - len(Ghydro) - len(Gsolar) - 1
            bus = wind_sgens.iloc[sgen_idx]['bus'] + 1
        elif g in Ghydro or g in Gtherm:
            gen_idx = g - 1
            bus = net.gen.iloc[gen_idx]['bus'] + 1
        elif g in Gbatt:
            storage_idx = g - len(Gtherm) - len(Ghydro) - len(Gsolar) - len(Gwind) - 1
            bus = battery_storage.iloc[storage_idx]['bus'] + 1
        else:
            raise ValueError(f"Unknown generator type for index: {g}")

        for n in N:
            p["Lg"][(g, n)] = 1 if n == bus else 0

    # Incidence matrix for lines
    p["Ll"] = {}
    for l in L:
        from_bus = net.line.at[l - 1, 'from_bus'] + 1
        to_bus = net.line.at[l - 1, 'to_bus'] + 1
        for n in N:
            if n == from_bus:
                p["Ll"][(l, n)] = 1
            elif n == to_bus:
                p["Ll"][(l, n)] = -1
            else:
                p["Ll"][(l, n)] = 0

    # Location mapping for demands
    p["Ld"] = {}
    for d in D:
        bus = net.load.at[d - 1, 'bus'] + 1
        for n in N:
            p["Ld"][(d, n)] = 1 if n == bus else 0

    p["Dl"] = {d: 1 / num_demands for d in D}
    p["Dt"] = {None: 1}

    p["line_from"] = {l: net.line.at[l - 1, 'from_bus'] + 1 for l in L}
    p["line_to"] = {l: net.line.at[l - 1, 'to_bus'] + 1 for l in L}
    p["X"] = {l: net.line.at[l - 1, 'x_ohm_per_km'] * net.line.at[l - 1, 'length_km'] for l in L}

    # Voltage base assumption
    S_base = 100  # MVA
    V_bases = net.bus['vn_kv'].unique()
    if len(V_bases) == 1:
        V_base = V_bases[0]
    else:
        raise ValueError("Multiple voltage bases found in the network.")
    Z_base = (V_base ** 2) / S_base  # Ohms
    # Convert X[l] from Ohms to per unit
    p["X_pu"] = {l: p["X"][l] / Z_base for l in L}

    # Extract Slack Bus ID
    if net.ext_grid.empty:
        raise ValueError("No external grid (slack bus) found in the network.")
    slack_bus = net.ext_grid.iloc[0]['bus'] + 1
    p["slack_bus"] = slack_bus

    # Serialize data
    data = pickle.dumps({None: p})
    with open("UCdata.p", "wb") as f:
        pickle.dump(data, f)

    return data

def random_range(min_val, max_val):
    """
    Returns a random float between min_val and max_val.
    """
    return min_val + random.random() * (max_val - min_val)

def add_gens_to_case(net, num_solar, num_wind, num_batt, num_hydro, num_thermal):
    """
    Adds specified number of generators of various types to a pandapower network in a specified order.

    Parameters:
    - net: pandapower network object
    - num_solar: Number of solar generators to add
    - num_wind: Number of wind generators to add
    - num_batt: Number of battery storage units to add
    - num_hydro: Number of hydro generators to add
    - num_thermal: Number of thermal generators to add

    Returns:
    - Modified pandapower network object with generators added in specific order.
    """
    # Get list of buses
    buses = net.bus.index.tolist()
    net = add_dummy_loads(net)

    # Ensure we have a slack bus
    if 'type' not in net.ext_grid.columns or 'slack' not in net.ext_grid['type'].values:
        if not net.ext_grid.empty:
            net.ext_grid.loc[net.ext_grid.index[0], 'type'] = 'slack'
        else:
            slack_bus = random.choice(buses)
            pp.create_ext_grid(net, slack_bus, vm_pu=1.0, name="Slack")
            net.ext_grid.loc[net.ext_grid.index[-1], 'type'] = 'slack'

    # Assign 'Thermal' type to existing generators without a type
    if 'type' not in net.gen.columns:
        net.gen['type'] = 'Thermal'
    else:
        net.gen.loc[net.gen['type'].isnull(), 'type'] = 'Thermal'

    # Function to add a generator
    def add_generator(gen_type):
        bus = random.choice(buses)
        unique_id = f"{gen_type}_{len(net.sgen) + len(net.gen) + len(net.storage)}"

        if gen_type == "Solar":
            pp.create_sgen(net, bus, min_p_mw=0, max_p_mw=30, p_mw=30, q_mvar=0, name=unique_id, type="PV")
        elif gen_type == "Wind":
            pp.create_sgen(net, bus, min_p_mw=0, max_p_mw=50, p_mw=50, q_mvar=0, name=unique_id, type="WP")
        elif gen_type == "Battery":
            pp.create_storage(net, bus, min_e_mwh=0, max_e_mwh=20, min_p_mw=-80, max_p_mw=80, p_mw=0, q_mvar=0,
                             name=unique_id, type="BT")
        elif gen_type == "Hydro":
            gen_idx = pp.create_gen(net, bus, min_p_mw=10, max_p_mw=100, p_mw=50, vm_pu=1.0, name=unique_id)
            net.gen.at[gen_idx, "type"] = "Hydro"
        elif gen_type == "Thermal":
            gen_idx = pp.create_gen(net, bus, min_p_mw=20, max_p_mw=200, p_mw=100, vm_pu=1.0, name=unique_id)
            net.gen.at[gen_idx, "type"] = "Thermal"

    # Add Thermal generators
    for _ in range(num_thermal):
        add_generator("Thermal")

    # Add Hydro generators
    for _ in range(num_hydro):
        add_generator("Hydro")

    # Add Solar generators
    for _ in range(num_solar):
        add_generator("Solar")

    # Add Wind generators
    for _ in range(num_wind):
        add_generator("Wind")

    # Add Battery generators
    for _ in range(num_batt):
        add_generator("Battery")

    return net

def add_dummy_loads(net, dummy_load_mw=1):
    """
    Add dummy loads to isolated nodes or nodes without loads in the network.

    Parameters:
    net (pandapower.Network): The pandapower network
    dummy_load_mw (float): The power of the dummy load in MW

    Returns:
    pandapower.Network: The updated network with dummy loads added
    """
    # Create a graph of the network
    graph = nx.Graph()
    for _, line in net.line.iterrows():
        graph.add_edge(line['from_bus'], line['to_bus'])

    # Find all connected components
    connected_components = list(nx.connected_components(graph))

    # Find buses with no loads
    buses_with_loads = set(net.load['bus'].values)
    all_buses = set(net.bus.index)
    buses_without_loads = all_buses - buses_with_loads

    # Add dummy loads to isolated buses and buses without loads
    dummy_load_count = 0
    for bus in buses_without_loads:
        # Check if the bus is isolated (in a component by itself)
        if any(len(component) == 1 and bus in component for component in connected_components):
            pp.create_load(net, bus=bus, p_mw=dummy_load_mw, name=f"Dummy Load {dummy_load_count}")
            dummy_load_count += 1
        # Or if it's in a larger component but has no load
        elif bus not in buses_with_loads:
            pp.create_load(net, bus=bus, p_mw=dummy_load_mw, name=f"Dummy Load {dummy_load_count}")
            dummy_load_count += 1

    print(f"Added {dummy_load_count} dummy loads to the network.")
    return net
