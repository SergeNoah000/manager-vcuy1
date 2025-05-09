export default function Layout({ children }) {
  return (
    <div className="bg-dark-900 min-h-screen text-white">
      <header className="bg-dark-800 p-4">
        <h1 className="text-xl font-bold">ManagerApp</h1>
      </header>
      <main className="p-4">{children}</main>
    </div>
  );
}