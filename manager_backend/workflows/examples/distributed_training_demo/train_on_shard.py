
import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32*32*3, 128), nn.ReLU(),
            nn.Linear(128, 10)
        )
    
    def forward(self, x):
        return self.fc(x)

def load_shard():
    """Charge le shard de données qui est monté dans le conteneur"""
    input_path = "/app/inputs/shard_0/data.pkl"  # Le path sera remplacé dynamiquement
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Le fichier {input_path} n'existe pas.")
    
    # Charger les données
    with open(input_path, "rb") as f:
        data, targets = pickle.load(f)
    
    # Convertir en tenseurs PyTorch
    X = torch.tensor(data, dtype=torch.float32) / 255.0  # Normalisation
    X = X.permute(0, 3, 1, 2)  # Changer l'ordre des dimensions pour PyTorch
    y = torch.tensor(targets, dtype=torch.long)
    
    return X, y

def train_model(X, y, epochs=5, batch_size=64):
    """Entraîne un modèle sur les données fournies"""
    # Créer le dataset et dataloader
    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialiser le modèle
    model = SimpleNet()
    
    # Définir la perte et l'optimiseur
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Entraînement
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    print(f"Entraînement sur {len(X)} échantillons pour {epochs} époques...")
    
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_X, batch_y in dataloader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            # Réinitialiser les gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Backward pass et optimisation
            loss.backward()
            optimizer.step()
            
            # Statistiques
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
        
        epoch_loss = running_loss / len(dataloader)
        epoch_acc = 100 * correct / total
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.2f}%")
    
    print("Entraînement terminé!")
    
    # Retourner le dictionnaire d'état du modèle
    return model.state_dict()

def save_model(model_state):
    """Sauvegarde le modèle entraîné"""
    output_dir = "/app/outputs/shard_0"  # Le path sera remplacé dynamiquement
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "model.pt")
    torch.save(model_state, output_path)
    print(f"Modèle sauvegardé dans {output_path}")

if __name__ == "__main__":
    try:
        # Charger les données
        X, y = load_shard()
        print(f"Données chargées: {X.shape}, {y.shape}")
        
        # Entraîner le modèle
        model_state = train_model(X, y)
        
        # Sauvegarder le modèle
        save_model(model_state)
        
        print("Entraînement et sauvegarde terminés avec succès!")
    except Exception as e:
        print(f"[ERROR] Une erreur s'est produite: {str(e)}")
        raise
