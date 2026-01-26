"""
Query Suggester - Dynamic Query Generation for Visual Analysis
Analyzes dataset structure and generates relevant visualization queries
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QuerySuggestion:
    """Data class for query suggestions"""
    id: int
    query: str
    category: str  # distribution, comparison, trend, correlation, top_n, aggregation
    icon: str  # Lucide icon name
    complexity: str  # basic, intermediate, advanced


class QuerySuggester:
    """Intelligent query suggestion generator"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Icon mapping for categories
        self.category_icons = {
            "distribution": "BarChart3",
            "comparison": "TrendingUp",
            "trend": "LineChart",
            "correlation": "GitBranch",
            "top_n": "Award",
            "aggregation": "Sigma",
            "filtering": "Filter",
            "hierarchical": "Layers",
            "advanced": "Zap"
        }
        
        # Semantic column name patterns to prioritize
        self.priority_patterns = {
            "high": ["revenue", "sales", "profit", "price", "amount", "value", "cost", "income"],
            "medium": ["age", "count", "total", "quantity", "rate", "score", "rating"],
            "low": ["id", "index", "key", "code"]
        }
    
    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze dataset structure for query generation"""
        analysis = {
            "numeric_cols": [],
            "categorical_cols": [],
            "datetime_cols": [],
            "column_priorities": {},
            "interesting_pairs": []
        }
        
        # Classify columns
        for col in df.columns:
            col_lower = col.lower()
            
            # Determine priority
            priority = "medium"
            for level, patterns in self.priority_patterns.items():
                if any(pattern in col_lower for pattern in patterns):
                    priority = level
                    break
            
            # Skip low priority columns (IDs)
            if priority == "low":
                continue
            
            # Classify by type
            if pd.api.types.is_numeric_dtype(df[col]):
                analysis["numeric_cols"].append(col)
                analysis["column_priorities"][col] = priority
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis["datetime_cols"].append(col)
                analysis["column_priorities"][col] = "high"
            else:
                # Check if categorical (low cardinality)
                nunique = df[col].nunique()
                if nunique < len(df) * 0.5:  # Less than 50% unique
                    analysis["categorical_cols"].append(col)
                    analysis["column_priorities"][col] = priority
        
        # Find interesting numeric pairs for correlation
        numeric_cols = analysis["numeric_cols"]
        if len(numeric_cols) >= 2:
            # Prioritize high-priority columns
            high_priority = [c for c in numeric_cols if analysis["column_priorities"].get(c) == "high"]
            if len(high_priority) >= 2:
                analysis["interesting_pairs"].append((high_priority[0], high_priority[1]))
            elif len(high_priority) == 1 and len(numeric_cols) >= 2:
                other = [c for c in numeric_cols if c != high_priority[0]][0]
                analysis["interesting_pairs"].append((high_priority[0], other))
            else:
                analysis["interesting_pairs"].append((numeric_cols[0], numeric_cols[1]))
        
        return analysis
    
    def generate_distribution_queries(self, analysis: Dict[str, Any], count: int = 2) -> List[QuerySuggestion]:
        """Generate distribution queries for numeric columns"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        priorities = analysis["column_priorities"]
        
        # Sort by priority
        sorted_cols = sorted(numeric_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        
        for i, col in enumerate(sorted_cols[:count]):
            queries.append(QuerySuggestion(
                id=len(queries) + 1,
                query=f"Show distribution of {col}",
                category="distribution",
                icon=self.category_icons["distribution"],
                complexity="basic"
            ))
        
        return queries
    
    def generate_comparison_queries(self, analysis: Dict[str, Any], count: int = 4) -> List[QuerySuggestion]:
        """Generate comparison queries (numeric by categorical)"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        categorical_cols = analysis["categorical_cols"]
        priorities = analysis["column_priorities"]
        
        if not numeric_cols or not categorical_cols:
            return queries
        
        # Sort by priority
        sorted_numeric = sorted(numeric_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        sorted_categorical = sorted(categorical_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        
        # Scenario 1: Bar Chart
        if len(sorted_numeric) >= 1 and len(sorted_categorical) >= 1:
            queries.append(QuerySuggestion(
                id=1,
                query=f"Compare total {sorted_numeric[0]} by {sorted_categorical[0]} as a bar chart",
                category="comparison",
                icon=self.category_icons["comparison"],
                complexity="basic"
            ))
            
        # Scenario 2: Donut Chart
        if len(sorted_numeric) >= 1 and len(sorted_categorical) >= 1:
            queries.append(QuerySuggestion(
                id=2,
                query=f"See proportion of {sorted_numeric[0]} across {sorted_categorical[0]} as a donut chart",
                category="comparison",
                icon=self.category_icons["comparison"],
                complexity="intermediate"
            ))
            
        # Scenario 3: Violin Plot
        if len(sorted_numeric) >= 1 and len(sorted_categorical) >= 1:
            queries.append(QuerySuggestion(
                id=3,
                query=f"Examine {sorted_numeric[0]} density across {sorted_categorical[0]} using a violin plot",
                category="distribution",
                icon=self.category_icons["distribution"],
                complexity="advanced"
            ))

        # Scenario 4: Box Plot
        if len(sorted_numeric) >= 1 and len(sorted_categorical) >= 1:
            queries.append(QuerySuggestion(
                id=4,
                query=f"Compare {sorted_numeric[0]} spread by {sorted_categorical[0]} with a box plot",
                category="distribution",
                icon=self.category_icons["distribution"],
                complexity="intermediate"
            ))
        
        return queries[:count]
    
    def generate_trend_queries(self, analysis: Dict[str, Any], count: int = 2) -> List[QuerySuggestion]:
        """Generate trend queries (numeric over time)"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        datetime_cols = analysis["datetime_cols"]
        priorities = analysis["column_priorities"]
        
        if not datetime_cols or not numeric_cols:
            return queries
        
        # Sort numeric by priority
        sorted_numeric = sorted(numeric_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        
        datetime_col = datetime_cols[0]
        
        # Scenario 1: Line Chart
        queries.append(QuerySuggestion(
            id=1,
            query=f"Track {sorted_numeric[0]} trends over time with a line chart",
            category="trend",
            icon=self.category_icons["trend"],
            complexity="intermediate"
        ))
        
        # Scenario 2: Area Chart
        if len(sorted_numeric) > 0:
            queries.append(QuerySuggestion(
                id=2,
                query=f"Visualize cumulative {sorted_numeric[0]} growth as an area chart",
                category="trend",
                icon=self.category_icons["trend"],
                complexity="intermediate"
            ))
        
        return queries[:count]
    
    def generate_correlation_queries(self, analysis: Dict[str, Any], count: int = 2) -> List[QuerySuggestion]:
        """Generate correlation queries"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        pairs = analysis["interesting_pairs"]
        
        if len(numeric_cols) >= 3:
            queries.append(QuerySuggestion(
                id=1,
                query="Generate a correlation matrix to see relationships between all numeric data",
                category="correlation",
                icon=self.category_icons["correlation"],
                complexity="advanced"
            ))
            
        if pairs:
            col1, col2 = pairs[0]
            queries.append(QuerySuggestion(
                id=2,
                query=f"Analyze relationship between {col1} and {col2} using a bubble chart",
                category="correlation",
                icon=self.category_icons["correlation"],
                complexity="advanced"
            ))
        
        return queries[:count]
    
    def generate_top_n_queries(self, analysis: Dict[str, Any], count: int = 2) -> List[QuerySuggestion]:
        """Generate top N queries"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        categorical_cols = analysis["categorical_cols"]
        priorities = analysis["column_priorities"]
        
        if not numeric_cols or not categorical_cols:
            return queries
        
        # Sort by priority
        sorted_numeric = sorted(numeric_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        sorted_categorical = sorted(categorical_cols, key=lambda c: (
            0 if priorities.get(c) == "high" else 1 if priorities.get(c) == "medium" else 2
        ))
        
        # Generate combinations
        for i in range(min(count, len(sorted_numeric), len(sorted_categorical))):
            num_col = sorted_numeric[i % len(sorted_numeric)]
            cat_col = sorted_categorical[i % len(sorted_categorical)]
            
            queries.append(QuerySuggestion(
                id=len(queries) + 1,
                query=f"Top 10 {cat_col} by total {num_col}",
                category="top_n",
                icon=self.category_icons["top_n"],
                complexity="intermediate"
            ))
        
        return queries
    
    def generate_hierarchical_queries(self, analysis: Dict[str, Any], count: int = 2) -> List[QuerySuggestion]:
        """Generate hierarchical visualization queries"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        categorical_cols = analysis["categorical_cols"]
        
        if len(categorical_cols) >= 2 and numeric_cols:
            queries.append(QuerySuggestion(
                id=1,
                query=f"Break down {numeric_cols[0]} by {categorical_cols[0]} and {categorical_cols[1]} using a treemap",
                category="hierarchical",
                icon=self.category_icons["hierarchical"],
                complexity="intermediate"
            ))
            
            queries.append(QuerySuggestion(
                id=2,
                query=f"Show hierarchical structure of {categorical_cols[0]} and {categorical_cols[1]} via sunburst chart",
                category="hierarchical",
                icon=self.category_icons["hierarchical"],
                complexity="advanced"
            ))
            
        return queries[:count]

    def generate_advanced_queries(self, analysis: Dict[str, Any], count: int = 1) -> List[QuerySuggestion]:
        """Generate advanced multivariate queries"""
        queries = []
        numeric_cols = analysis["numeric_cols"]
        
        if len(numeric_cols) >= 3:
            queries.append(QuerySuggestion(
                id=1,
                query=f"Multi-dimensional analysis of {', '.join(numeric_cols[:4])} using parallel coordinates",
                category="advanced",
                icon=self.category_icons["advanced"],
                complexity="advanced"
            ))
            
        return queries[:count]
    
    def generate_suggestions(self, df: pd.DataFrame, max_queries: int = 10) -> List[QuerySuggestion]:
        """
        Generate dynamic query suggestions based on dataset structure
        
        Args:
            df: DataFrame to analyze
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of QuerySuggestion objects
        """
        try:
            # Analyze dataset
            analysis = self.analyze_dataset(df)
            
            all_queries = []
            
            # Generate different types of queries
            # Priority: Distribution > Comparison > Trend > Top N > Correlation > Aggregation
            
            # 1. Comparison & Category (4)
            # - Bar, Donut, Violin, Box
            all_queries.extend(self.generate_comparison_queries(analysis, count=4))
            
            # 2. Distribution (2)
            # - Histogram, Density Heatmap
            all_queries.extend(self.generate_distribution_queries(analysis, count=2))
            
            # 3. Trends (2)
            # - Line, Area
            if analysis["datetime_cols"]:
                all_queries.extend(self.generate_trend_queries(analysis, count=2))
            
            # 4. Hierarchical (2)
            # - Treemap, Sunburst
            all_queries.extend(self.generate_hierarchical_queries(analysis, count=2))
            
            # 5. Correlation & Relational (2)
            # - Heatmap, Bubble
            if len(analysis["numeric_cols"]) >= 2:
                all_queries.extend(self.generate_correlation_queries(analysis, count=2))
            
            # 6. Advanced Multivariate (1)
            # - Parallel Coordinates
            all_queries.extend(self.generate_advanced_queries(analysis, count=1))

            # 7. Ranking & Aggregation (2)
            # - Top N, Simple Sums
            all_queries.extend(self.generate_top_n_queries(analysis, count=2))
            
            # Re-number IDs
            for i, query in enumerate(all_queries[:max_queries]):
                query.id = i + 1
            
            self.logger.info(f"Generated {len(all_queries[:max_queries])} query suggestions")
            return all_queries[:max_queries]
            
        except Exception as e:
            self.logger.error(f"Error generating query suggestions: {str(e)}")
            return []
