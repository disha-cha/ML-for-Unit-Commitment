import os
import csv

def parse_mps_file(mps_path):
    """
    Parses an MPS file to extract:
    - number of binary variables
    - number of continuous variables
    - number of integer variables
    - number of semi-continuous variables
    - number of semi-integer variables
    - number of free variables
    - number of fixed variables
    - number of variables with lower bound zero
    - number of variables with upper bound zero
    - number of variables with lower bound nonzero
    - number of variables with upper bound nonzero
    - number of variables with both bounds finite
    - number of variables with only lower bound finite
    - number of variables with only upper bound finite
    - number of variables with infinite bounds
    - total variables
    - number of constraints
    - number of equality constraints
    - number of inequality constraints
    - number of nonzero entries (matrix coefficients)
    - max absolute value of matrix coefficients
    - min absolute value of matrix coefficients
    - objective and constraint dynamism (ratio of largest to smallest nonzero coefficient)
    - number of nonzero objective coefficients
    - number of nonzero constraint coefficients
    - density of constraint matrix
    """
    n_bin = 0
    n_cont = 0
    n_int = 0
    n_semi_cont = 0
    n_semi_int = 0
    n_free = 0
    n_fixed = 0
    n_lb_zero = 0
    n_ub_zero = 0
    n_lb_nonzero = 0
    n_ub_nonzero = 0
    n_both_finite = 0
    n_only_lb_finite = 0
    n_only_ub_finite = 0
    n_infinite = 0
    n_var = 0
    n_con = 0
    n_eq_con = 0
    n_ineq_con = 0
    n_nz = 0
    max_coeff = 0.0
    min_coeff = None
    obj_coeffs = []
    con_coeffs = []
    n_obj_nz = 0
    n_con_nz = 0
    density = 0.0

    section = None
    var_types = {}
    var_set = set()
    con_set = set()
    with open(mps_path, 'r') as f:
        for line in f:
            if line.startswith('*') or line.strip() == '':
                continue
            if line.startswith('NAME'):
                continue
            if line.startswith('ROWS'):
                section = 'ROWS'
                continue
            if line.startswith('COLUMNS'):
                section = 'COLUMNS'
                continue
            if line.startswith('RHS'):
                section = 'RHS'
                continue
            if line.startswith('BOUNDS'):
                section = 'BOUNDS'
                continue
            if line.startswith('ENDATA'):
                break

            if section == 'ROWS':
                # ROWS section: constraint names
                parts = line.split()
                if len(parts) >= 2:
                    con_set.add(parts[1])
            elif section == 'COLUMNS':
                # COLUMNS section: variable coefficients in constraints and objective
                parts = line.split()
                if len(parts) >= 2:
                    var = parts[0]
                    var_set.add(var)
                    # Each line can have up to two (con, coeff) pairs
                    for i in range(1, len(parts)-1, 2):
                        con = parts[i]
                        try:
                            coeff = float(parts[i+1])
                        except Exception:
                            continue
                        n_nz += 1
                        if con == 'OBJ' or con == 'obj' or con == 'OBJECTIVE':
                            obj_coeffs.append(abs(coeff))
                        else:
                            con_coeffs.append(abs(coeff))
                        if min_coeff is None or abs(coeff) < min_coeff:
                            min_coeff = abs(coeff)
                        if abs(coeff) > max_coeff:
                            max_coeff = abs(coeff)
            elif section == 'BOUNDS':
                # BOUNDS section: variable types
                parts = line.split()
                if len(parts) >= 3:
                    bound_type = parts[0]
                    var = parts[2]
                    if bound_type in ('BV', 'LI', 'UI', 'BV '):
                        var_types[var] = 'BINARY'
                    elif bound_type in ('LO', 'UP', 'FX', 'FR'):
                        if var not in var_types:
                            var_types[var] = 'CONTINUOUS'
    # Count variable types
    for var in var_set:
        if var_types.get(var, 'CONTINUOUS') == 'BINARY':
            n_bin += 1
        else:
            n_cont += 1
    n_var = len(var_set)
    n_con = len(con_set)
    # Dynamism
    obj_dynamism = (max(obj_coeffs) / min(obj_coeffs)) if obj_coeffs and min(obj_coeffs) > 0 else None
    con_dynamism = (max(con_coeffs) / min(con_coeffs)) if con_coeffs and min(con_coeffs) > 0 else None

    return {
        'n_bin': n_bin,
        'n_cont': n_cont,
        'n_var': n_var,
        'n_con': n_con,
        'n_nz': n_nz,
        'max_coeff': max_coeff,
        'min_coeff': min_coeff,
        'obj_dynamism': obj_dynamism,
        'con_dynamism': con_dynamism,
        'n_obj_nz': n_obj_nz,
        'n_con_nz': n_con_nz,
        'density': density
    }

def collect_mps_info(data_dir='data'):
    rows = []
    for case_dir in os.listdir(data_dir):
        case_path = os.path.join(data_dir, case_dir)
        if not os.path.isdir(case_path):
            continue
        for model_dir in os.listdir(case_path):
            model_path = os.path.join(case_path, model_dir)
            if not os.path.isdir(model_path):
                continue
            mps_file = os.path.join(model_path, 'model.mps')
            if not os.path.isfile(mps_file):
                continue
            # Extract model number from model_dir
            model_number = model_dir.replace('model-', '')
            # Extract case type from case_dir (e.g., uc-pegase1354 -> pegase1354)
            if '-' in case_dir:
                case_type = case_dir.split('-', 1)[1]
            else:
                case_type = case_dir
            mps_info = parse_mps_file(mps_file)
            row = {
                'model_number': model_number,
                'case_type': case_type,
                'n_bin': mps_info['n_bin'],
                'n_cont': mps_info['n_cont'],
                'n_var': mps_info['n_var'],
                'n_con': mps_info['n_con'],
                'n_nz': mps_info['n_nz'],
                'max_coeff': mps_info['max_coeff'],
                'min_coeff': mps_info['min_coeff'],
                'obj_dynamism': mps_info['obj_dynamism'],
                'con_dynamism': mps_info['con_dynamism'],
                'n_obj_nz': mps_info['n_obj_nz'],
                'n_con_nz': mps_info['n_con_nz'],
                'density': mps_info['density'],
                'mps_path': mps_file
            }
            rows.append(row)
    return rows

def write_csv(rows, out_path='mps_summary.csv'):
    if not rows:
        print("No data to write.")
        return
    fieldnames = list(rows[0].keys())
    with open(out_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == '__main__':
    rows = collect_mps_info('data')
    # Sort rows by model_number as integer
    rows.sort(key=lambda x: int(x['model_number']))
    write_csv(rows, 'mps_summary.csv')
    print(f"Wrote summary for {len(rows)} models to mps_summary.csv")
