"""
Clustering Analyzer - Automated clustering and segmentation
Provides K-means, DBSCAN, and hierarchical clustering with automatic optimization
"""
#backend/app/core/ai/clustering_analyzer.py

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClusterConfig:
    """Configuration for clustering"""
    method: str = "auto"  # auto, kmeans, dbscan, hierarchical
    n_clusters: Optional[int] = None  # For kmeans (auto-detect if None)
    max_clusters: int = 10  # Maximum clusters to try
    eps: float = 0.5  # DBSCAN epsilon
    min_samples: int = 5  # DBSCAN minimum samples
    random_state: int = 42  # For reproducibility
    scale_features: bool = True  # Standardize features
    pca_components: Optional[int] = None  # Reduce dimensions (None = auto)


@dataclass
class ClusterResult:
    """Results from clustering analysis"""
    labels: np.ndarray  # Cluster labels for each sample
    n_clusters: int  # Number of clusters found
    method: str  # Method used
    cluster_centers: Optional[np.ndarray]  # Cluster centers (kmeans only)
    cluster_profiles: Dict[int, Dict[str, Any]]  # Profile for each cluster
    metrics: Dict[str, float]  # Quality metrics (silhouette, etc.)
    feature_importance: Dict[str, float]  # Feature importance per cluster
    pca_explained_variance: Optional[float] = None  # If PCA was used
    warnings: List[str] = field(default_factory=list)


