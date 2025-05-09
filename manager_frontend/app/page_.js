import { useEffect, useState } from "react";
import { connectWebSocket } from "../utils/websocket";

export default function Dashboard() {
  const [workflows, setWorkflows] = useState([]);

  useEffect(() => {
    const socket = connectWebSocket();

    // Écouter les mises à jour des workflows
    socket.on("workflow/progress", (data) => {
      setWorkflows((prev) =>
        prev.map((wf) =>
          wf.id === data.workflow_id ? { ...wf, progress: data.progress } : wf
        )
      );
    });

    socket.on("workflow/finish", (data) => {
      setWorkflows((prev) =>
        prev.map((wf) =>
          wf.id === data.workflow_id ? { ...wf, status: "completed" } : wf
        )
      );
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div className="bg-dark-900 min-h-screen text-white p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.length > 0 ? (
          workflows.map((workflow) => (
            <div
              key={workflow.id}
              className="bg-dark-800 p-4 rounded-lg shadow-md"
            >
              <h2 className="text-lg font-semibold">{workflow.name}</h2>
              <p className="text-sm text-gray-400">
                Status: {workflow.status}
              </p>
              <p className="text-sm text-gray-400">
                Progress: {workflow.progress}%
              </p>
            </div>
          ))
        ) : (
          <p className="text-gray-400">Aucun workflow disponible.</p>
        )}
      </div>
    </div>
  );
}
