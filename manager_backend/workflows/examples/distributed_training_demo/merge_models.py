#manager_backend/workflows/examples/distributed_training_demo/split_dataset.py


import torch
from glob import glob

models = [torch.load(f) for f in glob("outputs/*/model.pt")]
avg_model = models[0]
for k in avg_model:
    for m in models[1:]:
        avg_model[k] += m[k]
    avg_model[k] /= len(models)

torch.save(avg_model, "outputs/merged_model.pt")
