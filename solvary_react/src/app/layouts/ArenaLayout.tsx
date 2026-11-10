import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/app/providers/AuthProvider';
import { Avatar } from '@/shared/components/Avatar';
import { Code2, Home, LogOut, Swords, Timer, Users, Zap } from 'lucide-react';
import { ActiveInterviewPill } from '@/features/interviews/components/ActiveInterviewPill';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/problems', label: 'Problems', icon: Swords },
  { to: '/drills', label: 'Drills', icon: Zap },
  { to: '/workspaces', label: 'Workspaces', icon: Users },
  { to: '/interviews', label: 'Interviews', icon: Timer },
] as const;

export function ArenaLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Top bar */}
      <header className="h-12 bg-gray-900 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-white font-bold">
            <Code2 size={20} className="text-indigo-400" />
            Solvary
          </div>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                <Icon size={13} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {user && <ActiveInterviewPill />}
          {user && <Avatar src={user.avatar_url} name={user.name} size="sm" />}
          <button
            onClick={handleLogout}
            className="p-1 rounded hover:bg-white/10 text-white/70"
            title="Sign out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Page content — rendered by child route */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
