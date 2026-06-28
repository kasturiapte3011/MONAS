// Backend API adapter for MONAS.

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000/api';

const defaultKPIs = {
  bestAccuracy: 0,
  bestTradeoff: { accuracy: 0, flops: 0 },
  currentGeneration: 0,
  totalEvaluations: 0
};

let kpiData = { ...defaultKPIs };
let activityLog = [
  { id: 1, action: 'Frontend loaded', timestamp: new Date().toISOString(), type: 'info' },
];

const numberOrDefault = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeConfig = (config = {}) => ({
  populationSize: numberOrDefault(config.populationSize, 50),
  mutationRate: numberOrDefault(config.mutationRate, 0.1),
  crossoverRate: numberOrDefault(config.crossoverRate, 0.7),
  generations: numberOrDefault(config.generations, 10),
  objective: config.objective || 'balanced',
  hardware: config.hardware || config.targetHardware || 'gpu',
  seed: config.seed ?? 7,
  maxParams: config.maxParams || null,
  maxFlops: config.maxFlops || null,
  maxLatency: config.maxLatency || null,
});

const request = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof body === 'string' ? body : body.detail || 'Backend request failed';
    throw new Error(message);
  }

  return body;
};

const mergeActivity = (remoteActivities = []) => {
  const byKey = new Map();

  [...activityLog, ...remoteActivities].forEach((item) => {
    const key = `${item.timestamp}-${item.action}-${item.type}`;
    byKey.set(key, item);
  });

  activityLog = Array.from(byKey.values())
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-20);

  return [...activityLog];
};

export const initializePopulation = async (config) => {
  const result = await request('/initialize', {
    method: 'POST',
    body: JSON.stringify(normalizeConfig(config)),
  });

  if (result.kpis) {
    kpiData = result.kpis;
  }

  return result;
};

export const generatePopulation = async (config) => {
  const result = await initializePopulation(config);
  return result.population || [];
};

export const fetchPopulation = async () => {
  return await request('/population');
};

export const runSearch = async (config) => {
  const result = await request('/search', {
    method: 'POST',
    body: JSON.stringify(normalizeConfig(config)),
  });

  if (result.kpis) {
    kpiData = result.kpis;
  }

  return result;
};

export const fetchPareto = async () => {
  return await request('/pareto');
};

export const generateExplanation = async (modelId, explainType = 'global') => {
  return await request('/explain', {
    method: 'POST',
    body: JSON.stringify({ modelId, explainType }),
  });
};

export const advisorSuggest = async (params) => {
  return await request('/advisor', {
    method: 'POST',
    body: JSON.stringify(params),
  });
};

export const fetchModelCode = async (modelId) => {
  return await request(`/models/${encodeURIComponent(modelId)}/code`, {
    headers: { Accept: 'text/plain' },
  });
};

export const fetchKPIs = async () => {
  kpiData = await request('/kpis');
  return { ...kpiData };
};

export const getKPIs = () => ({ ...kpiData });

export const updateKPIs = (updates) => {
  kpiData = { ...kpiData, ...updates };
};

export const fetchActivityLog = async () => {
  const remoteActivities = await request('/activity');
  return mergeActivity(remoteActivities);
};

export const getActivityLog = () => [...activityLog];

export const addActivity = (action, type = 'info') => {
  activityLog.push({
    id: `local-${Date.now()}`,
    action,
    timestamp: new Date().toISOString(),
    type,
  });

  if (activityLog.length > 20) {
    activityLog = activityLog.slice(-20);
  }
};

export const getApiBaseUrl = () => API_BASE_URL;
