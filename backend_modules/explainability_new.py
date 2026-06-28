"""Explainability for MONAS using real SHAP and LIME."""

from __future__ import annotations

import json
import hashlib
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Try importing SHAP and LIME; fallback to surrogate if unavailable
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    warnings.warn("SHAP not installed. Using surrogate explanations.")

try:
    import lime
    import lime.lime_tabular
    HAS_LIME = True
except ImportError:
    HAS_LIME = False
    warnings.warn("LIME not installed. Using surrogate explanations.")

try:
    import sklearn.ensemble
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ============================================================================
# Surrogate Model: Simple RandomForest trained on architecture features
# ============================================================================

class ArchitectureSurrogateModel:
    """Lightweight surrogate model predicting accuracy from architecture features."""
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.scaler = None
        self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize with default synthetic training data for demo purposes."""
        if not HAS_SKLEARN:
            self.model = None
            return
        
        # Synthetic training data: 100 random architectures with synthetic metrics
        np.random.seed(42)
        n_samples = 100
        
        X = np.random.rand(n_samples, 7) * np.array([
            20,      # depth: 0-20
            500,     # avg_width: 0-500
            10,      # skip_count: 0-10
            10,      # large_kernel_count: 0-10
            10,      # pool_count: 0-10
            10,      # sep_count: 0-10
            10,      # activation_count: 0-10
        ])
        
        # Simple heuristic: accuracy ~ depth + width/500 + skip*0.02 - noise
        y = (
            0.5 +
            X[:, 0] * 0.02 +          # depth contribution
            (X[:, 1] / 500) * 0.15 +  # width contribution
            X[:, 2] * 0.01 +          # skip connections
            X[:, 3] * 0.005 +         # large kernels
            X[:, 5] * 0.01 +          # sep operations
            np.random.randn(n_samples) * 0.05  # noise
        )
        y = np.clip(y, 0.3, 0.95)  # Clip to valid accuracy range
        
        self.feature_names = [
            "depth", "avg_width", "skip_count", 
            "large_kernel_count", "pool_count", "sep_count", "activation_count"
        ]
        
        self.model = sklearn.ensemble.RandomForestRegressor(
            n_estimators=50, max_depth=8, random_state=42
        )
        self.model.fit(X, y)
    
    def extract_features(self, model: Dict[str, Any]) -> np.ndarray:
        """Extract architectural features from model dict."""
        if not model:
            return np.zeros(7)
        
        architecture = model.get("architecture", {})
        metrics = model.get("metrics", {})
        layers = architecture.get("layers", [])
        
        depth = len(layers)
        avg_width = sum(int(layer.get("channels", 0)) for layer in layers) / max(1, depth)
        skip_count = sum(1 for conn in architecture.get("connections", []) if conn.get("operation") == "skip")
        ops = [layer.get("op", "") for layer in layers]
        large_kernel_count = sum(1 for op in ops if "5x5" in op or "dil" in op)
        pool_count = sum(1 for op in ops if "pool" in op)
        sep_count = sum(1 for op in ops if "sep" in op or "bottleneck" in op)
        activation_count = sum(1 for layer in layers if layer.get("activation") in {"gelu", "swish"})
        
        return np.array([
            depth, avg_width, skip_count, large_kernel_count, 
            pool_count, sep_count, activation_count
        ]).reshape(1, -1)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict accuracy from feature array."""
        if self.model is None:
            return np.array([0.75])
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """For sklearn-compatible interface (not used for regressor)."""
        return self.predict(X)


# Global surrogate model instance
_SURROGATE_MODEL = ArchitectureSurrogateModel()


# ============================================================================
# SHAP Explainer
# ============================================================================

def _get_shap_explainer():
    """Get or create SHAP explainer."""
    if not HAS_SHAP or _SURROGATE_MODEL.model is None:
        return None
    
    try:
        explainer = shap.KernelExplainer(
            _SURROGATE_MODEL.predict,
            shap.sample(_SURROGATE_MODEL.extract_features(None), 50)
        )
        return explainer
    except Exception as e:
        warnings.warn(f"Failed to initialize SHAP: {e}")
        return None


