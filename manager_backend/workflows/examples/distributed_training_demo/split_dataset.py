# split_dataset.py
import pickle, os, sys
from torchvision.datasets import CIFAR10

shards = int(sys.argv[1]) if len(sys.argv) > 1 else 4
dataset = CIFAR10("./data", train=True, download=True)
size = len(dataset) // shards

for i in range(shards=4):
    os.makedirs(f"inputs/shard_{i}", exist_ok=True)
    data = dataset.data[i*size:(i+1)*size]
    labels = dataset.targets[i*size:(i+1)*size]
    with open(f"inputs/shard_{i}/data.pkl", "wb") as f:
        pickle.dump((data, labels), f)
