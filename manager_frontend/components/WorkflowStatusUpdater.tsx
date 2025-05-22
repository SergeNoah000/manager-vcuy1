import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';

interface WorkflowStatusUpdaterProps {
  workflowId: string;
  onStatusChange?: (status: string, message?: string) => void;
}

const WorkflowStatusUpdater: React.FC<WorkflowStatusUpdaterProps> = ({ 
  workflowId, 
  onStatusChange 
}) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Créer une connexion WebSocket
    console.log(`Tentative de connexion WebSocket pour le workflow ${workflowId}`);
    const ws = new WebSocket('ws://localhost:8765');

    // Gestionnaire d'ouverture de connexion
    ws.onopen = () => {
      console.log('Connexion WebSocket établie');
      setConnected(true);
      
      // S'abonner aux mises à jour du workflow
      const subscriptionMessage = JSON.stringify({
        action: 'subscribe',
        workflow_id: workflowId
      });
      ws.send(subscriptionMessage);
      console.log(`Abonnement envoyé pour le workflow ${workflowId}`);
    };

    // Gestionnaire de messages
    ws.onmessage = (event) => {
      try {
        console.log(`Message WebSocket reçu: ${event.data}`);
        const data = JSON.parse(event.data);
        
        if (data.type === 'subscription_confirmation') {
          console.log(`Abonnement confirmé pour le workflow ${data.workflow_id}`);
          toast.info(`Abonnement aux mises à jour du workflow confirmé`);
        } 
        else if (data.type === 'workflow_update') {
          console.log(`Mise à jour du workflow reçue: ${JSON.stringify(data)}`);
          
          // Extraire les données de la mise à jour
          const status = data.data?.status;
          const message = data.data?.message;
          
          // Notifier l'utilisateur
          if (message) {
            toast.info(message);
          }
          
          // Appeler le callback si fourni
          if (status && onStatusChange) {
            onStatusChange(status, message);
          }
        }
      } catch (error) {
        console.error('Erreur lors du traitement du message WebSocket:', error);
      }
    };

    // Gestionnaire d'erreur
    ws.onerror = (error) => {
      console.error('Erreur WebSocket:', error);
      setConnected(false);
      toast.error('Erreur de connexion aux mises à jour en temps réel');
    };

    // Gestionnaire de fermeture
    ws.onclose = () => {
      console.log('Connexion WebSocket fermée');
      setConnected(false);
    };

    // Stocker la référence du socket
    setSocket(ws);

    // Nettoyage à la désinscription
    return () => {
      console.log('Fermeture de la connexion WebSocket');
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [workflowId]);

  // Ce composant ne rend rien visuellement
  return null;
};

export default WorkflowStatusUpdater;