def _compute_shap_values(
    model: Dict[str, Any], 
    explainer: Any
) -> Optional[Dict[str, float]]:
    """Compute SHAP values for model architecture."""
    if explainer is None:
        return None
    
    try:
        features = _SURROGATE_MODEL.extract_features(model)
        shap_values = explainer.shap_values(features)
        
        # Convert SHAP values to feature importances (absolute values, normalized)
        importances = np.abs(shap_values[0])
        total = np.sum(importances) or 1.0
        normalized = importances / total
        
        feature_dict = {}
        for name, imp in zip(_SURROGATE_MODEL.feature_names, normalized):
            feature_dict[name] = float(imp)
        
        return feature_dict
    except Exception as e:
        warnings.warn(f"SHAP computation failed: {e}")
        return None


# ============================================================================
# LIME Explainer
# ============================================================================

def _compute_lime_values(
    model: Dict[str, Any]
) -> Optional[Dict[str, float]]:
    """Compute LIME feature importances for model architecture."""
    if not HAS_LIME or _SURROGATE_MODEL.model is None:
        return None
    
    try:
        # Create synthetic background data for LIME
        np.random.seed(42)
        n_background = 100
        background_data = np.random.rand(n_background, 7) * np.array([
            20, 500, 10, 10, 10, 10, 10
        ])
        
        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=background_data,
            feature_names=_SURROGATE_MODEL.feature_names,
            mode="regression",
            random_state=42
        )
        
        features = _SURROGATE_MODEL.extract_features(model).ravel()
        exp = explainer.explain_instance(
            data_row=features,
            predict_fn=_SURROGATE_MODEL.predict,
            num_features=len(_SURROGATE_MODEL.feature_names)
        )
        
        # Extract feature weights
        feature_dict = {}
        for name, weight in exp.as_list():
            # Parse LIME's "name <= value" format
            feature_name = name.split(" ")[0].strip()
            feature_dict[feature_name] = abs(weight)
        
        # Normalize
        total = sum(feature_dict.values()) or 1.0
        return {k: v / total for k, v in feature_dict.items()}
    
    except Exception as e:
        warnings.warn(f"LIME computation failed: {e}")
        return None


# ============================================================================
# Fallback Surrogate Implementation
# ============================================================================

