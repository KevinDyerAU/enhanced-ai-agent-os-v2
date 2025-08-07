import Sidebar from './Sidebar.jsx';
import { Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 min-h-screen bg-white p-6 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
