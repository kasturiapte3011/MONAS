// Mock data and API simulation for MONAS

const delay = (min = 300, max = 900) => 
  new Promise(resolve => setTimeout(resolve, Math.random() * (max - min) + min));

const generateId = () => Math.random().toString(36).substr(2, 9);

// Generate mock population data
export const generatePopulation = async (config) => {
  await delay(500, 1200);
  
  const { populationSize = 50 } = config;
  const population = [];
  
  for (let i = 0; i < populationSize; i++) {
    population.push({
      id: generateId(),
      modelId: `model_${i + 1}`,
      nodes: Math.floor(Math.random() * 20) + 10,
      edges: Math.floor(Math.random() * 30) + 15,
      layers: Math.floor(Math.random() * 10) + 5,
      fitness: (Math.random() * 0.4 + 0.6).toFixed(4),
      accuracy: (Math.random() * 0.15 + 0.85).toFixed(3),
      flops: (Math.random() * 500 + 100).toFixed(2) + 'M',
      params: (Math.random() * 10 + 1).toFixed(2) + 'M',
      latency: (Math.random() * 50 + 10).toFixed(1) + 'ms',
      generation: Math.floor(Math.random() * 10),
      architecture: {
        cells: Math.floor(Math.random() * 5) + 3,
        operations: ['conv3x3', 'conv5x5', 'maxpool', 'avgpool', 'skip'],
        connections: Array(5).fill(0).map(() => ({
          from: Math.floor(Math.random() * 10),
          to: Math.floor(Math.random() * 10),
          operation: ['conv3x3', 'conv5x5', 'maxpool'][Math.floor(Math.random() * 3)]
        }))
      }
    });
  }
  
  return population;
};

export const fetchPopulation = async () => {
  return await generatePopulation({ populationSize: 50 });
};

// Run genetic algorithm search
export const runSearch = async (config) => {
  await delay(1000, 2000);
  
  const logs = [];
  const { generations = 10, populationSize = 50 } = config;
  
  logs.push(`[INFO] Initializing population with ${populationSize} individuals...`);
  logs.push(`[INFO] Starting search for ${generations} generations...`);
  logs.push(`[INFO] Mutation rate: ${config.mutationRate}, Crossover rate: ${config.crossoverRate}`);
  
  for (let gen = 1; gen <= Math.min(5, generations); gen++) {
    await delay(200, 400);
    logs.push(`[GEN ${gen}] Evaluating population...`);
    logs.push(`[GEN ${gen}] Best fitness: ${(Math.random() * 0.2 + 0.8).toFixed(4)}`);
    logs.push(`[GEN ${gen}] Average fitness: ${(Math.random() * 0.2 + 0.6).toFixed(4)}`);
  }
  
  logs.push(`[INFO] Search completed successfully!`);
  logs.push(`[INFO] Best model found with accuracy: ${(Math.random() * 0.05 + 0.95).toFixed(3)}`);
  
  return { logs, success: true };
};

// Fetch Pareto front data
export const fetchPareto = async () => {
  await delay(400, 800);
  
  const paretoData = [];
  
  for (let i = 0; i < 30; i++) {
    const accuracy = 0.85 + Math.random() * 0.14;
    const flops = 100 + Math.random() * 400;
    const params = 1 + Math.random() * 9;
    
    paretoData.push({
      id: generateId(),
      modelId: `model_${i + 1}`,
      accuracy: accuracy.toFixed(3),
      flops: flops.toFixed(2),
      params: params.toFixed(2),
      latency: (flops / 10 + Math.random() * 10).toFixed(1),
      isPareto: Math.random() > 0.5
    });
  }
  
  return paretoData;
};

// Generate explanation data
export const generateExplanation = async (modelId) => {
  await delay(600, 1000);
  
  const features = [
    { name: 'Depth', importance: Math.random() * 0.3 + 0.2 },
    { name: 'Width', importance: Math.random() * 0.25 + 0.15 },
    { name: 'Skip Connections', importance: Math.random() * 0.2 + 0.15 },
    { name: 'Conv Kernel Size', importance: Math.random() * 0.2 + 0.1 },
    { name: 'Pooling Strategy', importance: Math.random() * 0.15 + 0.08 },
    { name: 'Activation Function', importance: Math.random() * 0.1 + 0.05 },
    { name: 'Batch Normalization', importance: Math.random() * 0.12 + 0.04 },
  ];
  
  // Normalize importance values
  const total = features.reduce((sum, f) => sum + f.importance, 0);
  features.forEach(f => f.importance = (f.importance / total));
  
  // Sort by importance
  features.sort((a, b) => b.importance - a.importance);
  
  return {
    modelId,
    features,
    method: 'SHAP',
    explanation: `This model achieves high accuracy through optimal depth-width balance and strategic use of skip connections. The architecture demonstrates efficient feature extraction with minimal parameter overhead.`,
    limeData: {
      positive: ['deep_layers', 'skip_connections', 'efficient_kernels'],
      negative: ['excessive_width', 'redundant_pooling'],
    }
  };
};

