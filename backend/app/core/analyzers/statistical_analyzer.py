"""
Statistical Analyzer - Advanced statistical analysis
Performs hypothesis testing, distribution analysis, and statistical inference
"""
#backend/app/core/analyzers/statistical_analyzer.py

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


@dataclass
class DistributionTest:
    """Results from distribution testing"""
    test_name: str
    statistic: float
    p_value: float
    is_normal: bool
    conclusion: str


@dataclass
class CorrelationAnalysis:
    """Correlation analysis results"""
    method: str  # pearson, spearman, kendall
    matrix: pd.DataFrame
    significant_pairs: List[Tuple[str, str, float, float]]  # (col1, col2, corr, p_value)


@dataclass
class OutlierAnalysis:
    """Outlier detection results"""
    method: str
    outliers: Dict[str, List[int]]  # column -> list of outlier indices
    outlier_counts: Dict[str, int]
    outlier_percentages: Dict[str, float]


@dataclass
class StatisticalResult:
    """Complete statistical analysis result"""
    # Distribution tests
    distribution_tests: Dict[str, DistributionTest]
    
    # Correlations
    correlation_analysis: Optional[CorrelationAnalysis]
    
    # Outliers
    outlier_analysis: Optional[OutlierAnalysis]
    
    # Variance analysis
    variance_tests: Dict[str, Any]
    
    # Summary statistics
    summary_stats: pd.DataFrame
    
    # Warnings and notes
    warnings: List[str] = field(default_factory=list)


