# backend/workflows/utils/resource_estimator.py
import os
import pickle
import json

def estimate_flops_memory(data):
    flops = (3072 * 128 + 128 * 10) * len(data) * 2
    memory = len(data) * 32 * 32 * 3 + (3072 * 128 + 128 * 10) * 4
    return flops, memory

def estimate_resources(inputs_dir):
    total_flops = 0
    total_memory = 0
    shard_count = 0

    for name in os.listdir(inputs_dir):
        shard_path = os.path.join(inputs_dir, name)
        data_file = os.path.join(shard_path, "data.pkl")
        if os.path.isfile(data_file):
            with open(data_file, "rb") as f:
                data, _ = pickle.load(f)
            flops, memory = estimate_flops_memory(data)
            total_flops += flops
            total_memory += memory
            shard_count += 1

    return {
        "estimated_flops": total_flops,
        "estimated_memory_bytes": total_memory,
        "estimated_time_seconds": round(total_flops / 1e9, 2),  # Assuming 1 GFLOP/s
        "shards": shard_count
    }

