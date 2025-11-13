import React, { useState } from 'react';
import { Lightbulb, Loader2, Download, Save, PlayCircle } from 'lucide-react';
import { advisorSuggest, addActivity, updateKPIs } from '../data/mockData';

export const AdvisorPage = () => {
  const [formData, setFormData] = useState({
    taskType: 'Image Classification',
    datasetSize: 'Medium (10k-100k)',
    priority: {
      accuracy: 0.6,
      latency: 0.3,
      size: 0.1
    },
    targetHardware: 'Cloud GPU',
    maxParams: '',
    maxFlops: '',
    maxLatency: '',
    specialRequirements: ''
  });

  const [suggestion, setSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePriorityChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      priority: { ...prev.priority, [field]: parseFloat(value) }
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    addActivity('Model Advisor query submitted', 'info');
    
    try {
      const result = await advisorSuggest(formData);
      setSuggestion(result);
      addActivity('Model Advisor recommendations generated', 'success');
    } catch (error) {
      console.error('Failed to generate suggestions:', error);
      addActivity('Model Advisor failed', 'warning');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = () => {
    if (!suggestion) return;
    
    const plan = { formData, suggestion, timestamp: new Date().toISOString() };
    localStorage.setItem(`advisor-plan-${Date.now()}`, JSON.stringify(plan));
    addActivity('Model build plan saved', 'success');
    alert('Plan saved to local storage!');
  };

  const handleExportPlan = () => {
    if (!suggestion) return;
    
    const plan = { formData, suggestion, timestamp: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model-plan-${Date.now()}.json`;
    a.click();
    addActivity('Model build plan exported', 'info');
  };

  const handleSimulateBuild = () => {
    if (!suggestion) return;
    
    addActivity('Build simulation started', 'info');
    
    // Simulate build with mock KPI updates
    setTimeout(() => {
      updateKPIs({
        totalEvaluations: Math.floor(Math.random() * 100) + 500,
        bestAccuracy: 0.92 + Math.random() * 0.05
      });
      addActivity('Build simulation completed', 'success');
      alert('Build simulation completed! Check Home page for updated metrics.');
    }, 1500);
  };

  // Normalize priority values to sum to 1
  const totalPriority = formData.priority.accuracy + formData.priority.latency + formData.priority.size;
  const normalizedPriority = {
    accuracy: formData.priority.accuracy / totalPriority,
    latency: formData.priority.latency / totalPriority,
    size: formData.priority.size / totalPriority
  };

  return (
    <div className="min-h-screen p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Model Advisor</h1>
        <p className="text-muted-foreground">
          Describe your desired model and receive an efficient, actionable build plan
        </p>
      </div>

      {/* Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {/* Task Type */}
          <div className="data-card">
            <h2 className="text-lg font-semibold mb-4">Task Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Task Type</label>
                <select
                  value={formData.taskType}
                  onChange={(e) => handleInputChange('taskType', e.target.value)}
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
                >
                  <option>Image Classification</option>
                  <option>Object Detection</option>
                  <option>NLP (text)</option>
                  <option>Tabular</option>
                  <option>Time Series</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Dataset Size</label>
                <div className="grid grid-cols-3 gap-2">
                  {['Small (<10k)', 'Medium (10k-100k)', 'Large (>100k)'].map(size => (
                    <button
                      key={size}
                      onClick={() => handleInputChange('datasetSize', size)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        formData.datasetSize === size
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-foreground hover:bg-muted/70'
                      }`}
                    >
                      {size.split(' ')[0]}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Target Hardware</label>
                <select
                  value={formData.targetHardware}
                  onChange={(e) => handleInputChange('targetHardware', e.target.value)}
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
                >
                  <option>Cloud GPU</option>
                  <option>Edge CPU</option>
                  <option>Mobile (ARM)</option>
                  <option>Raspberry Pi</option>
                </select>
              </div>
            </div>
          </div>

          {/* Priorities */}
          <div className="data-card">
            <h2 className="text-lg font-semibold mb-4">Optimization Priorities</h2>
            
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Accuracy</label>
                  <span className="text-sm text-muted-foreground">{(normalizedPriority.accuracy * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  value={formData.priority.accuracy}
                  onChange={(e) => handlePriorityChange('accuracy', e.target.value)}
                  min="0"
                  max="1"
                  step="0.05"
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Latency (Speed)</label>
                  <span className="text-sm text-muted-foreground">{(normalizedPriority.latency * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  value={formData.priority.latency}
                  onChange={(e) => handlePriorityChange('latency', e.target.value)}
                  min="0"
                  max="1"
                  step="0.05"
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Model Size</label>
                  <span className="text-sm text-muted-foreground">{(normalizedPriority.size * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  value={formData.priority.size}
                  onChange={(e) => handlePriorityChange('size', e.target.value)}
                  min="0"
                  max="1"
                  step="0.05"
                  className="w-full"
                />
              </div>

              {/* Priority visualization */}
              <div className="mt-4 h-6 flex rounded-lg overflow-hidden">
                <div 
                  className="bg-success flex items-center justify-center text-xs font-semibold text-white transition-all duration-300"
                  style={{ width: `${normalizedPriority.accuracy * 100}%` }}
                >
                  {normalizedPriority.accuracy > 0.15 && 'Acc'}
                </div>
                <div 
                  className="bg-primary flex items-center justify-center text-xs font-semibold text-white transition-all duration-300"
                  style={{ width: `${normalizedPriority.latency * 100}%` }}
                >
                  {normalizedPriority.latency > 0.15 && 'Speed'}
                </div>
                <div 
                  className="bg-warning flex items-center justify-center text-xs font-semibold text-black transition-all duration-300"
                  style={{ width: `${normalizedPriority.size * 100}%` }}
                >
                  {normalizedPriority.size > 0.15 && 'Size'}
                </div>
              </div>
            </div>
          </div>

          {/* Constraints */}
          <div className="data-card">
            <h2 className="text-lg font-semibold mb-4">Constraints (Optional)</h2>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Max Parameters (M)</label>
                <input
                  type="number"
                  value={formData.maxParams}
                  onChange={(e) => handleInputChange('maxParams', e.target.value)}
                  placeholder="e.g., 10"
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground text-sm"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Max FLOPs (M)</label>
                <input
                  type="number"
                  value={formData.maxFlops}
                  onChange={(e) => handleInputChange('maxFlops', e.target.value)}
                  placeholder="e.g., 500"
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground text-sm"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Max Latency (ms)</label>
                <input
                  type="number"
                  value={formData.maxLatency}
                  onChange={(e) => handleInputChange('maxLatency', e.target.value)}
                  placeholder="e.g., 100"
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground text-sm"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Special Requirements</label>
                <textarea
                  value={formData.specialRequirements}
                  onChange={(e) => handleInputChange('specialRequirements', e.target.value)}
                  placeholder="Describe any special requirements or constraints..."
                  rows={3}
                  className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground text-sm resize-none"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full px-6 py-4 bg-gradient-to-r from-primary to-accent-2 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-lg"
          >
            {loading ? <Loader2 size={24} className="animate-spin" /> : <Lightbulb size={24} />}
            {loading ? 'Analyzing...' : 'Advise Me'}
          </button>
        </div>

        {/* Results Panel */}
        <div className="space-y-6">
          {suggestion ? (
            <>
              {/* Recommendation Summary */}
              <div className="data-card glass">
                <div className="flex items-start justify-between mb-4">
                  <h2 className="text-xl font-semibold">Recommendations</h2>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">Confidence:</span>
                    <span className="font-bold text-primary">{(suggestion.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {/* Base Architecture */}
                  <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-primary mb-2">1. Base Architecture</h3>
                    <p className="text-2xl font-bold mb-2">{suggestion.baseArchitecture}</p>
                    <p className="text-sm text-muted-foreground">Recommended foundation for your use case</p>
                  </div>

                  {/* Modifications */}
                  <div>
                    <h3 className="text-sm font-semibold mb-2">2. Architectural Modifications</h3>
                    <ul className="space-y-2">
                      {suggestion.modifications.map((mod, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-primary mt-0.5">•</span>
                          <span>{mod}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Data Strategy */}
                  <div>
                    <h3 className="text-sm font-semibold mb-2">3. Data Strategy</h3>
                    <ul className="space-y-2">
                      {suggestion.dataStrategy.map((strategy, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-accent-2 mt-0.5">•</span>
                          <span>{strategy}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Training Recipe */}
                  <div>
                    <h3 className="text-sm font-semibold mb-2">4. Training Recipe</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-muted/30 rounded p-2">
                        <p className="text-xs text-muted-foreground">Epochs</p>
                        <p className="text-sm font-semibold">{suggestion.trainingRecipe.epochs}</p>
                      </div>
                      <div className="bg-muted/30 rounded p-2">
                        <p className="text-xs text-muted-foreground">Batch Size</p>
                        <p className="text-sm font-semibold">{suggestion.trainingRecipe.batchSize}</p>
                      </div>
                      <div className="bg-muted/30 rounded p-2">
                        <p className="text-xs text-muted-foreground">Optimizer</p>
                        <p className="text-sm font-semibold">{suggestion.trainingRecipe.optimizer}</p>
                      </div>
                      <div className="bg-muted/30 rounded p-2">
                        <p className="text-xs text-muted-foreground">LR Schedule</p>
                        <p className="text-sm font-semibold">{suggestion.trainingRecipe.schedule.split(' ')[0]}</p>
                      </div>
                    </div>
                  </div>

                  {/* Compression Options */}
                  {suggestion.compression.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">5. Compression Techniques</h3>
                      <div className="space-y-2">
                        {suggestion.compression.map((comp, idx) => (
                          <div key={idx} className="bg-warning/10 border border-warning/30 rounded-lg p-3">
                            <p className="text-sm font-semibold text-warning mb-1">{comp.technique}</p>
                            <p className="text-xs text-muted-foreground mb-1">{comp.description}</p>
                            <p className="text-xs font-mono text-success">{comp.impact}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Deployment */}
                  <div>
                    <h3 className="text-sm font-semibold mb-2">6. Deployment Notes</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Runtime:</span>
                        <span className="font-medium">{suggestion.deployment.runtime}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Batch Size:</span>
                        <span className="font-medium">{suggestion.deployment.batchSize}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Est. Latency:</span>
                        <span className="font-medium">{suggestion.deployment.estimatedLatency}</span>
                      </div>
                    </div>
                  </div>

                  {/* Justification */}
                  <div className="bg-gradient-to-br from-primary/5 to-accent-2/5 border border-primary/20 rounded-lg p-4">
                    <h3 className="text-sm font-semibold mb-2">Why This Approach?</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {suggestion.justification}
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="data-card">
                <h3 className="text-sm font-semibold mb-3">Actions</h3>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleSavePlan}
                    className="flex-1 px-4 py-2 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/70 transition-all flex items-center justify-center gap-2"
                  >
                    <Save size={18} />
                    Save Plan
                  </button>
                  <button
                    onClick={handleExportPlan}
                    className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
                  >
                    <Download size={18} />
                    Export JSON
                  </button>
                  <button
                    onClick={handleSimulateBuild}
                    className="flex-1 px-4 py-2 bg-success text-foreground rounded-lg font-medium hover:bg-success/90 transition-all flex items-center justify-center gap-2"
                  >
                    <PlayCircle size={18} />
                    Simulate Build
                  </button>
                </div>
              </div>

              {/* Trade-off Visualization */}
              <div className="data-card">
                <h3 className="text-sm font-semibold mb-3">Expected Trade-offs</h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs">Accuracy</span>
                      <span className="text-xs font-mono">~{(0.88 + Math.random() * 0.1).toFixed(2)}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-success" style={{ width: `${85 + Math.random() * 10}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs">Latency</span>
                      <span className="text-xs font-mono">{suggestion.deployment.estimatedLatency}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${70 + Math.random() * 15}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs">Model Size</span>
                      <span className="text-xs font-mono">~{(3 + Math.random() * 5).toFixed(1)}M params</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-warning" style={{ width: `${50 + Math.random() * 20}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="data-card h-full flex items-center justify-center min-h-[600px]">
              <div className="text-center">
                <Lightbulb className="w-20 h-20 text-muted-foreground/40 mx-auto mb-4" />
                <p className="text-muted-foreground mb-2 font-medium">No recommendations yet</p>
                <p className="text-sm text-muted-foreground max-w-md">
                  Configure your model requirements on the left and click "Advise Me" to receive 
                  a customized, efficient build plan tailored to your needs.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdvisorPage;