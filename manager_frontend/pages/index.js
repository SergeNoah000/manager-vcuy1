import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import WorkflowCard from '../components/WorkflowCard';
import { connectWebSocket } from '../utils/websocket';

export default function Dashboard() {
  const [workflows, setWorkflows] = useState([]);

  useEffect(() => {
    const socket = connectWebSocket();

    socket.on('workflow/progress', (data) => {
      setWorkflows((prev) =>
        prev.map((wf) => (wf.id === data.workflow_id ? { ...wf, progress: data.progress } : wf))
      );
    });

    socket.on('workflow/finish', (data) => {
      setWorkflows((prev) =>
        prev.map((wf) => (wf.id === data.workflow_id ? { ...wf, status: 'completed' } : wf))
      );
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
          {workflows.map((workflow) => (
            <WorkflowCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      </div>
    </Layout>
  );
}