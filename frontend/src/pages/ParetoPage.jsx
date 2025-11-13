import React, { useState, useEffect } from 'react';
import { Download, Info, X, Loader2, ZoomIn } from 'lucide-react';
import { fetchPareto } from '../data/mockData';

export const ParetoPage = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [xAxis, setXAxis] = useState('flops'); // 'flops' or 'params'
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const paretoData = await fetchPareto();
      setData(paretoData);
    } catch (error) {
      console.error('Failed to load Pareto data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format) => {
    let content, mimeType, filename;
    
    if (format === 'json') {
      content = JSON.stringify(data, null, 2);
      mimeType = 'application/json';
      filename = `pareto-front-${Date.now()}.json`;
    } else {
      // CSV export
      const headers = ['Model ID', 'Accuracy', 'FLOPs', 'Params', 'Latency', 'Is Pareto'];
      const rows = data.map(d => [
        d.modelId,
        d.accuracy,
        d.flops,
        d.params,
        d.latency,
        d.isPareto ? 'Yes' : 'No'
      ]);
      content = [headers, ...rows].map(row => row.join(',')).join('\n');
      mimeType = 'text/csv';
      filename = `pareto-front-${Date.now()}.csv`;
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  // Calculate chart dimensions and scales
  const chartWidth = 700;
  const chartHeight = 500;
  const padding = { top: 40, right: 40, bottom: 60, left: 70 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  // Get data ranges
  const accuracyValues = data.map(d => parseFloat(d.accuracy));
  const xValues = data.map(d => parseFloat(d[xAxis]));
  
  const accuracyMin = Math.min(...accuracyValues) * 0.98;
  const accuracyMax = Math.max(...accuracyValues) * 1.01;
  const xMin = Math.min(...xValues) * 0.95;
  const xMax = Math.max(...xValues) * 1.05;

  // Scale functions
  const scaleX = (value) => padding.left + ((value - xMin) / (xMax - xMin)) * plotWidth;
  const scaleY = (value) => chartHeight - padding.bottom - ((value - accuracyMin) / (accuracyMax - accuracyMin)) * plotHeight;

  return (
    <div className="min-h-screen p-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Pareto Front Visualization</h1>
          <p className="text-muted-foreground">
            Explore the trade-off between accuracy and computational efficiency
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/70 transition-all flex items-center gap-2"
          >
            <Download size={18} />
            CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-all flex items-center gap-2"
          >
            <Download size={18} />
            JSON
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="data-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">X-Axis:</label>
            <div className="flex gap-2">
              <button
                onClick={() => setXAxis('flops')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  xAxis === 'flops' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-foreground hover:bg-muted/70'
                }`}
              >
                FLOPs
              </button>
              <button
                onClick={() => setXAxis('params')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  xAxis === 'params' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-foreground hover:bg-muted/70'
                }`}
              >
                Parameters
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary"></div>
              <span>Pareto Optimal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-muted-foreground/40"></div>
              <span>Non-optimal</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="data-card h-[600px] flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-muted-foreground">Loading Pareto front data...</p>
          </div>
        </div>
      ) : (
        <div className="data-card">
          <div className="relative">
            <svg 
              width={chartWidth} 
              height={chartHeight} 
              className="mx-auto"
              style={{ maxWidth: '100%', height: 'auto' }}
            >
              {/* Grid lines */}
              <g opacity="0.1">
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
                  <line
                    key={`h-${ratio}`}
                    x1={padding.left}
                    y1={padding.top + plotHeight * ratio}
                    x2={padding.left + plotWidth}
                    y2={padding.top + plotHeight * ratio}
                    stroke="currentColor"
                    strokeWidth="1"
                  />
                ))}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
                  <line
                    key={`v-${ratio}`}
                    x1={padding.left + plotWidth * ratio}
                    y1={padding.top}
                    x2={padding.left + plotWidth * ratio}
                    y2={padding.top + plotHeight}
                    stroke="currentColor"
                    strokeWidth="1"
                  />
                ))}
              </g>

              {/* Axes */}
              <line 
                x1={padding.left} 
                y1={chartHeight - padding.bottom} 
                x2={chartWidth - padding.right} 
                y2={chartHeight - padding.bottom} 
                stroke="currentColor" 
                strokeWidth="2"
              />
              <line 
                x1={padding.left} 
                y1={padding.top} 
                x2={padding.left} 
                y2={chartHeight - padding.bottom} 
                stroke="currentColor" 
                strokeWidth="2"
              />

              {/* Axis labels */}
              <text 
                x={chartWidth / 2} 
                y={chartHeight - 10} 
                textAnchor="middle" 
                fill="currentColor" 
                fontSize="14"
                fontWeight="600"
              >
                {xAxis === 'flops' ? 'FLOPs (M)' : 'Parameters (M)'}
              </text>
              <text 
                x={padding.left - 50} 
                y={chartHeight / 2} 
                textAnchor="middle" 
                fill="currentColor" 
                fontSize="14"
                fontWeight="600"
                transform={`rotate(-90, ${padding.left - 50}, ${chartHeight / 2})`}
              >
                Accuracy
              </text>

              {/* Y-axis tick labels */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                const value = accuracyMin + (accuracyMax - accuracyMin) * (1 - ratio);
                return (
                  <text
                    key={`y-label-${ratio}`}
                    x={padding.left - 10}
                    y={padding.top + plotHeight * ratio + 5}
                    textAnchor="end"
                    fill="currentColor"
                    fontSize="11"
                  >
                    {value.toFixed(3)}
                  </text>
                );
              })}

              {/* X-axis tick labels */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                const value = xMin + (xMax - xMin) * ratio;
                return (
                  <text
                    key={`x-label-${ratio}`}
                    x={padding.left + plotWidth * ratio}
                    y={chartHeight - padding.bottom + 20}
                    textAnchor="middle"
                    fill="currentColor"
                    fontSize="11"
                  >
                    {value.toFixed(0)}
                  </text>
                );
              })}

              {/* Data points */}
              {data.map((point, idx) => {
                const x = scaleX(parseFloat(point[xAxis]));
                const y = scaleY(parseFloat(point.accuracy));
                const isHovered = hoveredPoint?.id === point.id;
                
                return (
                  <circle
                    key={point.id}
                    cx={x}
                    cy={y}
                    r={isHovered ? 8 : 6}
                    fill={point.isPareto ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))'}
                    opacity={point.isPareto ? 0.9 : 0.4}
                    className="cursor-pointer transition-all hover:stroke-2"
                    stroke={isHovered ? 'hsl(var(--accent-2))' : 'none'}
                    strokeWidth={isHovered ? 3 : 0}
                    onMouseEnter={() => setHoveredPoint(point)}
                    onMouseLeave={() => setHoveredPoint(null)}
                    onClick={() => setSelectedPoint(point)}
                  />
                );
              })}

              {/* Pareto frontier line */}
              <path
                d={data
                  .filter(d => d.isPareto)
                  .sort((a, b) => parseFloat(a[xAxis]) - parseFloat(b[xAxis]))
                  .map((point, idx) => {
                    const x = scaleX(parseFloat(point[xAxis]));
                    const y = scaleY(parseFloat(point.accuracy));
                    return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="url(#paretoGradient2)"
                strokeWidth="2"
                opacity="0.6"
              />

              <defs>
                <linearGradient id="paretoGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="hsl(var(--primary))" />
                  <stop offset="100%" stopColor="hsl(var(--accent-2))" />
                </linearGradient>
              </defs>
            </svg>

            {/* Hover tooltip */}
            {hoveredPoint && (
              <div 
                className="absolute bg-card border border-primary/50 rounded-lg p-3 shadow-lg pointer-events-none z-10"
                style={{
                  left: `${scaleX(parseFloat(hoveredPoint[xAxis])) + 10}px`,
                  top: `${scaleY(parseFloat(hoveredPoint.accuracy)) - 10}px`,
                  transform: 'translateY(-100%)'
                }}
              >
                <p className="text-xs font-mono text-primary mb-1">{hoveredPoint.modelId}</p>
                <div className="text-xs space-y-0.5">
                  <p><span className="text-muted-foreground">Accuracy:</span> {(parseFloat(hoveredPoint.accuracy) * 100).toFixed(2)}%</p>
                  <p><span className="text-muted-foreground">FLOPs:</span> {hoveredPoint.flops}M</p>
                  <p><span className="text-muted-foreground">Params:</span> {hoveredPoint.params}M</p>
                  <p><span className="text-muted-foreground">Latency:</span> {hoveredPoint.latency}ms</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="data-card">
          <p className="text-sm text-muted-foreground mb-2">Total Models</p>
          <p className="text-3xl font-bold">{data.length}</p>
        </div>
        <div className="data-card">
          <p className="text-sm text-muted-foreground mb-2">Pareto Optimal</p>
          <p className="text-3xl font-bold text-primary">{data.filter(d => d.isPareto).length}</p>
        </div>
        <div className="data-card">
          <p className="text-sm text-muted-foreground mb-2">Best Accuracy</p>
          <p className="text-3xl font-bold text-success">
            {data.length > 0 ? (Math.max(...data.map(d => parseFloat(d.accuracy))) * 100).toFixed(2) + '%' : 'N/A'}
          </p>
        </div>
      </div>

      {/* Selected point modal */}
      {selectedPoint && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-xl max-w-2xl w-full">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-2xl font-bold">Model: {selectedPoint.modelId}</h2>
              <button
                onClick={() => setSelectedPoint(null)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
                  <p className="text-2xl font-bold">{(parseFloat(selectedPoint.accuracy) * 100).toFixed(2)}%</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">FLOPs</p>
                  <p className="text-2xl font-bold">{selectedPoint.flops}M</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Parameters</p>
                  <p className="text-2xl font-bold">{selectedPoint.params}M</p>
                </div>
                <div className="bg-muted/20 p-4 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Latency</p>
                  <p className="text-2xl font-bold">{selectedPoint.latency}ms</p>
                </div>
              </div>
              
              <div className={`p-4 rounded-lg ${
                selectedPoint.isPareto ? 'bg-primary/10 border border-primary/30' : 'bg-muted/20'
              }`}>
                <p className="text-sm font-semibold mb-1">
                  {selectedPoint.isPareto ? '✓ Pareto Optimal' : 'Non-optimal'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {selectedPoint.isPareto 
                    ? 'This model represents a point on the Pareto frontier - no other model can improve one objective without degrading another.' 
                    : 'This model is dominated by other solutions that achieve better trade-offs.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParetoPage;