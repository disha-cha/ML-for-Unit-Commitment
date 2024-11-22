# generate_instance_configs.py
import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Define the number of instances
num_instances = 1000

# Initialize a list to store configurations
configs = []

# Define bus systems and their instance allocations
bus_systems = [
    ('case4gs', 20),
    ('case5', 20),
    ('case6ww', 20),
    ('case9', 30),
    ('case14', 40),
    ('case24_ieee_rts', 50),
    ('case30', 60),
    ('case33bw', 60),
    ('case39', 80),
    ('case57', 90),
    ('case89pegase', 100),
    ('case118', 120),
    ('case145', 120),
    ('illinois200', 120),
    ('case300', 120),
]

# Starting instance ID
instance_id = 1001

# Generate configurations for each bus system
for bus_system, count in bus_systems:
    for _ in range(count):
        # Define generator count ranges based on bus system size
        if bus_system in ['case4gs', 'case5', 'case6ww', 'case9', 'case14']:
            thermal_range = (1, 4)
            hydro_range = (0, 2)
            solar_range = (1, 3)
            wind_range = (1, 3)
            battery_range = (0, 2)
        elif bus_system in ['case24_ieee_rts', 'case30', 'case33bw', 'case39', 'case57']:
            thermal_range = (4, 10)
            hydro_range = (2, 5)
            solar_range = (3, 7)
            wind_range = (3, 7)
            battery_range = (2, 5)
        else:  # Larger systems
            thermal_range = (10, 30)
            hydro_range = (5, 15)
            solar_range = (8, 20)
            wind_range = (8, 20)
            battery_range = (5, 15)

        configs.append({
            'Instance ID': instance_id,
            'Bus System': bus_system,
            'Num Thermal': np.random.randint(*thermal_range),
            'Num Hydro': np.random.randint(*hydro_range),
            'Num Solar': np.random.randint(*solar_range),
            'Num Wind': np.random.randint(*wind_range),
            'Num Battery': np.random.randint(*battery_range),
            'Random Seed': instance_id + 1000
        })
        instance_id += 1

# Convert the list to a DataFrame
configs_df = pd.DataFrame(configs)



import os
import subprocess


# Read configurations


for idx, row in configs_df.iterrows():
    instance_id = int(row['Instance ID'])
    bus_system = row['Bus System']
    num_thermal = int(row['Num Thermal'])
    num_hydro = int(row['Num Hydro'])
    num_solar = int(row['Num Solar'])
    num_wind = int(row['Num Wind'])
    num_battery = int(row['Num Battery'])
    random_seed = int(row['Random Seed'])

    print(f"Generating Instance {instance_id}: {bus_system}")

    # Set random seeds for reproducibility (if needed)
    os.environ['PYTHONHASHSEED'] = str(random_seed)

    # Construct command to run example.py
    command = [
        'python', 'example.py', bus_system,
        str(num_solar), str(num_wind), str(num_hydro),
        str(num_battery), str(num_thermal)
    ]

    # Run example.py with the specified configuration
    subprocess.run(command)



