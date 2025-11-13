import React, { useState } from 'react';
import { Brain, Loader2, Info } from 'lucide-react';
import { generateExplanation } from '../data/mockData';

export const ExplainPage = () => {
  const [modelId, setModelId] = useState('model_42');
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [explainType, setExplainType] = useState('global'); // 'global' or 'instance'

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const data = await generateExplanation(modelId);
      setExplanation(data);
    } catch (error) {
      console.error('Failed to generate explanation:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Model Explainability</h1>
        <p className="text-muted-foreground">
          Understand why certain architectures perform better using SHAP and LIME analysis
        </p>
      </div>

      {/* Controls */}
      <div className="data-card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Model ID</label>
            <input
              type="text"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="Enter model ID..."
              className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Explanation Type</label>
            <div className="flex gap-2">
              <button
                onClick={() => setExplainType('global')}
                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  explainType === 'global' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-foreground hover:bg-muted/70'
                }`}
              >
                Global
              </button>
              <button
                onClick={() => setExplainType('instance')}
                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  explainType === 'instance' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-foreground hover:bg-muted/70'
                }`}
              >
                Instance-level
              </button>
            </div>
          </div>
        </div>
        
        <button
          onClick={handleGenerate}
          disabled={loading || !modelId}
          className="mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Brain size={18} />}
          {loading ? 'Generating...' : 'Generate Explanation'}
        </button>
      </div>

      {/* Results */}
      {explanation ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Feature Importance */}
          <div className="data-card">
            <div className="flex items-center gap-2 mb-4">
              <h2 className="text-xl font-semibold">Feature Importance</h2>
              <div className="group relative">
                <Info size={16} className="text-muted-foreground cursor-help" />
                <div className="absolute left-0 top-6 w-64 bg-card border border-border rounded-lg p-3 shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
                  <p className="text-xs text-muted-foreground">
                    SHAP values showing how much each architectural feature contributes to model performance.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              {explanation.features.map((feature, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{feature.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {(feature.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-accent-2 transition-all duration-500"
                      style={{ width: `${feature.importance * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
              <p className="text-xs font-semibold text-primary mb-1">Method: {explanation.method}</p>
              <p className="text-xs text-muted-foreground">
                Using SHapley Additive exPlanations to determine feature contributions
              </p>
            </div>
          </div>

          {/* Explanation Details */}
          <div className="data-card">
            <h2 className="text-xl font-semibold mb-4">Explanation Details</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold mb-2">Summary</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {explanation.explanation}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold mb-2 text-success">Positive Contributors</h3>
                <div className="flex flex-wrap gap-2">
                  {explanation.limeData.positive.map((item, idx) => (
                    <span 
                      key={idx}
                      className="px-3 py-1 bg-success/10 text-success border border-success/30 rounded-full text-xs font-medium"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold mb-2 text-destructive">Negative Contributors</h3>
                <div className="flex flex-wrap gap-2">
                  {explanation.limeData.negative.map((item, idx) => (
                    <span 
                      key={idx}
                      className="px-3 py-1 bg-destructive/10 text-destructive border border-destructive/30 rounded-full text-xs font-medium"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            {/* LIME Visualization Placeholder */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold mb-3">LIME Local Explanation</h3>
              <div className="bg-muted/20 border border-border rounded-lg p-6 h-48 flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-3">
                    <Brain className="w-8 h-8 text-primary" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    LIME visualization showing layer-by-layer contribution
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    (Mock visualization - actual implementation would show detailed layer analysis)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="data-card h-96 flex items-center justify-center">
          <div className="text-center">
            <Brain className="w-16 h-16 text-muted-foreground/40 mx-auto mb-4" />
            <p className="text-muted-foreground mb-2">No explanation generated yet</p>
            <p className="text-sm text-muted-foreground">Enter a model ID and click "Generate Explanation" to start</p>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="data-card bg-gradient-to-br from-primary/5 to-transparent border-primary/20">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Info size={16} className="text-primary" />
            What is SHAP?
          </h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            SHAP (SHapley Additive exPlanations) is a unified approach to explain the output of any machine learning model. 
            It connects optimal credit allocation with local explanations using Shapley values from game theory.
          </p>
        </div>
        
        <div className="data-card bg-gradient-to-br from-accent-2/5 to-transparent border-accent-2/20">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Info size={16} className="text-accent-2" />
            What is LIME?
          </h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            LIME (Local Interpretable Model-agnostic Explanations) explains individual predictions by approximating 
            the model locally with an interpretable model, helping understand feature contributions at the instance level.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ExplainPage;