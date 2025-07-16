# generate_instance_configs.py
import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Define the number of instances
num_instances = 50

# Initialize a list to store configurations
configs = []

# Define bus systems and their instance allocations
bus_systems = [
    ("case4gs", 5),
    ("case5", 5),
    ("case6ww", 5),
    ("case9", 5),
    ("case14", 5),
    ("case24_ieee_rts", 5),
]

# Starting instance ID
instance_id = 1

# Generate configurations for each bus system
for bus_system, count in bus_systems:
    for _ in range(count):
        # Define generator count ranges based on specific bus system
        if bus_system == "case4gs":
            thermal_range = (2, 3)
            hydro_range = (0, 1)
            solar_range = (0, 2)
            wind_range = (0, 2)
            battery_range = (0, 1)
        elif bus_system == "case5":
            thermal_range = (2, 3)
            hydro_range = (0, 1)
            solar_range = (0, 2)
            wind_range = (0, 2)
            battery_range = (0, 1)
        elif bus_system == "case6ww":
            thermal_range = (2, 3)
            hydro_range = (0, 1)
            solar_range = (0, 2)
            wind_range = (0, 2)
            battery_range = (0, 1)
        elif bus_system == "case9":
            thermal_range = (3, 4)
            hydro_range = (0, 1)
            solar_range = (0, 2)
            wind_range = (0, 2)
            battery_range = (0, 1)
        elif bus_system == "case14":
            thermal_range = (5, 6)
            hydro_range = (0, 2)
            solar_range = (0, 2)
            wind_range = (0, 2)
            battery_range = (0, 1)
        elif bus_system == "case24_ieee_rts":
            thermal_range = (8, 10)
            hydro_range = (2, 3)
            solar_range = (2, 8)
            wind_range = (2, 6)
            battery_range = (1, 4)
        elif bus_system == "case30":
            thermal_range = (6, 8)
            hydro_range = (1, 2)
            solar_range = (2, 8)
            wind_range = (2, 6)
            battery_range = (1, 4)
        elif bus_system == "case33bw":
            thermal_range = (6, 8)
            hydro_range = (1, 2)
            solar_range = (2, 8)
            wind_range = (2, 6)
            battery_range = (1, 4)
        elif bus_system == "case39":
            thermal_range = (10, 12)
            hydro_range = (2, 3)
            solar_range = (2, 8)
            wind_range = (2, 6)
            battery_range = (1, 4)
        elif bus_system == "case57":
            thermal_range = (12, 15)
            hydro_range = (2, 4)
            solar_range = (2, 8)
            wind_range = (2, 6)
            battery_range = (1, 4)
        elif bus_system == "case118":
            thermal_range = (25, 30)
            hydro_range = (4, 6)
            solar_range = (5, 15)
            wind_range = (4, 12)
            battery_range = (3, 8)
        elif bus_system == "case145":
            thermal_range = (30, 35)
            hydro_range = (5, 7)
            solar_range = (5, 15)
            wind_range = (4, 12)
            battery_range = (3, 8)
        elif bus_system == "illinois200":
            thermal_range = (40, 45)
            hydro_range = (6, 8)
            solar_range = (5, 15)
            wind_range = (4, 12)
            battery_range = (3, 8)
        elif bus_system == "case300":
            thermal_range = (50, 60)
            hydro_range = (8, 10)
            solar_range = (5, 15)
            wind_range = (4, 12)
            battery_range = (3, 8)
        elif bus_system == "case1354pegase":
            thermal_range = (220, 240)
            hydro_range = (110, 120)
            solar_range = (90, 100)
            wind_range = (90, 100)
            battery_range = (70, 80)
        elif bus_system == "case1888rte":
            thermal_range = (310, 330)
            hydro_range = (155, 165)
            solar_range = (125, 135)
            wind_range = (125, 135)
            battery_range = (95, 105)
        elif bus_system == "case2848rte":
            thermal_range = (470, 490)
            hydro_range = (235, 245)
            solar_range = (190, 200)
            wind_range = (190, 200)
            battery_range = (140, 150)
        elif bus_system == "case2869pegase":
            thermal_range = (475, 495)
            hydro_range = (235, 245)
            solar_range = (190, 200)
            wind_range = (190, 200)
            battery_range = (140, 150)
        elif bus_system == "case3120sp":
            thermal_range = (520, 540)
            hydro_range = (260, 270)
            solar_range = (210, 220)
            wind_range = (210, 220)
            battery_range = (155, 165)
        elif bus_system == "case6470rte":
            thermal_range = (1075, 1095)
            hydro_range = (535, 545)
            solar_range = (430, 440)
            wind_range = (430, 440)
            battery_range = (320, 330)

        configs.append(
            {
                "Instance ID": instance_id,
                "Bus System": bus_system,
                "Num Thermal": np.random.randint(*thermal_range),
                "Num Hydro": np.random.randint(*hydro_range),
                "Num Solar": np.random.randint(*solar_range),
                "Num Wind": np.random.randint(*wind_range),
                "Num Battery": np.random.randint(*battery_range),
                "Random Seed": instance_id + 10000,
            }
        )
        instance_id += 1

# Convert the list to a DataFrame
configs_df = pd.DataFrame(configs)


import os
import subprocess


# Read configurations


for idx, row in configs_df.iterrows():
    instance_id = int(row["Instance ID"])
    bus_system = row["Bus System"]
    num_thermal = int(row["Num Thermal"])
    num_hydro = int(row["Num Hydro"])
    num_solar = int(row["Num Solar"])
    num_wind = int(row["Num Wind"])
    num_battery = int(row["Num Battery"])
    random_seed = int(row["Random Seed"])

    print(f"Generating Instance {instance_id}: {bus_system}")

    # Set random seeds for reproducibility (if needed)
    os.environ["PYTHONHASHSEED"] = str(random_seed)

    # Construct command to run example.py
    command = [
        "python",
        "example.py",
        bus_system,
        str(num_solar),
        str(num_wind),
        str(num_hydro),
        str(num_battery),
        str(num_thermal),
    ]

    # Run example.py with the specified configuration
    subprocess.run(command)