// Model Advisor suggestion engine
export const advisorSuggest = async (params) => {
  await delay(800, 1500);
  
  const { taskType, datasetSize, priority, targetHardware } = params;
  
  // Simple rule-based mapping
  let baseArchitecture = 'MobileNetV3';
  let modifications = [];
  let dataStrategy = [];
  let trainingRecipe = {};
  let compression = [];
  let deployment = {};
  
  // Base architecture selection
  if (targetHardware === 'Mobile (ARM)' || targetHardware === 'Raspberry Pi') {
    baseArchitecture = 'EfficientNet-lite';
  } else if (targetHardware === 'Edge CPU') {
    baseArchitecture = 'MobileNetV3';
  } else if (targetHardware === 'Cloud GPU') {
    if (taskType === 'NLP (text)') {
      baseArchitecture = 'BERT-tiny';
    } else {
      baseArchitecture = 'ResNet50';
    }
  }
  
  // Modifications based on priorities
  if (priority.accuracy > priority.latency) {
    modifications.push('Increase depth by 20%');
    modifications.push('Use larger kernel sizes (5x5 instead of 3x3)');
  } else {
    modifications.push('Reduce depth, increase width');
    modifications.push('Use depthwise separable convolutions');
    modifications.push('Implement early exit layers');
  }
  
  // Data strategy
  if (datasetSize === 'Small (<10k)') {
    dataStrategy.push('Use transfer learning with ImageNet pretrained weights');
    dataStrategy.push('Aggressive data augmentation (rotation, flip, color jitter)');
    dataStrategy.push('Consider few-shot learning approaches');
  } else if (datasetSize === 'Medium (10k-100k)') {
    dataStrategy.push('Fine-tune with moderate augmentation');
    dataStrategy.push('Use mixup/cutmix for regularization');
  } else {
    dataStrategy.push('Train from scratch with standard augmentation');
    dataStrategy.push('Implement progressive resizing');
  }
  
  // Training recipe
  trainingRecipe = {
    epochs: datasetSize === 'Small (<10k)' ? '50-100' : datasetSize === 'Medium (10k-100k)' ? '30-50' : '20-30',
    batchSize: targetHardware === 'Cloud GPU' ? '64-128' : '16-32',
    learningRate: '1e-3 with cosine annealing',
    optimizer: 'AdamW',
    schedule: 'Warmup for 5% of steps, then cosine decay'
  };
  
  // Compression options
  if (priority.size > 0.5 || targetHardware !== 'Cloud GPU') {
    compression.push({
      technique: 'Quantization',
      description: 'INT8 post-training quantization',
      impact: '-50% model size, -2% accuracy, +30% speed'
    });
    compression.push({
      technique: 'Pruning',
      description: 'Structured pruning with 30% sparsity',
      impact: '-30% parameters, -1% accuracy, +15% speed'
    });
  }
  
  if (datasetSize === 'Large (>100k)') {
    compression.push({
      technique: 'Knowledge Distillation',
      description: 'Distill from larger teacher model',
      impact: '-40% parameters, -1.5% accuracy vs teacher'
    });
  }
  
  // Deployment
  deployment = {
    runtime: targetHardware === 'Cloud GPU' ? 'TorchScript or ONNX' : 'TFLite or ONNX Runtime',
    batchSize: targetHardware === 'Cloud GPU' ? '32-64' : '1',
    estimatedLatency: priority.latency > priority.accuracy ? '< 50ms' : '50-150ms'
  };
  
  return {
    baseArchitecture,
    modifications,
    dataStrategy,
    trainingRecipe,
    compression,
    deployment,
    confidence: 0.85 + Math.random() * 0.1,
    justification: `Based on your ${targetHardware} target and ${datasetSize} dataset, ${baseArchitecture} offers the best accuracy-efficiency tradeoff. The suggested modifications optimize for your stated priorities while maintaining deployability.`
  };
};

// Activity log for home page
let activityLog = [
  { id: 1, action: 'System initialized', timestamp: new Date(Date.now() - 3600000).toISOString(), type: 'info' },
  { id: 2, action: 'Default population loaded', timestamp: new Date(Date.now() - 1800000).toISOString(), type: 'info' },
];

export const getActivityLog = () => [...activityLog];

export const addActivity = (action, type = 'info') => {
  activityLog.push({
    id: activityLog.length + 1,
    action,
    timestamp: new Date().toISOString(),
    type
  });
  
  // Keep only last 20 activities
  if (activityLog.length > 20) {
    activityLog = activityLog.slice(-20);
  }
};

// KPI data for home page
let kpiData = {
  bestAccuracy: 0.952,
  bestTradeoff: { accuracy: 0.918, flops: 156.2 },
  currentGeneration: 8,
  totalEvaluations: 427
};

export const getKPIs = () => ({ ...kpiData });

export const updateKPIs = (updates) => {
  kpiData = { ...kpiData, ...updates };
};