class StatisticalAnalyzer:
    """Perform advanced statistical analysis on DataFrames"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Significance level
        self.alpha = 0.05
        
        # Outlier detection thresholds
        self.iqr_multiplier = 1.5
        self.z_score_threshold = 3
    
    def analyze(self, df: pd.DataFrame) -> StatisticalResult:
        """
        Perform complete statistical analysis
        
        Args:
            df: pandas DataFrame
        
        Returns:
            StatisticalResult with all analyses
        """
        self.logger.info(f"Performing statistical analysis on DataFrame")
        
        warnings = []
        
        # Summary statistics
        summary_stats = self._calculate_summary_stats(df)
        
        # Distribution tests (for numeric columns)
        distribution_tests = self._test_distributions(df)
        
        # Correlation analysis
        correlation_analysis = self._analyze_correlations(df)
        
        # Outlier detection
        outlier_analysis = self._detect_outliers(df)
        
        # Variance tests
        variance_tests = self._test_variances(df)
        
        return StatisticalResult(
            distribution_tests=distribution_tests,
            correlation_analysis=correlation_analysis,
            outlier_analysis=outlier_analysis,
            variance_tests=variance_tests,
            summary_stats=summary_stats,
            warnings=warnings
        )
    
    def _calculate_summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive summary statistics
        
        Args:
            df: pandas DataFrame
        
        Returns:
            DataFrame with summary statistics
        """
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return pd.DataFrame()
        
        # Basic statistics
        summary = numeric_df.describe().T
        
        # Add additional statistics
        summary['skewness'] = numeric_df.skew()
        summary['kurtosis'] = numeric_df.kurtosis()
        summary['variance'] = numeric_df.var()
        summary['range'] = numeric_df.max() - numeric_df.min()
        summary['iqr'] = numeric_df.quantile(0.75) - numeric_df.quantile(0.25)
        summary['cv'] = (numeric_df.std() / numeric_df.mean()).abs()  # Coefficient of variation
        
        return summary
    
    def _test_distributions(self, df: pd.DataFrame) -> Dict[str, DistributionTest]:
        """
        Test if numeric columns follow normal distribution
        
        Args:
            df: pandas DataFrame
        
        Returns:
            Dictionary of distribution test results
        """
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            
            if len(data) < 8:  # Need at least 8 samples for Shapiro-Wilk
                continue
            
            try:
                # Shapiro-Wilk test for normality
                statistic, p_value = stats.shapiro(data)
                
                is_normal = p_value > self.alpha
                
                conclusion = (
                    f"Data appears normally distributed (p={p_value:.4f})"
                    if is_normal
                    else f"Data does not appear normally distributed (p={p_value:.4f})"
                )
                
                results[col] = DistributionTest(
                    test_name="Shapiro-Wilk",
                    statistic=float(statistic),
                    p_value=float(p_value),
                    is_normal=is_normal,
                    conclusion=conclusion
                )
            
            except Exception as e:
                self.logger.warning(f"Could not test distribution for {col}: {str(e)}")
        
        return results
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Optional[CorrelationAnalysis]:
        """
        Perform correlation analysis with significance testing
        
        Args:
            df: pandas DataFrame
        
        Returns:
            CorrelationAnalysis or None
        """
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return None
        
        try:
            # Calculate Pearson correlation
            corr_matrix = numeric_df.corr(method='pearson')
            
            # Find significant correlations
            significant_pairs = []
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr = corr_matrix.iloc[i, j]
                    
                    # Calculate p-value for correlation
                    data1 = numeric_df[col1].dropna()
                    data2 = numeric_df[col2].dropna()
                    
                    # Get common indices
                    common_idx = data1.index.intersection(data2.index)
                    if len(common_idx) < 3:
                        continue
                    
                    try:
                        _, p_value = stats.pearsonr(
                            numeric_df.loc[common_idx, col1],
                            numeric_df.loc[common_idx, col2]
                        )
                        
                        # Store if significant
                        if p_value < self.alpha and abs(corr) > 0.3:
                            significant_pairs.append((col1, col2, float(corr), float(p_value)))
                    except:
                        continue
            
            return CorrelationAnalysis(
                method='pearson',
                matrix=corr_matrix,
                significant_pairs=significant_pairs
            )
        
        except Exception as e:
            self.logger.error(f"Error in correlation analysis: {str(e)}")
            return None
    
    def _detect_outliers(self, df: pd.DataFrame) -> Optional[OutlierAnalysis]:
        """
        Detect outliers using IQR and Z-score methods
        
        Args:
            df: pandas DataFrame
        
        Returns:
            OutlierAnalysis or None
        """
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return None
        
        outliers = {}
        outlier_counts = {}
        outlier_percentages = {}
        
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            
            if len(data) == 0:
                continue
            
            # IQR method
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            
            # Find outlier indices
            outlier_mask = (data < lower_bound) | (data > upper_bound)
            outlier_indices = data[outlier_mask].index.tolist()
            
            if outlier_indices:
                outliers[col] = outlier_indices
                outlier_counts[col] = len(outlier_indices)
                outlier_percentages[col] = round(
                    (len(outlier_indices) / len(data)) * 100, 2
                )
        
        return OutlierAnalysis(
            method='IQR',
            outliers=outliers,
            outlier_counts=outlier_counts,
            outlier_percentages=outlier_percentages
        )
    
    def _test_variances(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Test equality of variances (homoscedasticity)
        
        Args:
            df: pandas DataFrame
        
        Returns:
            Dictionary with variance test results
        """
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return results
        
        try:
            # Levene's test for equal variances
            data_arrays = [df[col].dropna().values for col in numeric_cols]
            
            # Filter out empty arrays
            data_arrays = [arr for arr in data_arrays if len(arr) > 0]
            
            if len(data_arrays) >= 2:
                statistic, p_value = stats.levene(*data_arrays)
                
                results['levene_test'] = {
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'equal_variances': p_value > self.alpha,
                    'conclusion': (
                        "Variances are approximately equal"
                        if p_value > self.alpha
                        else "Variances are significantly different"
                    )
                }
        
        except Exception as e:
            self.logger.warning(f"Could not perform variance tests: {str(e)}")
        
        return results
    
    def compare_groups(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str
    ) -> Dict[str, Any]:
        """
        Compare groups using appropriate statistical tests
        
        Args:
            df: pandas DataFrame
            group_col: Column containing group labels
            value_col: Column containing values to compare
        
        Returns:
            Dictionary with comparison results
        """
        results = {}
        
        try:
            # Get unique groups
            groups = df[group_col].unique()
            
            if len(groups) < 2:
                return {'error': 'Need at least 2 groups for comparison'}
            
            # Get data for each group
            group_data = [df[df[group_col] == group][value_col].dropna() for group in groups]
            
            # Filter out empty groups
            group_data = [data for data in group_data if len(data) > 0]
            
            if len(group_data) < 2:
                return {'error': 'Not enough data in groups'}
            
            # Two groups: t-test
            if len(group_data) == 2:
                # Check for normality
                normal_tests = [stats.shapiro(data) for data in group_data if len(data) >= 8]
                all_normal = all(p > self.alpha for _, p in normal_tests)
                
                if all_normal:
                    # Independent t-test
                    statistic, p_value = stats.ttest_ind(group_data[0], group_data[1])
                    test_name = "Independent t-test"
                else:
                    # Mann-Whitney U test (non-parametric)
                    statistic, p_value = stats.mannwhitneyu(group_data[0], group_data[1])
                    test_name = "Mann-Whitney U test"
                
                results = {
                    'test': test_name,
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'significant': p_value < self.alpha,
                    'conclusion': (
                        f"Groups are significantly different (p={p_value:.4f})"
                        if p_value < self.alpha
                        else f"No significant difference between groups (p={p_value:.4f})"
                    )
                }
            
            # More than two groups: ANOVA or Kruskal-Wallis
            else:
                # Check for normality
                normal_tests = [stats.shapiro(data) for data in group_data if len(data) >= 8]
                all_normal = all(p > self.alpha for _, p in normal_tests)
                
                if all_normal:
                    # One-way ANOVA
                    statistic, p_value = stats.f_oneway(*group_data)
                    test_name = "One-way ANOVA"
                else:
                    # Kruskal-Wallis H-test (non-parametric)
                    statistic, p_value = stats.kruskal(*group_data)
                    test_name = "Kruskal-Wallis H-test"
                
                results = {
                    'test': test_name,
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'significant': p_value < self.alpha,
                    'conclusion': (
                        f"At least one group is significantly different (p={p_value:.4f})"
                        if p_value < self.alpha
                        else f"No significant difference among groups (p={p_value:.4f})"
                    )
                }
        
        except Exception as e:
            self.logger.error(f"Error comparing groups: {str(e)}")
            results = {'error': str(e)}
        
        return results
    
    def test_independence(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str
    ) -> Dict[str, Any]:
        """
        Test independence between two categorical variables using Chi-square test
        
        Args:
            df: pandas DataFrame
            col1: First categorical column
            col2: Second categorical column
        
        Returns:
            Dictionary with test results
        """
        try:
            # Create contingency table
            contingency_table = pd.crosstab(df[col1], df[col2])
            
            # Perform Chi-square test
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            return {
                'test': 'Chi-square test of independence',
                'chi2_statistic': float(chi2),
                'p_value': float(p_value),
                'degrees_of_freedom': int(dof),
                'independent': p_value > self.alpha,
                'conclusion': (
                    f"Variables are independent (p={p_value:.4f})"
                    if p_value > self.alpha
                    else f"Variables are dependent (p={p_value:.4f})"
                )
            }
        
        except Exception as e:
            self.logger.error(f"Error testing independence: {str(e)}")
            return {'error': str(e)}
    
    def calculate_confidence_interval(
        self,
        df: pd.DataFrame,
        column: str,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate confidence interval for a column mean
        
        Args:
            df: pandas DataFrame
            column: Column name
            confidence: Confidence level (default: 0.95)
        
        Returns:
            Dictionary with confidence interval
        """
        try:
            data = df[column].dropna()
            
            if len(data) == 0:
                return {'error': 'No data available'}
            
            mean = data.mean()
            se = stats.sem(data)
            ci = stats.t.interval(
                confidence,
                len(data) - 1,
                loc=mean,
                scale=se
            )
            
            return {
                'mean': float(mean),
                'confidence_level': confidence,
                'lower_bound': float(ci[0]),
                'upper_bound': float(ci[1]),
                'margin_of_error': float(ci[1] - mean),
                'sample_size': len(data)
            }
        
        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {str(e)}")
            return {'error': str(e)}