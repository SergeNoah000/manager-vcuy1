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

// Gestion des tâches
export const taskService = {
  // Récupérer toutes les tâches
  getTasks: async () => {
    try {
      const response = await api.get('/tasks/');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des tâches' };
      }
    }
  },

  // Récupérer une tâche par ID
  getTask: async (id: string) => {
    try {
      const response = await api.get(`/tasks/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération de la tâche' };
      }
    }
  },

  // Récupérer les tâches d'un workflow
  getWorkflowTasks: async (workflowId: string) => {
    try {
      const response = await api.get(`/tasks/by_workflow/?workflow_id=${workflowId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des tâches du workflow' };
      }
    }
  },

  // Créer une tâche
  createTask: async (taskData: any) => {
    try {
      const response = await api.post('/tasks/', taskData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la création de la tâche' };
      }
    }
  },

  // Mettre à jour une tâche
  updateTask: async (id: string, taskData: any) => {
    try {
      const response = await api.put(`/tasks/${id}/`, taskData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour de la tâche' };
      }
    }
  },

  // Supprimer une tâche
  deleteTask: async (id: string) => {
    try {
      const response = await api.delete(`/tasks/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la suppression de la tâche' };
      }
    }
  },

  // Assigner une tâche à un volontaire
  assignTask: async (taskId: string, volunteerId: string) => {
    try {
      const response = await api.post(`/tasks/${taskId}/assign/`, { volunteer_id: volunteerId });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de l\'assignation de la tâche' };
      }
    }
  },

  // Récupérer les volontaires assignés à une tâche
  getTaskVolunteers: async (taskId: string) => {
    try {
      const response = await api.get(`/tasks/${taskId}/volunteers/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des volontaires de la tâche' };
      }
    }
  },

  // Récupérer les tâches par statut
  getTasksByStatus: async (status: string) => {
    try {
      const response = await api.get(`/tasks/by_status/?status=${status}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des tâches par statut' };
      }
    }
  },

  // Démarrer une tâche
  startTask: async (taskId: string) => {
    try {
      const response = await api.post(`/tasks/${taskId}/start/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors du démarrage de la tâche' };
      }
    }
  },

  // Terminer une tâche
  completeTask: async (taskId: string) => {
    try {
      const response = await api.post(`/tasks/${taskId}/complete/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la complétion de la tâche' };
      }
    }
  },

  // Marquer une tâche comme échouée
  failTask: async (taskId: string, errorMessage: string = '') => {
    try {
      const response = await api.post(`/tasks/${taskId}/fail/`, { error: errorMessage });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors du marquage de la tâche comme échouée' };
      }
    }
  },

  // Mettre à jour la progression d'une tâche
  updateTaskProgress: async (taskId: string, progress: number) => {
    try {
      const response = await api.post(`/tasks/${taskId}/update_progress/`, { progress });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour de la progression' };
      }
    }
  }
};

// Gestion des volontaires
export const volunteerService = {
  // Récupérer tous les volontaires
  getVolunteers: async () => {
    try {
      const response = await api.get('/volunteers/');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des volontaires' };
      }
    }
  },

  // Récupérer un volontaire par ID
  getVolunteer: async (id: string) => {
    try {
      const response = await api.get(`/volunteers/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération du volontaire' };
      }
    }
  },

  // Récupérer les volontaires par workflow
  getWorkflowVolunteers: async (workflowId: string) => {
    try {
      const response = await api.get(`/volunteers/by_workflow/?workflow_id=${workflowId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des volontaires du workflow' };
      }
    }
  },

  // Récupérer les volontaires par statut
  getVolunteersByStatus: async (status: string) => {
    try {
      const response = await api.get(`/volunteers/by_status/?status=${status}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des volontaires par statut' };
      }
    }
  },

  // Récupérer les tâches assignées à un volontaire
  getVolunteerTasks: async (volunteerId: string) => {
    try {
      const response = await api.get(`/volunteers/${volunteerId}/tasks/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des tâches du volontaire' };
      }
    }
  },

  // Assigner une tâche à un volontaire
  assignTask: async (volunteerId: string, taskId: string) => {
    try {
      const response = await api.post(`/volunteers/${volunteerId}/assign_task/`, { task_id: taskId });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de l\'assignation de la tâche' };
      }
    }
  },

  // Mettre à jour le statut d'un volontaire
  updateVolunteerStatus: async (volunteerId: string, status: string) => {
    try {
      const response = await api.patch(`/volunteers/${volunteerId}/`, { status });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour du statut du volontaire' };
      }
    }
  },

  // Mettre à jour la disponibilité d'un volontaire
  updateVolunteerAvailability: async (volunteerId: string, available: boolean) => {
    try {
      const response = await api.patch(`/volunteers/${volunteerId}/`, { available });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour de la disponibilité du volontaire' };
      }
    }
  }
};

// Gestion des assignations de tâches aux volontaires
export const volunteerTaskService = {
  // Récupérer toutes les assignations
  getVolunteerTasks: async () => {
    try {
      const response = await api.get('/volunteers/tasks/');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des assignations' };
      }
    }
  },

  // Récupérer une assignation par ID
  getVolunteerTask: async (id: string) => {
    try {
      const response = await api.get(`/volunteers/tasks/${id}/`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération de l\'assignation' };
      }
    }
  },

  // Récupérer les assignations par tâche
  getTaskAssignments: async (taskId: string) => {
    try {
      const response = await api.get(`/volunteers/tasks/by_task/?task_id=${taskId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des assignations par tâche' };
      }
    }
  },

  // Récupérer les assignations par volontaire
  getVolunteerAssignments: async (volunteerId: string) => {
    try {
      const response = await api.get(`/volunteers/tasks/by_volunteer/?volunteer_id=${volunteerId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la récupération des assignations par volontaire' };
      }
    }
  },

  // Mettre à jour la progression d'une assignation
  updateProgress: async (volunteerTaskId: string, progress: number) => {
    try {
      const response = await api.post(`/volunteers/tasks/${volunteerTaskId}/update_progress/`, { progress });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors de la mise à jour de la progression' };
      }
    }
  },

  // Marquer une assignation comme terminée
  completeTask: async (volunteerTaskId: string, result: any = null) => {
    try {
      const response = await api.post(`/volunteers/tasks/${volunteerTaskId}/complete/`, { result });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors du marquage de l\'assignation comme terminée' };
      }
    }
  },

  // Marquer une assignation comme échouée
  failTask: async (volunteerTaskId: string, error: string) => {
    try {
      const response = await api.post(`/volunteers/tasks/${volunteerTaskId}/fail/`, { error });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw error.response.data;
      } else {
        throw { error: 'Une erreur est survenue lors du marquage de l\'assignation comme échouée' };
      }
    }
  }
};

export default api;