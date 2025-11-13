import React, { useState, useEffect } from 'react';
import { Search, Download, SortAsc, Eye, X, Loader2 } from 'lucide-react';
import { fetchPopulation } from '../data/mockData';

export const PopulationPage = () => {
  const [population, setPopulation] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('fitness');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedModel, setSelectedModel] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadPopulation();
  }, []);

  const loadPopulation = async () => {
    setLoading(true);
    try {
      const data = await fetchPopulation();
      setPopulation(data);
    } catch (error) {
      console.error('Failed to load population:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleInspect = (model) => {
    setSelectedModel(model);
    setModalOpen(true);
  };

  const handleExport = () => {
    const data = JSON.stringify(population, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `population-${Date.now()}.json`;
    a.click();
  };

  // Filter and sort
  const filteredPopulation = population
    .filter(model => 
      model.modelId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.id.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      
      // Handle string numbers like "156.2M"
      if (typeof aVal === 'string' && aVal.includes('M')) {
        aVal = parseFloat(aVal);
        bVal = parseFloat(bVal);
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

  return (
    <div className="min-h-screen p-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Population Table</h1>
          <p className="text-muted-foreground">
            View and inspect all individuals in the current population
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={population.length === 0}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          <Download size={18} />
          Export
        </button>
      </div>

      {/* Controls */}
      <div className="data-card">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={18} />
            <input
              type="text"
              placeholder="Search by model ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            />
          </div>
          <div className="text-sm text-muted-foreground">
            {filteredPopulation.length} of {population.length} models
          </div>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="data-card h-96 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-muted-foreground">Loading population...</p>
          </div>
        </div>
      ) : (
        <div className="data-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('modelId')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Model ID <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('nodes')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Nodes <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('edges')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Edges <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('fitness')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Fitness <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('accuracy')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Accuracy <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('flops')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      FLOPs <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">
                    <button onClick={() => handleSort('params')} className="flex items-center gap-1 hover:text-primary transition-colors">
                      Params <SortAsc size={14} />
                    </button>
                  </th>
                  <th className="text-left p-4 font-semibold text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPopulation.map((model) => (
                  <tr key={model.id} className="border-b border-border hover:bg-muted/20 transition-colors">
                    <td className="p-4 text-sm font-mono text-primary">{model.modelId}</td>
                    <td className="p-4 text-sm">{model.nodes}</td>
                    <td className="p-4 text-sm">{model.edges}</td>
                    <td className="p-4 text-sm font-semibold">{model.fitness}</td>
                    <td className="p-4 text-sm">{(parseFloat(model.accuracy) * 100).toFixed(1)}%</td>
                    <td className="p-4 text-sm">{model.flops}</td>
                    <td className="p-4 text-sm">{model.params}</td>
                    <td className="p-4">
                      <button
                        onClick={() => handleInspect(model)}
                        className="px-3 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors text-sm font-medium flex items-center gap-1"
                      >
                        <Eye size={14} />
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal */}
      {modalOpen && selectedModel && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-card border-b border-border p-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold">Model Inspector: {selectedModel.modelId}</h2>
              <button
                onClick={() => setModalOpen(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Fitness</p>
                  <p className="text-xl font-bold">{selectedModel.fitness}</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
                  <p className="text-xl font-bold">{(parseFloat(selectedModel.accuracy) * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">FLOPs</p>
                  <p className="text-xl font-bold">{selectedModel.flops}</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Parameters</p>
                  <p className="text-xl font-bold">{selectedModel.params}</p>
                </div>
              </div>

              {/* Architecture DAG */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Architecture DAG</h3>
                <div className="bg-muted/20 border border-border rounded-lg p-6">
                  <svg width="100%" height="300" viewBox="0 0 600 300">
                    {/* Simple DAG visualization */}
                    {selectedModel.architecture.connections.slice(0, 8).map((conn, idx) => {
                      const x1 = 100 + (idx % 4) * 120;
                      const y1 = 50 + Math.floor(idx / 4) * 120;
                      const x2 = x1 + 80;
                      const y2 = y1 + 60;
                      
                      return (
                        <g key={idx}>
                          <line 
                            x1={x1} y1={y1} 
                            x2={x2} y2={y2} 
                            stroke="hsl(var(--primary))" 
                            strokeWidth="2" 
                            opacity="0.5"
                          />
                          <circle cx={x1} cy={y1} r="20" fill="hsl(var(--primary))" opacity="0.8" />
                          <circle cx={x2} cy={y2} r="20" fill="hsl(var(--accent-2))" opacity="0.8" />
                          <text x={x1} y={y1 + 5} textAnchor="middle" fill="white" fontSize="10">
                            {conn.operation.slice(0, 4)}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </div>

              {/* Architecture JSON */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Architecture Details</h3>
                <pre className="bg-muted/20 border border-border rounded-lg p-4 overflow-x-auto text-xs font-mono">
                  {JSON.stringify(selectedModel.architecture, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PopulationPage;