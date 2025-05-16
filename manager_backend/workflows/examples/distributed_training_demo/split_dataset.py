# manager_backend/workflows/examples/distributed_training_demo/split_dataset.py
import os
import pickle
import numpy as np
import sys
from torchvision.datasets import CIFAR10
from torchvision import transforms
import shutil
import argparse

def download_cifar10():
    """Télécharge le dataset CIFAR10 s'il n'est pas déjà présent"""
    print(f"[INFO] Téléchargement du dataset CIFAR10...")
    # Le téléchargement se fait automatiquement lors de la première utilisation
    CIFAR10('./data', train=True, download=True, transform=transforms.ToTensor())
    print(f"[INFO] Dataset téléchargé avec succès!")

def split_dataset(num_shards):
    """
    Divise le dataset CIFAR10 en num_shards parties égales.
    Chaque shard est sauvegardé dans un répertoire distinct.
    
    Args:
        num_shards (int): Nombre de shards à créer
    """
    print(f"[INFO] Découpage du dataset en {num_shards} shards...")
    
    # Assurer que les répertoires existent
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "inputs")
    output_dir = os.path.join(base_dir, "outputs")
    
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Charger le dataset CIFAR10
    cifar10 = CIFAR10('./data', train=True, download=False, transform=transforms.ToTensor())
    data = cifar10.data  # numpy array de shape (50000, 32, 32, 3)
    targets = np.array(cifar10.targets)  # liste de 50000 labels
    
    # Calculer la taille de chaque shard
    samples_per_shard = len(data) // num_shards
    
    # Diviser les données en shards
    for i in range(num_shards):
        # Calculer les indices de début et fin pour ce shard
        start_idx = i * samples_per_shard
        end_idx = (i + 1) * samples_per_shard if i < num_shards - 1 else len(data)
        
        # Extraire les données et cibles pour ce shard
        shard_data = data[start_idx:end_idx]
        shard_targets = targets[start_idx:end_idx]
        
        # Créer un répertoire pour ce shard
        shard_dir = os.path.join(input_dir, f"shard_{i}")
        os.makedirs(shard_dir, exist_ok=True)
        
        # Créer aussi un répertoire de sortie pour ce shard
        shard_output_dir = os.path.join(output_dir, f"shard_{i}")
        os.makedirs(shard_output_dir, exist_ok=True)
        
        # Sauvegarder les données et cibles dans ce répertoire
        with open(os.path.join(shard_dir, "data.pkl"), "wb") as f:
            pickle.dump((shard_data, shard_targets), f)
        
        print(f"[INFO] Shard {i}: {len(shard_data)} échantillons sauvegardés.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Découpe le dataset CIFAR10 en N shards.")
    parser.add_argument("num_shards", type=int, help="Nombre de shards à créer")
    args = parser.parse_args()
    
    # Télécharger le dataset si nécessaire
    download_cifar10()
    
    # Découper le dataset
    split_dataset(args.num_shards)
    
    print("[INFO] Découpage terminé avec succès!")