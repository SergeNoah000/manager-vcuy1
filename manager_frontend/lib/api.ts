// lib/api.ts
import axios from 'axios';

// Utiliser une URL absolue pour éviter les problèmes relatifs
const API_URL = 'http://127.0.0.1:8000';

// Instance axios de base
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Ajouter le token d'authentification si disponible
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
  }
  return config;
});

// Log pour débogage des réponses
api.interceptors.response.use(
  response => {
    console.log(`[API] Réponse ${response.config.url}:`, response.status, response.data);
    return response;
  },
  error => {
    console.error(`[API] Erreur ${error.config?.url || 'inconnue'}:`, 
      error.response?.status || 'no status', 
      error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Services d'authentification
export const authService = {
  // Inscription
  register: async (userData: {
    username: string;
    email: string;
    password: string;
    password2: string;
  }) => {
    try {
      // Afficher les données pour le débogage (sans le mot de passe)
      console.log('Envoi des données d\'inscription:', {
        username: userData.username,
        email: userData.email,
        password: '********'
      });
      
      // Envoi de la requête
      const response = await api.post('/workflows/auth/register/', userData);
      
      // Si succès, stockage du token
      if (response.data && response.data.token) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      // Afficher l'erreur pour le débogage
      console.error('Erreur brute:', error);
      
      // Gérer spécifiquement les erreurs
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 500) {
          console.error('Erreur serveur 500:', error.response.data);
          throw { error: "Une erreur serveur s'est produite. Veuillez réessayer plus tard." };
        }
        
        if (error.response?.data) {
          console.error('Détails de l\'erreur:', error.response.data);
          
          // Traiter les différents formats d'erreur possibles
          if (typeof error.response.data === 'string') {
            throw { error: error.response.data };
          }
          
          if (error.response.data.error) {
            throw { error: error.response.data.error };
          }
          
          if (error.response.data.email) {
            throw { error: `Email: ${error.response.data.email}` };
          }
          
          if (error.response.data.username) {
            throw { error: `Username: ${error.response.data.username}` };
          }
          
          if (error.response.data.password) {
            throw { error: `Password: ${error.response.data.password}` };
          }
          
          throw error.response.data;
        }
      }
      
      // Erreur générique
      throw { error: 'Une erreur est survenue lors de l\'inscription' };
    }
  },

  // Connexion
  login: async (credentials: { email: string; password: string }) => {
    try {
      console.log('Tentative de connexion:', { email: credentials.email, password: '********' });
      const response = await api.post('/workflows/auth/login/', credentials);
      
      // Si succès, stockage du token
      if (response.data && response.data.token) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      console.error('Erreur de connexion:', error);
      
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 500) {
          throw { error: "Une erreur serveur s'est produite. Veuillez réessayer plus tard." };
        }
        
        if (error.response?.data) {
          if (typeof error.response.data === 'string') {
            throw { error: error.response.data };
          }
          
          if (error.response.data.error) {
            throw { error: error.response.data.error };
          }
          
          if (error.response.data.email) {
            throw { error: `Email: ${error.response.data.email}` };
          }
          
          if (error.response.data.non_field_errors) {
            throw { error: error.response.data.non_field_errors[0] };
          }
          
          throw error.response.data;
        }
      }
      
      throw { error: 'Une erreur est survenue lors de la connexion' };
    }
  },

  // Déconnexion
  logout: async () => {
    try {
      await api.post('/workflows/auth/logout/');
    } catch (error) {
      console.error('Erreur de déconnexion:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },

  // Vérification d'authentification
  isAuthenticated: () => {
    return typeof window !== 'undefined' && Boolean(localStorage.getItem('token'));
  },

  // Récupération de l'utilisateur
  getCurrentUser: () => {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          return JSON.parse(userStr);
        } catch (error) {
          localStorage.removeItem('user');
          return null;
        }
      }
    }
    return null;
  }
};

// Services pour les workflows
export const workflowService = {
  // Récupérer tous les workflows
  getWorkflows: async () => {
    try {
      const response = await api.get('/workflows/');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des workflows' };
      }
    }
  },

  // Récupérer un workflow par ID
  getWorkflow: async (id: string) => {
    try {
      const response = await api.get(`/workflows/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération du workflow' };
      }
    }
  },

  // Créer un workflow
  createWorkflow: async (workflowData: any) => {
    try {
      const response = await api.post('/workflows/', workflowData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la création du workflow' };
      }
    }
  },

  // Mettre à jour un workflow
  updateWorkflow: async (id: string, workflowData: any) => {
    try {
      const response = await api.put(`/workflows/${id}/`, workflowData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour du workflow' };
      }
    }
  },

  // Supprimer un workflow
  deleteWorkflow: async (id: string) => {
    try {
      const response = await api.delete(`/workflows/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la suppression du workflow' };
      }
    }
  },

  // Soumettre un workflow
  submitWorkflow: async (id: string) => {
    try {
      const response = await api.post(`/workflows/${id}/submit/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la soumission du workflow' };
      }
    }
  },

  // Récupérer les tâches d'un workflow
  getWorkflowTasks: async (id: string) => {
    try {
      const response = await api.get(`/workflows/${id}/tasks/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des tâches du workflow' };
      }
    }
  }
};

export default api;