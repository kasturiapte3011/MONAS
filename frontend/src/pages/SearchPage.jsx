import React, { useState, useRef } from 'react';
import { Play, RotateCcw, Download, Loader2, Save } from 'lucide-react';
import { runSearch, addActivity, updateKPIs } from '../data/mockData';

export const SearchPage = () => {
  const [config, setConfig] = useState({
    populationSize: 50,
    mutationRate: 0.1,
    crossoverRate: 0.7,
    generations: 10,
    objective: 'accuracy'
  });

  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [initialized, setInitialized] = useState(false);

  const result = useRef(null);

  const presets = [
    { name: 'Edge Search', config: { populationSize: 30, mutationRate: 0.15, crossoverRate: 0.6, generations: 15, objective: 'efficiency' } },
    { name: 'High Accuracy', config: { populationSize: 100, mutationRate: 0.05, crossoverRate: 0.8, generations: 20, objective: 'accuracy' } },
    { name: 'Balanced', config: { populationSize: 50, mutationRate: 0.1, crossoverRate: 0.7, generations: 10, objective: 'balanced' } },
  ];

  const handleInputChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handlePreset = (preset) => {
    setConfig(preset.config);
    addLog(`[INFO] Applied preset: ${preset.name}`);
  };

  const addLog = (message) => {
    setLogs(prev => [...prev, { id: Date.now(), message, timestamp: new Date().toLocaleTimeString() }]);
  };

  const handleInitialize = () => {
    setInitialized(true);
    addLog(`[INFO] Population initialized with ${config.populationSize} individuals`);
    addLog(`[INFO] Configuration: mutation=${config.mutationRate}, crossover=${config.crossoverRate}`);
    addActivity('Population initialized', 'success');
  };

  const handleStartSearch = async () => {
    if (!initialized) {
      addLog('[ERROR] Please initialize population first');
      return;
    }

    setIsRunning(true);
    addLog('[INFO] Starting genetic algorithm search...');
    addActivity('Search started', 'info');

    try {
      // const result = await runSearch(config);
      // result.logs.forEach(log => addLog(log));
      result.current = await runSearch(config);
      result.current.logs.forEach(log => addLog(log));


      // Update KPIs
      updateKPIs({
        currentGeneration: config.generations,
        totalEvaluations: config.populationSize * config.generations,
        bestAccuracy: 0.95 + Math.random() * 0.04
      });
      
      addActivity('Search completed successfully', 'success');
    } catch (error) {
      addLog(`[ERROR] Search failed: ${error.message}`);
      addActivity('Search failed', 'warning');
    } finally {
      setIsRunning(false);
    }
  };

  const handleExport = () => {
    const data = { config, logs };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `monas-search-${Date.now()}.json`;
    a.click();
    addLog('[INFO] Results exported');
  };

  const handleSavePlan = () => {
    const plan = { result: result.current, config, timestamp: new Date().toISOString() };
    localStorage.setItem(`evolved-plan-${Date.now()}`, JSON.stringify(plan));
    addActivity('Model build plan saved', 'success');
    alert('Plan saved to local storage!');
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="min-h-screen p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Genetic Algorithm Search</h1>
        <p className="text-muted-foreground">
          Configure and run neural architecture search using multi-objective genetic algorithms
        </p>
      </div>

      {/* Presets */}
      <div className="data-card">
        <h2 className="text-lg font-semibold mb-3">Quick Presets</h2>
        <div className="flex flex-wrap gap-3">
          {presets.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handlePreset(preset)}
              className="px-4 py-2 bg-muted hover:bg-muted/70 rounded-lg text-sm font-medium transition-colors"
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="data-card space-y-4">
          <h2 className="text-lg font-semibold">Configuration</h2>
          
          {/* Population Size */}
          <div>
            <label className="block text-sm font-medium mb-2">Population Size</label>
            <input
              type="number"
              value={config.populationSize}
              onChange={(e) => handleInputChange('populationSize', parseInt(e.target.value) || 0)}
              min="10"
              max="200"
              className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            />
            <p className="text-xs text-muted-foreground mt-1">Number of individuals in each generation (10-200)</p>
          </div>

          {/* Mutation Rate */}
          <div>
            <label className="block text-sm font-medium mb-2">Mutation Rate</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                value={config.mutationRate}
                onChange={(e) => handleInputChange('mutationRate', parseFloat(e.target.value))}
                min="0"
                max="1"
                step="0.01"
                className="flex-1"
              />
              <span className="text-sm font-mono w-12 text-right">{config.mutationRate.toFixed(2)}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Probability of mutation per gene (0.0-1.0)</p>
          </div>

          {/* Crossover Rate */}
          <div>
            <label className="block text-sm font-medium mb-2">Crossover Rate</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                value={config.crossoverRate}
                onChange={(e) => handleInputChange('crossoverRate', parseFloat(e.target.value))}
                min="0"
                max="1"
                step="0.01"
                className="flex-1"
              />
              <span className="text-sm font-mono w-12 text-right">{config.crossoverRate.toFixed(2)}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Probability of crossover between parents (0.0-1.0)</p>
          </div>

          {/* Generations */}
          <div>
            <label className="block text-sm font-medium mb-2">Generations</label>
            <input
              type="number"
              value={config.generations}
              onChange={(e) => handleInputChange('generations', parseInt(e.target.value) || 0)}
              min="1"
              max="100"
              className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            />
            <p className="text-xs text-muted-foreground mt-1">Number of evolutionary generations (1-100)</p>
          </div>

          {/* Objective */}
          <div>
            <label className="block text-sm font-medium mb-2">Primary Objective</label>
            <select
              value={config.objective}
              onChange={(e) => handleInputChange('objective', e.target.value)}
              className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            >
              <option value="accuracy">Maximize Accuracy</option>
              <option value="efficiency">Maximize Efficiency (FLOPs)</option>
              <option value="size">Minimize Model Size</option>
              <option value="latency">Minimize Latency</option>
              <option value="balanced">Balanced (Pareto)</option>
            </select>
          </div>
        </div>

        {/* Logs */}
        <div className="data-card flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Search Logs</h2>
            <button
              onClick={handleClearLogs}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear
            </button>
          </div>
          <div className="flex-1 bg-muted/20 border border-border rounded-lg p-4 font-mono text-sm h-96 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-muted-foreground">No logs yet. Initialize population to start.</p>
            ) : (
              <div className="space-y-1">
                {logs.map(log => (
                  <div key={log.id} className="text-xs">
                    <span className="text-muted-foreground">[{log.timestamp}]</span>{' '}
                    <span className={log.message.includes('[ERROR]') ? 'text-destructive' : log.message.includes('[INFO]') ? 'text-primary' : 'text-foreground'}>
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="data-card">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleInitialize}
            disabled={initialized || isRunning}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            <RotateCcw size={18} />
            Initialize Population
          </button>

          <button
            onClick={handleStartSearch}
            disabled={!initialized || isRunning}
            className="px-6 py-3 bg-success text-foreground rounded-lg font-medium hover:bg-success/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isRunning ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
            {isRunning ? 'Running...' : 'Start Search'}
          </button>

          <button
            onClick={handleExport}
            disabled={logs.length === 0}
            className="px-6 py-3 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/70 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            <Download size={18} />
            Export Results
          </button>

          <button
            onClick={handleSavePlan}
            disabled={!initialized || isRunning || logs.length === 0}
            className="flex-1 px-4 py-2 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/70 transition-all flex items-center justify-center gap-2"
          >
            <Save size={18} />
            Save Plan
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchPage;