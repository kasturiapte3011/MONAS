import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Search, Users, TrendingUp, Brain, Lightbulb } from 'lucide-react';
import Logo from './Logo';

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/population', label: 'Population', icon: Users },
  { path: '/pareto', label: 'Pareto Front', icon: TrendingUp },
  { path: '/explain', label: 'Explain', icon: Brain },
  { path: '/advisor', label: 'Model Advisor', icon: Lightbulb },
];

export const Sidebar = () => {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <Logo size="default" variant="full" />
        <p className="text-xs text-muted-foreground mt-2">Multi-Objective Neural Architecture Search</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-primary/10 text-primary border border-primary/20' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                }
              `}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground space-y-1">
          <p>MONAS v1.0.0</p>
          <p className="text-[10px]">Research Dashboard</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;