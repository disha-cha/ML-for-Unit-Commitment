"""
To determine a benchmark set, we must determine that it is
1. benchmark suitable
2. diversity preselect per model
3. cluster select overall
"""
from benchmark import benchmark_suitable
from distance import diversity_preselect
from benchmarkMIP import benchmark_mip

model_groups = []

for model_group in model_groups:
    for model, p in model_group:
        if not benchmark_suitable(model, p):
            continue
    preselect = diversity_preselect(model_group)

benchmark = benchmark_mip(preselect) # output file names?