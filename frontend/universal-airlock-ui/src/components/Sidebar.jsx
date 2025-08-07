import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Lightbulb, ShieldCheck, Upload, FileText } from 'lucide-react';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/ideation', label: 'Ideation', icon: Lightbulb },
  { to: '/validation', label: 'Training-Validation', icon: ShieldCheck },
  { to: '/upload', label: 'Upload Docs', icon: Upload },
  { to: '/reports', label: 'Reports', icon: FileText }
];

export default function Sidebar() {
  return (
    <aside className="h-screen w-56 bg-gray-100 border-r flex flex-col py-6">
      <h2 className="px-6 mb-8 text-xl font-bold text-primary">Universal Airlock</h2>
      <nav className="flex-1 space-y-1 px-2">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `flex items-center gap-3 rounded px-3 py-2 text-sm font-medium ${
                isActive ? 'bg-blue-500 text-white' : 'text-gray-700 hover:bg-gray-200'
              }`
            }
          >
            <Icon className="h-5 w-5" /> {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
