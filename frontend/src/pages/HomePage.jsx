import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Database, Lightbulb, TrendingUp, Activity, Zap } from 'lucide-react';
import { getKPIs, getActivityLog } from '../data/mockData';

export const HomePage = () => {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(getKPIs());
  const [activities, setActivities] = useState(getActivityLog());

  useEffect(() => {
    // Update KPIs periodically
    const interval = setInterval(() => {
      setKpis(getKPIs());
      setActivities(getActivityLog());
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const quickActions = [
    { icon: Play, label: 'Start New Search', path: '/search', color: 'primary' },
    { icon: Database, label: 'Load Population', path: '/population', color: 'accent-2' },
    { icon: Lightbulb, label: 'Open Model Advisor', path: '/advisor', color: 'warning' },
  ];

  const kpiCards = [
    { 
      label: 'Best Accuracy', 
      value: (kpis.bestAccuracy * 100).toFixed(1) + '%', 
      icon: TrendingUp,
      trend: '+2.3%',
      color: 'success'
    },
    { 
      label: 'Best Tradeoff', 
      value: `${(kpis.bestTradeoff.accuracy * 100).toFixed(1)}% @ ${kpis.bestTradeoff.flops}M`, 
      icon: Zap,
      trend: 'Optimal',
      color: 'primary'
    },
    { 
      label: 'Current Generation', 
      value: kpis.currentGeneration, 
      icon: Activity,
      trend: 'Active',
      color: 'accent-2'
    },
    { 
      label: 'Total Evaluations', 
      value: kpis.totalEvaluations, 
      icon: Database,
      trend: '+12 recent',
      color: 'muted'
    },
  ];

  return (
    <div className="min-h-screen p-8 space-y-8">
      {/* Hero Section */}
      <div className="data-card glass">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">
              Welcome to <span className="gradient-text">MONAS</span>
            </h1>
            <p className="text-muted-foreground text-lg">
              Multi-Objective Neural Architecture Search Platform
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Explore, optimize, and explain neural network architectures with cutting-edge genetic algorithms.
            </p>
          </div>
          <div className="bg-primary/10 p-4 rounded-lg">
            <Activity className="w-12 h-12 text-primary animate-pulse" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <button
                key={idx}
                onClick={() => navigate(action.path)}
                className="data-card text-left group cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg bg-${action.color}/10 group-hover:bg-${action.color}/20 transition-colors`}>
                    <Icon className={`w-6 h-6 text-${action.color}`} />
                  </div>
                  <div>
                    <p className="font-semibold">{action.label}</p>
                    <p className="text-xs text-muted-foreground">Click to navigate</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiCards.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <div key={idx} className="data-card">
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2 rounded-lg bg-${kpi.color}/10`}>
                    <Icon className={`w-5 h-5 text-${kpi.color}`} />
                  </div>
                  <span className="text-xs text-success font-medium">{kpi.trend}</span>
                </div>
                <p className="text-2xl font-bold mb-1">{kpi.value}</p>
                <p className="text-sm text-muted-foreground">{kpi.label}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Activity and Pareto Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="data-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Recent Activity</h2>
            <Activity className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {activities.slice(-8).reverse().map((activity) => (
              <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/20 border border-border/50">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  activity.type === 'success' ? 'bg-success' : 
                  activity.type === 'warning' ? 'bg-warning' : 
                  'bg-primary'
                }`} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{activity.action}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mini Pareto Preview */}
        <div className="data-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Pareto Front Preview</h2>
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="h-64 flex items-center justify-center border border-border rounded-lg bg-muted/10">
            {/* Simple sparkline visualization */}
            <div className="text-center">
              <div className="mb-4">
                <svg className="w-full h-40" viewBox="0 0 300 150">
                  {/* Grid */}
                  <line x1="30" y1="10" x2="30" y2="140" stroke="hsl(var(--border))" strokeWidth="1" />
                  <line x1="30" y1="140" x2="290" y2="140" stroke="hsl(var(--border))" strokeWidth="1" />
                  
                  {/* Mock Pareto curve */}
                  <path
                    d="M 40 120 Q 80 80, 120 60 T 200 30 T 280 20"
                    fill="none"
                    stroke="url(#paretoGradient)"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                  
                  {/* Points */}
                  {[40, 80, 120, 160, 200, 240, 280].map((x, i) => {
                    const y = 120 - (i * i * 2);
                    return (
                      <circle
                        key={i}
                        cx={x}
                        cy={Math.max(20, y)}
                        r="4"
                        fill="hsl(188, 94%, 43%)"
                        className="hover:r-6 transition-all"
                      />
                    );
                  })}
                  
                  <defs>
                    <linearGradient id="paretoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="hsl(188, 94%, 43%)" />
                      <stop offset="100%" stopColor="hsl(174, 100%, 48%)" />
                    </linearGradient>
                  </defs>
                  
                  {/* Labels */}
                  <text x="150" y="155" fill="hsl(var(--muted-foreground))" fontSize="10" textAnchor="middle">
                    FLOPs (M)
                  </text>
                  <text x="10" y="75" fill="hsl(var(--muted-foreground))" fontSize="10" textAnchor="middle" transform="rotate(-90, 10, 75)">
                    Accuracy
                  </text>
                </svg>
              </div>
              <button
                onClick={() => navigate('/pareto')}
                className="text-sm text-primary hover:text-primary/80 font-medium transition-colors"
              >
                View Full Pareto Front →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* About Section */}
      <div className="data-card bg-gradient-to-br from-primary/5 to-accent-2/5 border-primary/20">
        <h2 className="text-xl font-semibold mb-3">About MONAS</h2>
        <p className="text-muted-foreground leading-relaxed">
          MONAS is a cutting-edge platform for automated neural architecture search using multi-objective genetic algorithms. 
          It helps researchers and practitioners discover optimal network architectures that balance accuracy, computational efficiency, 
          and inference speed. Our explainability features provide insights into why certain architectures perform better, 
          making the search process transparent and actionable.
        </p>
      </div>
    </div>
  );
};

export default HomePage;