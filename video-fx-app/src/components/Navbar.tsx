import { Film, CreditCard, LayoutDashboard, Upload } from 'lucide-react';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function Navbar({ currentPage, onNavigate }: NavbarProps) {
  const links = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'editor', label: 'Editor', icon: Film },
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'pricing', label: 'Pricing', icon: CreditCard },
  ];

  return (
    <nav className="glass-card border-b border-purple-500/10 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
          <Film className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold gradient-text">VideoFX AI</span>
      </button>

      <div className="flex items-center gap-1">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = currentPage === link.id;
          return (
            <button
              key={link.id}
              onClick={() => onNavigate(link.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-purple-500/20 text-purple-300'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              {link.label}
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs text-zinc-500 bg-zinc-800/50 px-3 py-1.5 rounded-full">
          Free Plan
        </span>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-blue-400 flex items-center justify-center text-xs font-bold text-white">
          U
        </div>
      </div>
    </nav>
  );
}
