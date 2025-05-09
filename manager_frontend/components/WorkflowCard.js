export default function WorkflowCard({ workflow }) {
  return (
    <div className="bg-dark-800 p-4 rounded-lg shadow-md">
      <h2 className="text-lg font-semibold text-white">{workflow.name}</h2>
      <p className="text-sm text-gray-400">Status: {workflow.status}</p>
      <p className="text-sm text-gray-400">Progress: {workflow.progress}%</p>
    </div>
  );
}