import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import websocketService from '../services/websocket.service';

/**
 * Composant pour gérer les notifications en temps réel des changements de statut des workflows
 * Ce composant ne rend rien visuellement, il gère uniquement les notifications
 */
const WorkflowStatusNotifier = ({ workflowId }) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Initialiser la connexion WebSocket
    websocketService.connect();

    // Gérer les événements de connexion
    const handleConnected = () => {
      setIsConnected(true);
      toast.success('Connexion au serveur de notifications établie');
      
      // S'abonner au workflow une fois connecté
      if (workflowId) {
        websocketService.subscribeToWorkflow(workflowId);
      }
    };

    // Gérer les événements de déconnexion
    const handleDisconnected = () => {
      setIsConnected(false);
      toast.error('Connexion au serveur de notifications perdue');
    };

    // Gérer les mises à jour de statut des workflows
    const handleWorkflowUpdate = (data) => {
      if (data.workflow_id === workflowId) {
        // Afficher une notification toast avec le message approprié
        const statusMap = {
          'SUBMITTING': { type: 'info', message: 'Soumission en cours...' },
          'SPLITTING': { type: 'info', message: 'Découpage du workflow en tâches...' },
          'SPLIT_COMPLETED': { type: 'success', message: 'Découpage terminé' },
          'ASSIGNING': { type: 'info', message: 'Attribution des tâches aux volontaires...' },
          'ASSIGNED': { type: 'success', message: 'Tâches attribuées avec succès' },
          'WAITING_VOLUNTEERS': { type: 'warning', message: 'En attente de volontaires disponibles' },
          'SUBMISSION_FAILED': { type: 'error', message: 'Échec de la soumission' },
          'ERROR': { type: 'error', message: 'Une erreur est survenue' }
        };

        const statusInfo = statusMap[data.status] || { type: 'info', message: data.message || 'Mise à jour du workflow' };
        
        // Afficher la notification avec le type approprié
        switch (statusInfo.type) {
          case 'success':
            toast.success(data.message || statusInfo.message);
            break;
          case 'error':
            toast.error(data.message || statusInfo.message);
            break;
          case 'warning':
            toast.warning(data.message || statusInfo.message);
            break;
          default:
            toast.info(data.message || statusInfo.message);
        }
      }
    };

    // S'abonner aux événements WebSocket
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('workflow_update', handleWorkflowUpdate);

    // Nettoyer les abonnements lors du démontage du composant
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('workflow_update', handleWorkflowUpdate);
    };
  }, [workflowId]);

  // S'abonner au workflow si l'ID change
  useEffect(() => {
    if (isConnected && workflowId) {
      websocketService.subscribeToWorkflow(workflowId);
    }
  }, [isConnected, workflowId]);

  // Ce composant ne rend rien visuellement
  return null;
};

export default WorkflowStatusNotifier;
