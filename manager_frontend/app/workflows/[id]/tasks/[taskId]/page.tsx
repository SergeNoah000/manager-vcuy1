"use client"

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { taskService, volunteerService } from '@/lib/api';
import { Task, Volunteer } from '../../../../../lib/types';
import Link from 'next/link';

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;
  const taskId = params.taskId as string;
  
  const [task, setTask] = useState<Task | null>(null);
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [availableVolunteers, setAvailableVolunteers] = useState<Volunteer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAssignForm, setShowAssignForm] = useState(false);
  const [selectedVolunteerId, setSelectedVolunteerId] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Récupérer les détails de la tâche
        const taskData = await taskService.getTask(taskId);
        setTask(taskData);
        
        // Récupérer les volontaires assignés à cette tâche
        const taskVolunteers = await taskService.getTaskVolunteers(taskId);
        setVolunteers(taskVolunteers);
        
        // Récupérer tous les volontaires disponibles
        const allVolunteers = await volunteerService.getVolunteers();
        const available: Volunteer[] = allVolunteers.filter(
          (v: Volunteer) => v.available && !taskVolunteers.some((tv: Volunteer) => tv.id === v.id)
        );
        setAvailableVolunteers(available);
        
        setLoading(false);
      } catch (err: any) {
        setError(err.error || 'Une erreur est survenue');
        setLoading(false);
      }
    };

    fetchData();
  }, [taskId]);

  const handleAssignVolunteer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVolunteerId) return;
    
    try {
      setLoading(true);
      await taskService.assignTask(taskId, selectedVolunteerId);
      
      // Actualiser les données
      const taskVolunteers = await taskService.getTaskVolunteers(taskId);
      setVolunteers(taskVolunteers);
      
      const allVolunteers = await volunteerService.getVolunteers();
      const available: Volunteer[] = allVolunteers.filter(
        (v: Volunteer) => v.available && !taskVolunteers.some((tv: Volunteer) => tv.id === v.id)
      );
      setAvailableVolunteers(available);
      
      setShowAssignForm(false);
      setSelectedVolunteerId('');
      setLoading(false);
    } catch (err: any) {
      setError(err.error || 'Une erreur est survenue lors de l\'assignation du volontaire');
      setLoading(false);
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'PENDING':
        return {
          bg: 'bg-amber-100',
          text: 'text-amber-800',
          icon: '⏳'
        };
      case 'RUNNING':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          icon: '▶️'
        };
      case 'COMPLETED':
        return {
          bg: 'bg-green-100',
          text: 'text-green-800',
          icon: '✅'
        };
      case 'FAILED':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          icon: '❌'
        };
      case 'ASSIGNED':
        return {
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          icon: '🔗'
        };
      default:
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          icon: '❓'
        };
    }
  };

  if (loading && !task) {
    return (
      <div className="min-h-screen bg-black">
        <div className="container mx-auto p-6">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black">
        <div className="container mx-auto p-6">
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg shadow-md">
            <div className="flex items-center">
              <svg className="h-6 w-6 text-red-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="font-medium">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Format JSON pour une meilleure présentation
  const formatJSON = (json: any) => {
    if (!json) return 'Non défini';
    try {
      if (typeof json === 'string') {
        return JSON.parse(json);
      }
      // Si c'est un objet simple, afficher ses propriétés directement
      if (typeof json === 'object' && Object.keys(json).length < 4) {
        return Object.entries(json)
          .map(([key, value]) => `${key}: ${value}`)
          .join(', ');
      }
      // Sinon formater en JSON
      return JSON.stringify(json, null, 2);
    } catch (e) {
      return json.toString();
    }
  };

  return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <Link href={`/workflows/${workflowId}/tasks`} 
            className="inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors duration-150">
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Retour aux tâches
          </Link>
        </div>

        {task && (
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-6 py-4">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                <h1 className="text-2xl font-bold text-white mb-3 md:mb-0">{task.name}</h1>
                <div className="flex items-center space-x-2">
                  <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusClass(task.status).bg} ${getStatusClass(task.status).text} flex items-center`}>
                    <span className="mr-1">{getStatusClass(task.status).icon}</span>
                    {task.status}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <div className="mb-8">
                <p className="text-gray-700 bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">{task.description}</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
                <div className="bg-gray-50 p-5 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold mb-4 text-gray-800 border-b pb-2">Détails de la tâche</h3>
                  <ul className="space-y-3">
                    <li className="flex">
                      <span className="font-medium w-40 text-gray-700">Workflow:</span> 
                      <span className="text-gray-900">{task.workflow_name}</span>
                    </li>
                    <li className="flex">
                      <span className="font-medium w-40 text-gray-700">Commande:</span> 
                      <code className="bg-gray-100 px-2 py-1 rounded text-blue-700 font-mono">{task.command}</code>
                    </li>
                    <li>
                      <span className="font-medium text-gray-700">Paramètres:</span> 
                      <pre className="mt-1 bg-gray-100 p-2 rounded text-sm overflow-x-auto font-mono">{formatJSON(task.parameters)}</pre>
                    </li>
                    <li>
                      <span className="font-medium text-gray-700">Ressources requises:</span> 
                      <pre className="mt-1 bg-gray-100 p-2 rounded text-sm overflow-x-auto font-mono">{formatJSON(task.required_resources)}</pre>
                    </li>
                    <li className="flex">
                      <span className="font-medium w-40 text-gray-700">Temps max estimé:</span> 
                      <span className="text-gray-900">{task.estimated_max_time} secondes</span>
                    </li>
                    <li className="flex">
                      <span className="font-medium w-40 text-gray-700">Créé le:</span> 
                      <span className="text-gray-900">{new Date(task.created_at).toLocaleString('fr-FR')}</span>
                    </li>
                    {task.start_time && (
                      <li className="flex">
                        <span className="font-medium w-40 text-gray-700">Démarré le:</span> 
                        <span className="text-gray-900">{new Date(task.start_time).toLocaleString('fr-FR')}</span>
                      </li>
                    )}
                    {task.end_time && (
                      <li className="flex">
                        <span className="font-medium w-40 text-gray-700">Terminé le:</span> 
                        <span className="text-gray-900">{new Date(task.end_time).toLocaleString('fr-FR')}</span>
                      </li>
                    )}
                  </ul>
                </div>
                
                <div className="bg-gray-50 p-5 rounded-lg shadow-sm">
                  <h3 className="text-lg font-semibold mb-4 text-gray-800 border-b pb-2">Progression</h3>
                  <div className="mb-6">
                    <div className="flex justify-between mb-1 text-sm font-medium">
                      <span>Avancement</span>
                      <span>{task.progress}%</span>
                    </div>
                    <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          task.status === 'FAILED' ? 'bg-red-500' : 
                          task.status === 'COMPLETED' ? 'bg-green-500' : 
                          'bg-blue-500'
                        } transition-all duration-500 ease-out`} 
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  {task.start_time && task.end_time ? (
                    <div>
                      <h4 className="font-medium text-gray-700 mb-2">Durée d'exécution</h4>
                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-100 flex items-center">
                        <svg className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-blue-800">
                          {((new Date(task.end_time).getTime() - new Date(task.start_time).getTime()) / 1000).toFixed(2)} secondes
                        </span>
                      </div>
                    </div>
                  ) : task.start_time ? (
                    <div>
                      <h4 className="font-medium text-gray-700 mb-2">En cours depuis</h4>
                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-100 flex items-center">
                        <svg className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-blue-800">
                          {((new Date().getTime() - new Date(task.start_time).getTime()) / 1000).toFixed(2)} secondes
                        </span>
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
              
              <div className="mb-10">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Volontaires assignés 
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                      {volunteers.length}
                    </span>
                  </h3>
                  <button
                    onClick={() => setShowAssignForm(!showAssignForm)}
                    className="inline-flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-sm font-medium rounded-md transition-colors duration-150"
                  >
                    <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Assigner un volontaire
                  </button>
                </div>
                
                {showAssignForm && (
                  <div className="bg-gray-50 p-6 rounded-lg shadow-sm mb-6 border border-gray-200">
                    <h4 className="text-md font-semibold mb-4 text-gray-800">Assigner un nouveau volontaire</h4>
                    {availableVolunteers.length === 0 ? (
                      <div className="flex items-center bg-amber-50 text-amber-700 p-4 rounded-lg">
                        <svg className="h-5 w-5 text-amber-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <p>Aucun volontaire disponible pour cette tâche. Les volontaires doivent être disponibles et non déjà assignés.</p>
                      </div>
                    ) : (
                      <form onSubmit={handleAssignVolunteer} className="flex flex-col md:flex-row md:space-x-4">
                        <div className="relative flex-grow mb-4 md:mb-0">
                          <select
                            className="block w-full bg-white border border-gray-300 hover:border-gray-400 px-4 py-3 pr-8 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            value={selectedVolunteerId}
                            onChange={(e) => setSelectedVolunteerId(e.target.value)}
                            required
                          >
                            <option value="">Sélectionnez un volontaire</option>
                            {availableVolunteers.map((volunteer) => (
                              <option key={volunteer.id} value={volunteer.id}>
                                {volunteer.name} ({volunteer.hostname}) - {volunteer.cpu_cores} cœurs, {volunteer.ram_mb} MB RAM
                              </option>
                            ))}
                          </select>
                          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                              <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                            </svg>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            type="submit"
                            className="flex-grow md:flex-grow-0 inline-flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-150"
                          >
                            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                            Assigner
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowAssignForm(false)}
                            className="flex-grow md:flex-grow-0 inline-flex justify-center items-center px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors duration-150"
                          >
                            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            Annuler
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                )}
                
                {volunteers.length === 0 ? (
                  <div className="flex flex-col items-center justify-center bg-gray-50 p-8 rounded-lg border border-gray-200">
                    <svg className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <p className="text-gray-600 italic text-center">Aucun volontaire assigné à cette tâche.</p>
                    <p className="text-gray-500 text-sm mt-2 text-center">Assignez un volontaire pour commencer l'exécution de cette tâche.</p>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Nom
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Ressources
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Statut
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Dernière activité
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {volunteers.map((volunteer) => {
                          const volStatusClass = getStatusClass(volunteer.status);
                          
                          return (
                            <tr key={volunteer.id} className="hover:bg-gray-50 transition-colors duration-150">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold">
                                    {volunteer.name.charAt(0).toUpperCase()}
                                  </div>
                                  <div className="ml-4">
                                    <div className="text-sm font-medium text-gray-900">{volunteer.name}</div>
                                    <div className="text-sm text-gray-500">{volunteer.hostname}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex flex-col">
                                  <div className="flex items-center text-sm text-gray-900">
                                    <svg className="h-4 w-4 text-gray-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                    <span>{volunteer.cpu_cores} CPU cores</span>
                                  </div>
                                  <div className="flex items-center text-sm text-gray-500 mt-1">
                                    <svg className="h-4 w-4 text-gray-400 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                                    </svg>
                                    <span>{volunteer.ram_mb} MB RAM</span>
                                  </div>
                                  <div className="flex items-center text-sm text-gray-500 mt-1">
                                    <svg className="h-4 w-4 text-gray-400 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                    </svg>
                                    <span>{volunteer.disk_gb} GB Disk</span>
                                  </div>
                                  {volunteer.gpu && (
                                    <div className="flex items-center text-sm text-gray-500 mt-1">
                                      <svg className="h-4 w-4 text-gray-400 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                                      </svg>
                                      <span>GPU: {volunteer.gpu}</span>
                                    </div>
                                  )}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${volStatusClass.bg} ${volStatusClass.text}`}>
                                  <span className="mr-1">{volStatusClass.icon}</span>
                                  {volunteer.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <div className="flex items-center">
                                  <svg className="h-4 w-4 text-gray-400 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  {new Date(volunteer.last_seen).toLocaleString('fr-FR')}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <Link href={`/volunteers/${volunteer.id}`} 
                                  className="inline-flex items-center px-3 py-1 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-150">
                                  <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                    </svg>
                                  Détails
                                </Link>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
              
              {task.subtasks && task.subtasks.length > 0 && (
                <div className="bg-gray-50 rounded-lg shadow-sm border border-gray-200 p-6 mb-10">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-800">
                      Sous-tâches
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {task.subtasks.length}
                      </span>
                    </h3>
                  </div>
                  
                  <div className="overflow-hidden rounded-lg border border-gray-200">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Nom
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Statut
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Progression
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {task.subtasks.map((subtask) => {
                          const subtaskStatusClass = getStatusClass(subtask.status);
                          
                          return (
                            <tr key={subtask.id} className="hover:bg-gray-50 transition-colors duration-150">
                              <td className="px-6 py-4">
                                <div className="flex items-center">
                                  <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-xs">
                                    ST
                                  </div>
                                  <div className="ml-4">
                                    <div className="text-sm font-medium text-gray-900">{subtask.name}</div>
                                    {subtask.description && (
                                      <div className="text-sm text-gray-500">
                                        {subtask.description.substring(0, 60)}
                                        {subtask.description.length > 60 ? '...' : ''}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${subtaskStatusClass.bg} ${subtaskStatusClass.text}`}>
                                  <span className="mr-1">{subtaskStatusClass.icon}</span>
                                  {subtask.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="w-full bg-gray-200 rounded-full h-2.5">
                                  <div 
                                    className={`h-2.5 rounded-full ${
                                      subtask.status === 'FAILED' ? 'bg-red-500' : 
                                      subtask.status === 'COMPLETED' ? 'bg-green-500' : 
                                      'bg-blue-500'
                                    }`} 
                                    style={{ width: `${subtask.progress}%` }}>
                                  </div>
                                </div>
                                <p className="text-gray-500 text-xs mt-1">{subtask.progress}%</p>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <Link href={`/workflows/${workflowId}/tasks/${subtask.id}`} 
                                  className="inline-flex items-center px-3 py-1 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-150">
                                  <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  Détails
                                </Link>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              {task.logs && (
                <div className="bg-gray-50 rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Logs d'exécution</h3>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-gray-300 font-mono text-sm whitespace-pre-wrap">{task.logs}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}