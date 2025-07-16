"""
Currently, there are two large zip files in the folder data/

The zip folder contains .mps files named in the form output_<number>_<case>.mps

This script will rename the files to

data/
    uc-<case>/
        model-<number>/
            model.mps
        model-<number>/
            model.mps
        ...
    uc-<case>/
        ...
"""

import os
from glob import glob
import zipfile

INSTANCE_PATTERN = "data/output_*.mps"

# Unzip all zip files in data/ directory
zip_files = glob("tmp_test_data/*.zip")
for zip_path in zip_files:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("data/")

if not os.path.exists('data'):
    os.makedirs('data')

def get_output_dir(case_number, model_number):
    return f"data/uc-{case_number}/model-{model_number}"

for instance_path in glob(INSTANCE_PATTERN):
    case_type = instance_path.split("_")[-1].split(".")[0]
    model_number = instance_path.split("_")[-2]
    output_dir = get_output_dir(case_type, model_number)
    os.makedirs(output_dir, exist_ok=True)
    os.rename(instance_path, f"{output_dir}/model.mps")

print("Done")