class ClusteringAnalyzer:
    """Automated clustering and segmentation analysis"""
    
    def __init__(self):
        """Initialize clustering analyzer"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._check_sklearn_available()
    
    def _check_sklearn_available(self):
        """Check if scikit-learn is installed"""
        try:
            import sklearn
            self.sklearn_available = True
            self.logger.info("scikit-learn library is available")
        except ImportError:
            self.sklearn_available = False
            self.logger.warning(
                "scikit-learn library not installed. "
                "Install with: pip install scikit-learn"
            )
    
    def auto_cluster(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        config: Optional[ClusterConfig] = None
    ) -> ClusterResult:
        """
        Automatically cluster data using best method
        
        Args:
            df: DataFrame to cluster
            features: Optional list of feature columns (None = all numeric)
            config: Optional clustering configuration
        
        Returns:
            ClusterResult with labels and analysis
        
        Raises:
            ImportError: If scikit-learn is not installed
            ValueError: If data is invalid
        """
        if not self.sklearn_available:
            raise ImportError(
                "scikit-learn library is required for clustering. "
                "Install with: pip install scikit-learn"
            )
        
        config = config or ClusterConfig()
        warnings = []
        
        # Prepare data
        X, feature_names = self._prepare_data(df, features, config.scale_features)
        
        if len(X) < config.min_samples:
            raise ValueError(
                f"Insufficient data for clustering. "
                f"Need at least {config.min_samples} samples, got {len(X)}"
            )
        
        # Apply PCA if needed
        pca_variance = None
        if config.pca_components or X.shape[1] > 10:
            X, pca_variance = self._apply_pca(X, config.pca_components)
            self.logger.info(f"Applied PCA, explained variance: {pca_variance:.2%}")
        
        # Choose method
        if config.method == "auto":
            # Use kmeans for smaller datasets, DBSCAN for larger
            method = "kmeans" if len(X) < 10000 else "dbscan"
        else:
            method = config.method
        
        # Perform clustering
        if method == "kmeans":
            result = self.kmeans_cluster(df, features, config)
        elif method == "dbscan":
            result = self.dbscan_cluster(df, features, config)
        elif method == "hierarchical":
            result = self.hierarchical_cluster(df, features, config)
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        result.pca_explained_variance = pca_variance
        return result
    
    def kmeans_cluster(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        config: Optional[ClusterConfig] = None
    ) -> ClusterResult:
        """
        K-means clustering with elbow method for optimal K
        
        Args:
            df: DataFrame to cluster
            features: Optional feature columns
            config: Optional configuration
        
        Returns:
            ClusterResult
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        
        config = config or ClusterConfig()
        warnings = []
        
        # Prepare data
        X, feature_names = self._prepare_data(df, features, config.scale_features)
        
        # Determine optimal number of clusters
        if config.n_clusters is None:
            optimal_k = self._find_optimal_k(X, config.max_clusters)
            self.logger.info(f"Optimal K determined: {optimal_k}")
        else:
            optimal_k = config.n_clusters
        
        # Fit KMeans
        kmeans = KMeans(
            n_clusters=optimal_k,
            random_state=config.random_state,
            n_init=10
        )
        labels = kmeans.fit_predict(X)
        
        # Calculate metrics
        silhouette = silhouette_score(X, labels) if optimal_k > 1 else 0.0
        inertia = kmeans.inertia_
        
        metrics = {
            "silhouette_score": float(silhouette),
            "inertia": float(inertia),
            "n_samples": len(X)
        }
        
        # Profile clusters
        cluster_profiles = self._profile_clusters(df, labels, feature_names)
        
        # Feature importance (variance between clusters)
        feature_importance = self._calculate_feature_importance(X, labels, feature_names)
        
        # Warnings
        if silhouette < 0.3:
            warnings.append(
                f"Low silhouette score ({silhouette:.2f}). "
                "Clusters may not be well-separated."
            )
        
        return ClusterResult(
            labels=labels,
            n_clusters=optimal_k,
            method="kmeans",
            cluster_centers=kmeans.cluster_centers_,
            cluster_profiles=cluster_profiles,
            metrics=metrics,
            feature_importance=feature_importance,
            warnings=warnings
        )
    
    def dbscan_cluster(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        config: Optional[ClusterConfig] = None
    ) -> ClusterResult:
        """
        DBSCAN clustering for density-based clustering
        
        Args:
            df: DataFrame to cluster
            features: Optional feature columns
            config: Optional configuration
        
        Returns:
            ClusterResult
        """
        from sklearn.cluster import DBSCAN
        from sklearn.metrics import silhouette_score
        
        config = config or ClusterConfig()
        warnings = []
        
        # Prepare data
        X, feature_names = self._prepare_data(df, features, config.scale_features)
        
        # Fit DBSCAN
        dbscan = DBSCAN(
            eps=config.eps,
            min_samples=config.min_samples
        )
        labels = dbscan.fit_predict(X)
        
        # Count clusters (excluding noise points labeled as -1)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        # Calculate metrics
        if n_clusters > 1:
            # Only calculate silhouette for non-noise points
            mask = labels != -1
            if mask.sum() > 0:
                silhouette = silhouette_score(X[mask], labels[mask])
            else:
                silhouette = 0.0
        else:
            silhouette = 0.0
        
        metrics = {
            "silhouette_score": float(silhouette),
            "n_noise_points": n_noise,
            "noise_percentage": (n_noise / len(X)) * 100,
            "n_samples": len(X)
        }
        
        # Profile clusters
        cluster_profiles = self._profile_clusters(df, labels, feature_names)
        
        # Feature importance
        feature_importance = self._calculate_feature_importance(X, labels, feature_names)
        
        # Warnings
        if n_noise > len(X) * 0.3:
            warnings.append(
                f"High noise percentage ({metrics['noise_percentage']:.1f}%). "
                "Consider adjusting eps or min_samples."
            )
        
        if n_clusters == 0:
            warnings.append("No clusters found. Try adjusting parameters.")
        
        return ClusterResult(
            labels=labels,
            n_clusters=n_clusters,
            method="dbscan",
            cluster_centers=None,
            cluster_profiles=cluster_profiles,
            metrics=metrics,
            feature_importance=feature_importance,
            warnings=warnings
        )
    
    def hierarchical_cluster(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        config: Optional[ClusterConfig] = None
    ) -> ClusterResult:
        """
        Hierarchical clustering
        
        Args:
            df: DataFrame to cluster
            features: Optional feature columns
            config: Optional configuration
        
        Returns:
            ClusterResult
        """
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import silhouette_score
        
        config = config or ClusterConfig()
        warnings = []
        
        # Prepare data
        X, feature_names = self._prepare_data(df, features, config.scale_features)
        
        # Determine number of clusters
        if config.n_clusters is None:
            optimal_k = self._find_optimal_k(X, config.max_clusters)
        else:
            optimal_k = config.n_clusters
        
        # Fit hierarchical clustering
        hierarchical = AgglomerativeClustering(n_clusters=optimal_k)
        labels = hierarchical.fit_predict(X)
        
        # Calculate metrics
        silhouette = silhouette_score(X, labels) if optimal_k > 1 else 0.0
        
        metrics = {
            "silhouette_score": float(silhouette),
            "n_samples": len(X)
        }
        
        # Profile clusters
        cluster_profiles = self._profile_clusters(df, labels, feature_names)
        
        # Feature importance
        feature_importance = self._calculate_feature_importance(X, labels, feature_names)
        
        return ClusterResult(
            labels=labels,
            n_clusters=optimal_k,
            method="hierarchical",
            cluster_centers=None,
            cluster_profiles=cluster_profiles,
            metrics=metrics,
            feature_importance=feature_importance,
            warnings=warnings
        )
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]],
        scale: bool
    ) -> Tuple[np.ndarray, List[str]]:
        """Prepare data for clustering"""
        # Select features
        if features is None:
            # Use all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                raise ValueError("No numeric columns found for clustering")
            features = numeric_cols
        
        # Extract data
        X = df[features].values
        
        # Handle missing values
        if np.isnan(X).any():
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy='mean')
            X = imputer.fit_transform(X)
        
        # Scale if requested
        if scale:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
        
        return X, features
    
    def _apply_pca(
        self,
        X: np.ndarray,
        n_components: Optional[int]
    ) -> Tuple[np.ndarray, float]:
        """Apply PCA for dimensionality reduction"""
        from sklearn.decomposition import PCA
        
        if n_components is None:
            # Auto-determine components (95% variance)
            pca = PCA(n_components=0.95)
        else:
            pca = PCA(n_components=n_components)
        
        X_pca = pca.fit_transform(X)
        explained_variance = pca.explained_variance_ratio_.sum()
        
        return X_pca, explained_variance
    
    def _find_optimal_k(
        self,
        X: np.ndarray,
        max_k: int
    ) -> int:
        """Find optimal K using elbow method"""
        from sklearn.cluster import KMeans
        
        inertias = []
        K_range = range(2, min(max_k + 1, len(X)))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Find elbow using rate of change
        if len(inertias) < 2:
            return 2
        
        # Calculate rate of change
        deltas = np.diff(inertias)
        delta_deltas = np.diff(deltas)
        
        # Find elbow (maximum second derivative)
        if len(delta_deltas) > 0:
            elbow_idx = np.argmax(delta_deltas) + 2  # +2 because of double diff
            return min(elbow_idx, max_k)
        
        return 3  # Default
    
    def _profile_clusters(
        self,
        df: pd.DataFrame,
        labels: np.ndarray,
        features: List[str]
    ) -> Dict[int, Dict[str, Any]]:
        """Generate profile for each cluster"""
        profiles = {}
        
        for cluster_id in set(labels):
            if cluster_id == -1:  # Skip noise in DBSCAN
                continue
            
            mask = labels == cluster_id
            cluster_df = df[mask]
            
            profile = {
                "size": int(mask.sum()),
                "percentage": float((mask.sum() / len(df)) * 100),
                "feature_means": {},
                "feature_stds": {}
            }
            
            # Calculate statistics for each feature
            for feature in features:
                if feature in cluster_df.columns:
                    profile["feature_means"][feature] = float(cluster_df[feature].mean())
                    profile["feature_stds"][feature] = float(cluster_df[feature].std())
            
            profiles[int(cluster_id)] = profile
        
        return profiles
    
    def _calculate_feature_importance(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        features: List[str]
    ) -> Dict[str, float]:
        """Calculate feature importance based on variance between clusters"""
        importance = {}
        
        for i, feature in enumerate(features):
            feature_values = X[:, i]
            
            # Calculate variance between clusters
            cluster_means = []
            for cluster_id in set(labels):
                if cluster_id != -1:  # Skip noise
                    mask = labels == cluster_id
                    if mask.sum() > 0:
                        cluster_means.append(feature_values[mask].mean())
            
            if cluster_means:
                # Variance of cluster means
                between_variance = np.var(cluster_means)
                importance[feature] = float(between_variance)
        
        # Normalize to 0-1
        if importance:
            max_importance = max(importance.values())
            if max_importance > 0:
                importance = {k: v / max_importance for k, v in importance.items()}
        
        return importance
