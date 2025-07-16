import os
import subprocess
import glob
from pyscipopt import Model
import pandas as pd
import numpy as np

# Create test_data directory if it doesn't exist
if not os.path.exists('test_data'):
    os.makedirs('test_data')

def generate_test_instances():
    """
    Generate test instances using the configs from test_branching.py
    """
    # Define bus systems and their instance allocations (from test_branching.py)
    bus_systems = [
        ("case4gs", 10),
        ("case5", 10),
        ("case6ww", 10),
        ("case9", 10),
        ("case14", 10),
    ]
    
    # Starting instance ID
    instance_id = 10000
    
    # Initialize a list to store configurations
    configs = []
    
    # Generate configurations for each bus system
    for bus_system, count in bus_systems:
        for _ in range(count):
            # Define generator count ranges based on specific bus system
            if bus_system == 'case4gs':
                thermal_range = (2, 3)
                hydro_range = (0, 1)
                solar_range = (0, 2)
                wind_range = (0, 2)
                battery_range = (0, 1)
            elif bus_system == 'case5':
                thermal_range = (2, 3)
                hydro_range = (0, 1)
                solar_range = (0, 2)
                wind_range = (0, 2)
                battery_range = (0, 1)
            elif bus_system == 'case6ww':
                thermal_range = (2, 3)
                hydro_range = (0, 1)
                solar_range = (0, 2)
                wind_range = (0, 2)
                battery_range = (0, 1)
            elif bus_system == 'case9':
                thermal_range = (3, 4)
                hydro_range = (0, 1)
                solar_range = (0, 2)
                wind_range = (0, 2)
                battery_range = (0, 1)
            elif bus_system == 'case14':
                thermal_range = (5, 6)
                hydro_range = (0, 2)
                solar_range = (0, 2)
                wind_range = (0, 2)
                battery_range = (0, 1)
            elif bus_system == 'case24_ieee_rts':
                thermal_range = (8, 10)
                hydro_range = (2, 3)
                solar_range = (2, 8)
                wind_range = (2, 6)
                battery_range = (1, 4)
            else:
                # Default ranges for other cases
                thermal_range = (2, 4)
                hydro_range = (0, 2)
                solar_range = (0, 3)
                wind_range = (0, 3)
                battery_range = (0, 2)

            configs.append({
                "Instance ID": instance_id,
                "Bus System": bus_system,
                "Num Thermal": np.random.randint(*thermal_range),
                "Num Hydro": np.random.randint(*hydro_range),
                "Num Solar": np.random.randint(*solar_range),
                "Num Wind": np.random.randint(*wind_range),
                "Num Battery": np.random.randint(*battery_range),
                "Random Seed": instance_id + 10000,
            })
            instance_id += 1

    # Convert to DataFrame
    configs_df = pd.DataFrame(configs)
    
    print(f"Generating {len(configs_df)} test instances...")
    
    # Generate instances
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

        # Set random seeds for reproducibility
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
        
        # Set environment variable to use test_data directory
        env = os.environ.copy()
        env['OUTPUT_DIR'] = 'test_data'

        # Run example.py with the specified configuration
        subprocess.run(command, env=env)
    
    return configs_df

def solve_mps_with_scip(mps_file_path, timeout_seconds=60):
    """
    Solves an MPS file with SCIP and returns the number of nodes used.
    
    Parameters:
        mps_file_path (str): Path to the MPS file
        timeout_seconds (int): Maximum time to spend solving (default: 60 seconds)
        
    Returns:
        dict: Dictionary containing solver results including node count
    """
    try:
        # Create SCIP model
        model = Model("UC_Model")
        
        # Configure SCIP for faster solving and limited output
        model.hideOutput(True)  # Reduce output for faster processing
        model.setParam("limits/time", timeout_seconds)  # Set time limit
        model.setParam("limits/nodes", 1000)  # Limit nodes for testing
        model.setParam("display/verblevel", 0)  # Minimal verbosity
        
        # Read the MPS file
        model.readProblem(mps_file_path)
        
        # Solve the model
        model.optimize()
        
        # Get solver statistics
        num_nodes = model.getNNodes()
        obj_val = model.getObjVal() if model.getStatus() == "optimal" else None
        status = model.getStatus()
        
        return {
            'file': mps_file_path,
            'status': status,
            'num_nodes': num_nodes,
            'obj_val': obj_val
        }
        
    except Exception as e:
        return {
            'file': mps_file_path,
            'status': 'error',
            'num_nodes': -1,
            'obj_val': None,
            'error': str(e)
        }

def test_uc_instances():
    """
    Main function to test UC instances and find those with non-trivial branching.
    """
    # First, generate test instances if they don't exist
    test_data_dir = "test_data"
    mps_files = glob.glob(os.path.join(test_data_dir, "*.mps"))
    
    if not mps_files:
        print("No MPS files found in test_data directory. Generating test instances...")
        generate_test_instances()
        mps_files = glob.glob(os.path.join(test_data_dir, "*.mps"))
    
    if not mps_files:
        print("No MPS files found after generation.")
        return
    
    print(f"Found {len(mps_files)} MPS files to test.")
    print("=" * 80)
    
    results = []
    non_trivial_instances = []
    
    for i, mps_file in enumerate(mps_files, 1):
        print(f"Testing file {i}/{len(mps_files)}: {os.path.basename(mps_file)}")
        
        # Solve with SCIP
        result = solve_mps_with_scip(mps_file)
        results.append(result)
        
        # Check if this instance used non-zero nodes (non-trivial branching)
        if result['num_nodes'] > 1:
            non_trivial_instances.append(result)
            print(f"  ✓ NON-TRIVIAL: {result['num_nodes']} nodes used")
        elif result['num_nodes'] == 1:
            print(f"  - Trivial: {result['num_nodes']} node (solved without branching)")
        elif result['num_nodes'] == 0:
            print(f"  - Trivial: {result['num_nodes']} nodes (presolved)")
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_files = len(results)
    non_trivial_count = len(non_trivial_instances)
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Total files tested: {total_files}")
    print(f"Non-trivial instances (nodes > 1): {non_trivial_count}")
    print(f"Trivial instances (nodes ≤ 1): {total_files - non_trivial_count - error_count}")
    print(f"Errors: {error_count}")
    
    if non_trivial_instances:
        print(f"\nNon-trivial instances found:")
        print("-" * 60)
        for instance in non_trivial_instances:
            print(f"File: {os.path.basename(instance['file'])}")
            print(f"  Nodes: {instance['num_nodes']}")
            print(f"  Status: {instance['status']}")
            if instance['obj_val'] is not None:
                print(f"  Objective: {instance['obj_val']:.2f}")
            print()
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    csv_file = "test_uc_instance_results.csv"
    results_df.to_csv(csv_file, index=False)
    print(f"Detailed results saved to: {csv_file}")
    
    return results, non_trivial_instances

if __name__ == "__main__":
    # Run the test
    result = test_uc_instances()
    if result is not None:
        results, non_trivial_instances = result