def _normalize(features: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Normalize feature importances."""
    total = sum(item["importance"] for item in features) or 1.0
    normalized = [
        {"name": item["name"], "importance": item["importance"] / total} 
        for item in features
    ]
    return sorted(normalized, key=lambda item: item["importance"], reverse=True)


def _compute_surrogate_explanation(
    model_id: str, 
    model: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Fallback surrogate explanation when SHAP/LIME unavailable."""
    if not model:
        features = _normalize([
            {"name": "Depth", "importance": 0.24},
            {"name": "Width", "importance": 0.19},
            {"name": "Skip Connections", "importance": 0.17},
            {"name": "Conv Kernel Size", "importance": 0.14},
            {"name": "Pooling Strategy", "importance": 0.10},
            {"name": "Activation Function", "importance": 0.08},
            {"name": "Batch Normalization", "importance": 0.08},
        ])
        return {
            "modelId": model_id,
            "features": features,
            "method": "Surrogate Rules (SHAP/LIME unavailable)",
            "explanation": (
                "No stored architecture found. Returned baseline search-space explanation."
            ),
            "limeData": {"positive": [], "negative": []},
        }
    
    architecture = model["architecture"]
    metrics = model["metrics"]
    layers = architecture.get("layers", [])
    ops = [layer.get("op", "") for layer in layers]
    depth = len(layers)
    avg_width = sum(int(layer.get("channels", 0)) for layer in layers) / max(1, depth)
    skip_count = sum(1 for conn in architecture.get("connections", []) if conn.get("operation") == "skip")
    sep_count = sum(1 for op in ops if "sep" in op or "bottleneck" in op)
    pool_count = sum(1 for op in ops if "pool" in op)
    large_kernel_count = sum(1 for op in ops if "5x5" in op or "dil" in op)
    activation_count = sum(1 for layer in layers if layer.get("activation") in {"gelu", "swish"})

    features = _normalize([
        {"name": "Depth", "importance": 0.12 + min(0.18, depth * 0.012)},
        {"name": "Width", "importance": 0.10 + min(0.18, avg_width / 800.0)},
        {"name": "Skip Connections", "importance": 0.08 + min(0.18, skip_count * 0.035)},
        {"name": "Conv Kernel Size", "importance": 0.07 + min(0.14, large_kernel_count * 0.025)},
        {"name": "Pooling Strategy", "importance": 0.05 + min(0.12, pool_count * 0.03)},
        {"name": "Efficient Operations", "importance": 0.07 + min(0.16, sep_count * 0.022)},
        {"name": "Activation Function", "importance": 0.04 + min(0.08, activation_count * 0.012)},
    ])

    positive = []
    negative = []
    if depth >= 8:
        positive.append("sufficient_depth")
    else:
        negative.append("shallow_feature_hierarchy")
    if skip_count:
        positive.append("skip_connections")
    if sep_count >= max(1, depth // 3):
        positive.append("efficient_kernels")
    if metrics.get("params", 0) > 20:
        negative.append("large_parameter_budget")
    if metrics.get("latency", 0) > 80:
        negative.append("latency_pressure")
    if large_kernel_count > depth // 2:
        negative.append("many_large_kernels")
    if not negative:
        negative.append("minor_compute_overhead")

    explanation = (
        f"{model_id} reaches {metrics.get('accuracy', 0) * 100:.1f}% estimated accuracy with "
        f"{metrics.get('flops', 0):.1f}M FLOPs and {metrics.get('params', 0):.2f}M parameters."
    )

    return {
        "modelId": model_id,
        "features": features,
        "method": "Surrogate Rules",
        "explanation": explanation,
        "limeData": {"positive": positive, "negative": negative},
    }


# ============================================================================
# Main Explainability Function
# ============================================================================

def explain_model(
    model_id: str, 
    model: Optional[Dict[str, Any]] = None, 
    explain_type: str = "global"
) -> Dict[str, Any]:
    """
    Explain model architecture using real SHAP/LIME or fall back to surrogate rules.
    
    Args:
        model_id: Unique model identifier
        model: Architecture dict with 'architecture' and 'metrics' keys
        explain_type: 'global' or 'instance' explanation mode
    
    Returns:
        Dict with features, explanation, LIME tags, and method used
    """
    start_time = time.time()
    
    # Try real SHAP/LIME if available and model provided
    if model and (HAS_SHAP or HAS_LIME):
        try:
            shap_explainer = _get_shap_explainer() if HAS_SHAP else None
            features_dict = {}
            method_used = []
            
            # Compute SHAP
            if shap_explainer:
                shap_values = _compute_shap_values(model, shap_explainer)
                if shap_values:
                    features_dict.update(shap_values)
                    method_used.append("SHAP")
            
            # Compute LIME
            if HAS_LIME:
                lime_values = _compute_lime_values(model)
                if lime_values and not features_dict:  # Use LIME if SHAP failed
                    features_dict.update(lime_values)
                    method_used.append("LIME")
            
            # If either method succeeded, format and return
            if features_dict:
                features = [
                    {"name": name, "importance": imp}
                    for name, imp in sorted(
                        features_dict.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )
                ]
                
                explanation = (
                    f"{model_id}: {model.get('metrics', {}).get('accuracy', 0) * 100:.1f}% accuracy. "
                    f"Top factors: {', '.join([f['name'] for f in features[:3]])}."
                )
                
                elapsed = time.time() - start_time
                
                return {
                    "modelId": model_id,
                    "features": features,
                    "method": " + ".join(method_used) if method_used else "Surrogate",
                    "explanation": explanation,
                    "limeData": {"positive": [], "negative": []},
                    "computationTimeMs": elapsed * 1000,
                }
        
        except Exception as e:
            warnings.warn(f"Real explainability failed, falling back to surrogate: {e}")
    
    # Fall back to surrogate
    elapsed = time.time() - start_time
    result = _compute_surrogate_explanation(model_id, model)
    result["computationTimeMs"] = elapsed * 1000
    return result