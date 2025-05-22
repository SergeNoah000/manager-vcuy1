/**
 * Service pour gérer les connexions WebSocket avec le backend
 */
class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.callbacks = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000; // 3 secondes
    this.url = `ws://${window.location.hostname}:8765`;
  }

  /**
   * Initialise la connexion WebSocket
   */
  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket déjà connecté ou en cours de connexion');
      return;
    }

    console.log(`Connexion au serveur WebSocket: ${this.url}`);
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      console.log('Connexion WebSocket établie');
      this.connected = true;
      this.reconnectAttempts = 0;
      this._triggerEvent('connected', { status: 'connected' });
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Message WebSocket reçu:', message);
        
        // Déclencher l'événement correspondant au type de message
        if (message.type) {
          this._triggerEvent(message.type, message);
        }
      } catch (error) {
        console.error('Erreur lors du traitement du message WebSocket:', error);
      }
    };

    this.socket.onclose = (event) => {
      this.connected = false;
      console.log(`Connexion WebSocket fermée. Code: ${event.code}, Raison: ${event.reason}`);
      this._triggerEvent('disconnected', { status: 'disconnected', code: event.code, reason: event.reason });
      
      // Tentative de reconnexion
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${this.reconnectInterval}ms...`);
        setTimeout(() => this.connect(), this.reconnectInterval);
      } else {
        console.error('Nombre maximum de tentatives de reconnexion atteint');
      }
    };

    this.socket.onerror = (error) => {
      console.error('Erreur WebSocket:', error);
      this._triggerEvent('error', { error });
    };
  }

  /**
   * S'abonne à un workflow spécifique pour recevoir des mises à jour
   * @param {string} workflowId - ID du workflow à suivre
   */
  subscribeToWorkflow(workflowId) {
    if (!this.connected) {
      console.warn('WebSocket non connecté, impossible de s\'abonner au workflow');
      return;
    }

    const message = {
      action: 'subscribe',
      workflow_id: workflowId
    };

    this.socket.send(JSON.stringify(message));
    console.log(`Abonnement au workflow ${workflowId}`);
  }

  /**
   * Enregistre un callback pour un type d'événement spécifique
   * @param {string} eventType - Type d'événement (ex: 'workflow_update')
   * @param {Function} callback - Fonction à appeler lorsque l'événement se produit
   */
  on(eventType, callback) {
    if (!this.callbacks[eventType]) {
      this.callbacks[eventType] = [];
    }
    this.callbacks[eventType].push(callback);
    return this;
  }

  /**
   * Supprime un callback pour un type d'événement spécifique
   * @param {string} eventType - Type d'événement
   * @param {Function} callback - Fonction à supprimer
   */
  off(eventType, callback) {
    if (!this.callbacks[eventType]) return this;
    
    if (callback) {
      this.callbacks[eventType] = this.callbacks[eventType].filter(cb => cb !== callback);
    } else {
      delete this.callbacks[eventType];
    }
    
    return this;
  }

  /**
   * Déclenche un événement et appelle tous les callbacks associés
   * @param {string} eventType - Type d'événement
   * @param {Object} data - Données associées à l'événement
   * @private
   */
  _triggerEvent(eventType, data) {
    if (!this.callbacks[eventType]) return;
    
    this.callbacks[eventType].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Erreur lors de l'exécution du callback pour l'événement ${eventType}:`, error);
      }
    });
  }

  /**
   * Ferme la connexion WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.connected = false;
    }
  }
}

// Singleton pour partager la même instance dans toute l'application
const websocketService = new WebSocketService();
export default websocketService;
