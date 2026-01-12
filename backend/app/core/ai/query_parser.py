"""
Query Parser - Natural Language to Visualization
Converts user's natural language queries into structured visualization requests
"""
#backend/app/core/ai/query_parser.py

from typing import List, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass
from enum import Enum
import logging
import re

from .llm_client import LLMClient, get_llm_client
from .conversation_manager import ConversationManager, get_conversation_manager

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Types of query intents"""
    VISUALIZE = "visualize"  # Create a chart
    ANALYZE = "analyze"      # Analyze data
    COMPARE = "compare"      # Compare values
    FILTER = "filter"        # Filter data
    AGGREGATE = "aggregate"  # Aggregate/summarize
    CORRELATE = "correlate"  # Find correlations
    TREND = "trend"          # Show trends
    DISTRIBUTION = "distribution"  # Show distributions
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    """Structured representation of parsed query"""
    intent: QueryIntent
    chart_type: Optional[str]
    columns: List[str]
    filters: Dict[str, Any]
    aggregations: Dict[str, str]  # column -> agg_function
    groupby: Optional[str]
    sort_by: Optional[str]
    limit: Optional[int]
    time_range: Optional[Dict[str, Any]]
    raw_query: str
    confidence: float


class QueryParser:
    """Parse natural language queries into structured visualization commands"""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        conversation_manager: Optional[ConversationManager] = None
    ):
        self.llm = llm_client or get_llm_client()
        self.conversation_mgr = conversation_manager or get_conversation_manager()
        
        # Intent keywords mapping
        self.intent_keywords = {
            QueryIntent.VISUALIZE: [
                "show", "display", "plot", "chart", "graph", "visualize", "draw"
            ],
            QueryIntent.ANALYZE: [
                "analyze", "analysis", "examine", "investigate", "study"
            ],
            QueryIntent.COMPARE: [
                "compare", "comparison", "versus", "vs", "difference", "between"
            ],
            QueryIntent.CORRELATE: [
                "correlation", "correlate", "relationship", "relation", "between"
            ],
            QueryIntent.TREND: [
                "trend", "over time", "time series", "temporal", "change"
            ],
            QueryIntent.DISTRIBUTION: [
                "distribution", "spread", "range", "histogram"
            ],
            QueryIntent.AGGREGATE: [
                "sum", "average", "mean", "count", "total", "aggregate"
            ]
        }
        
        # Chart type keywords
        self.chart_keywords = {
            "bar": ["bar", "bars", "bar chart"],
            "line": ["line", "lines", "line chart", "trend"],
            "scatter": ["scatter", "scatter plot", "points"],
            "pie": ["pie", "pie chart", "proportion"],
            "histogram": ["histogram", "distribution"],
            "box": ["box", "box plot", "boxplot"],
            "heatmap": ["heatmap", "heat map", "correlation"],
        }
    
    async def parse_query(
        self,
        query: str,
        df: pd.DataFrame,
        use_ai: bool = True,
        session_id: Optional[str] = None
    ) -> ParsedQuery:
        """
        Main method to parse natural language query
        
        Args:
            query: User's natural language query
            df: DataFrame to query against
            use_ai: Whether to use AI parsing
            session_id: Optional session ID for conversation context
        
        Returns:
            ParsedQuery with structured query information
        """
        # Resolve references if session provided
        resolved_query = query
        if session_id:
            resolved_query = self.conversation_mgr.resolve_references(session_id, query)
            
            # Add query to conversation history
            self.conversation_mgr.add_user_message(session_id, query)
        
        if use_ai:
            try:
                # Include conversation context in AI parsing
                context = self.conversation_mgr.get_context(session_id) if session_id else {}
                result = await self._parse_with_ai(resolved_query, df, context)
                
                # Update conversation context with parsed result
                if session_id:
                    self.conversation_mgr.update_context(session_id, {
                        "last_intent": result.intent.value,
                        "last_chart_type": result.chart_type,
                        "last_columns": result.columns,
                        "last_filters": result.filters
                    })
                
                return result
            except Exception as e:
                logger.warning(f"AI parsing failed, using rule-based: {str(e)}")
        
        result = self._parse_with_rules(resolved_query, df)
        
        # Update conversation context
        if session_id:
            self.conversation_mgr.update_context(session_id, {
                "last_intent": result.intent.value,
                "last_chart_type": result.chart_type,
                "last_columns": result.columns
            })
        
        return result
    
    async def _parse_with_ai(
        self,
        query: str,
        df: pd.DataFrame,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> ParsedQuery:
        """
        Parse query using AI/LLM with conversation context
        
        Args:
            query: User query
            df: DataFrame
            conversation_context: Optional conversation context
        
        Returns:
            ParsedQuery
        """
        # Prepare data context
        columns_info = []
        for col in df.columns:
            col_type = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else \
                       "datetime" if pd.api.types.is_datetime64_any_dtype(df[col]) else \
                       "categorical"
            columns_info.append(f"{col} ({col_type})")
        
        # Add conversation context if available
        context_info = ""
        if conversation_context:
            last_intent = conversation_context.get("last_intent")
            last_columns = conversation_context.get("last_columns", [])
            if last_intent or last_columns:
                context_info = f"\n\nConversation Context:\n"
                if last_intent:
                    context_info += f"- Previous intent: {last_intent}\n"
                if last_columns:
                    context_info += f"- Previously used columns: {', '.join(last_columns)}\n"
        
        data_context = f"""
Available Data:
- Columns: {', '.join(columns_info)}
- Total Rows: {len(df)}
- Sample Values: {df.head(2).to_dict('records')}{context_info}
"""
        
        system_message = """You are a data visualization expert.
Parse the user's natural language query into a structured format for creating visualizations.

Identify:
1. Intent (what they want to do)
2. Chart type (if specified or implied)
3. Columns to use
4. Any filters or conditions
5. Aggregations needed
6. Grouping/sorting requirements"""
        
        prompt = f"""{data_context}

User Query: "{query}"

Parse this query into JSON format:
{{
    "intent": "visualize|analyze|compare|correlate|trend|distribution",
    "chart_type": "bar|line|scatter|pie|histogram|box|heatmap|null",
    "columns": ["column1", "column2"],
    "filters": {{"column_name": "condition"}},
    "aggregations": {{"column_name": "sum|mean|count|max|min"}},
    "groupby": "column_name or null",
    "sort_by": "column_name or null",
    "limit": number or null,
    "confidence": 0.0-1.0
}}

Examples:
Query: "Show me sales by region"
Response: {{"intent": "visualize", "chart_type": "bar", "columns": ["region", "sales"], "aggregations": {{"sales": "sum"}}, "groupby": "region", "confidence": 0.9}}

Query: "Plot revenue over time"
Response: {{"intent": "trend", "chart_type": "line", "columns": ["time", "revenue"], "confidence": 0.95}}

Now parse the user's query above."""
        
        try:
            response = await self.llm.generate_structured(
                prompt=prompt,
                system_message=system_message,
                output_schema={
                    "intent": "string",
                    "chart_type": "string or null",
                    "columns": ["string"],
                    "filters": {},
                    "aggregations": {},
                    "groupby": "string or null",
                    "sort_by": "string or null",
                    "limit": "number or null",
                    "confidence": "float"
                }
            )
            
            # Convert to ParsedQuery
            return ParsedQuery(
                intent=QueryIntent(response.get("intent", "visualize")),
                chart_type=response.get("chart_type"),
                columns=response.get("columns", []),
                filters=response.get("filters", {}),
                aggregations=response.get("aggregations", {}),
                groupby=response.get("groupby"),
                sort_by=response.get("sort_by"),
                limit=response.get("limit"),
                time_range=None,
                raw_query=query,
                confidence=response.get("confidence", 0.8)
            )
        
        except Exception as e:
            logger.error(f"AI query parsing error: {str(e)}")
            raise
    
    def _parse_with_rules(self, query: str, df: pd.DataFrame) -> ParsedQuery:
        """Parse query using rule-based approach"""
        
        query_lower = query.lower()
        
        # 1. Detect intent
        intent = self._detect_intent(query_lower)
        
        # 2. Detect chart type
        chart_type = self._detect_chart_type(query_lower)
        
        # 3. Extract column names
        columns = self._extract_columns(query_lower, df)
        
        # 4. Detect aggregations
        aggregations = self._detect_aggregations(query_lower, columns)
        
        # 5. Detect groupby
        groupby = self._detect_groupby(query_lower, df)
        
        # 6. Detect filters
        filters = self._detect_filters(query_lower, df)
        
        # 7. Detect sorting
        sort_by = self._detect_sorting(query_lower, df)
        
        # 8. Detect limit
        limit = self._detect_limit(query_lower)
        
        return ParsedQuery(
            intent=intent,
            chart_type=chart_type,
            columns=columns,
            filters=filters,
            aggregations=aggregations,
            groupby=groupby,
            sort_by=sort_by,
            limit=limit,
            time_range=None,
            raw_query=query,
            confidence=0.6  # Lower confidence for rule-based
        )
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect query intent from keywords"""
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in query for keyword in keywords):
                return intent
        return QueryIntent.VISUALIZE  # Default
    
    def _detect_chart_type(self, query: str) -> Optional[str]:
        """Detect chart type from keywords"""
        for chart_type, keywords in self.chart_keywords.items():
            if any(keyword in query for keyword in keywords):
                return chart_type
        return None
    
    def _extract_columns(self, query: str, df: pd.DataFrame) -> List[str]:
        """Extract column names mentioned in query"""
        found_columns = []
        
        for col in df.columns:
            # Check exact match (case-insensitive)
            if col.lower() in query:
                found_columns.append(col)
            # Check partial match
            elif any(word in query for word in col.lower().split('_')):
                found_columns.append(col)
        
        return found_columns
    
    def _detect_aggregations(
        self,
        query: str,
        columns: List[str]
    ) -> Dict[str, str]:
        """Detect aggregation functions"""
        aggregations = {}
        
        agg_keywords = {
            "sum": ["sum", "total"],
            "mean": ["average", "mean", "avg"],
            "count": ["count", "number of"],
            "max": ["maximum", "max", "highest"],
            "min": ["minimum", "min", "lowest"]
        }
        
        for agg_func, keywords in agg_keywords.items():
            if any(keyword in query for keyword in keywords):
                # Apply to numeric columns
                for col in columns:
                    aggregations[col] = agg_func
                break
        
        return aggregations
    
    def _detect_groupby(self, query: str, df: pd.DataFrame) -> Optional[str]:
        """Detect groupby column"""
        groupby_keywords = ["by", "per", "for each", "group by"]
        
        for keyword in groupby_keywords:
            if keyword in query:
                # Find the column after the keyword
                words = query.split(keyword)
                if len(words) > 1:
                    potential_col = words[1].strip().split()[0]
                    # Check if it matches a column
                    for col in df.columns:
                        if col.lower() in potential_col or potential_col in col.lower():
                            return col
        
        return None
    
    def _detect_filters(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect filter conditions"""
        filters = {}
        
        # Look for comparison operators
        patterns = [
            r"(\w+)\s*(>|<|>=|<=|=|==)\s*(\d+\.?\d*)",
            r"(\w+)\s*is\s*(\w+)",
            r"where\s+(\w+)\s*=\s*['\"]?(\w+)['\"]?"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                col_name = match.group(1)
                # Find matching column
                for col in df.columns:
                    if col.lower() in col_name or col_name in col.lower():
                        filters[col] = match.group(2) if len(match.groups()) > 1 else match.group(1)
        
        return filters
    
    def _detect_sorting(self, query: str, df: pd.DataFrame) -> Optional[str]:
        """Detect sorting requirements"""
        sort_keywords = ["sort", "order", "sorted by", "ordered by"]
        
        for keyword in sort_keywords:
            if keyword in query:
                words = query.split(keyword)
                if len(words) > 1:
                    potential_col = words[1].strip().split()[0]
                    for col in df.columns:
                        if col.lower() in potential_col or potential_col in col.lower():
                            return col
        
        return None
    
    def _detect_limit(self, query: str) -> Optional[int]:
        """Detect limit/top N"""
        # Look for "top N", "first N", "limit N"
        patterns = [
            r"top\s+(\d+)",
            r"first\s+(\d+)",
            r"limit\s+(\d+)",
            r"(\d+)\s+(?:top|first)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def suggest_chart_for_intent(
        self,
        parsed_query: ParsedQuery,
        df: pd.DataFrame
    ) -> str:
        """Suggest best chart type based on parsed query and data"""
        
        # If chart type already specified, use it
        if parsed_query.chart_type:
            return parsed_query.chart_type
        
        columns = parsed_query.columns
        if not columns:
            return "table"  # Fallback
        
        # Analyze column types
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
        categorical_cols = [col for col in columns if not pd.api.types.is_numeric_dtype(df[col])]
        datetime_cols = [col for col in columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        
        # Decision logic based on intent and columns
        if parsed_query.intent == QueryIntent.TREND or datetime_cols:
            return "line"
        
        elif parsed_query.intent == QueryIntent.DISTRIBUTION:
            return "histogram"
        
        elif parsed_query.intent == QueryIntent.CORRELATE:
            if len(numeric_cols) >= 2:
                return "scatter"
            return "heatmap"
        
        elif parsed_query.intent == QueryIntent.COMPARE:
            return "bar"
        
        elif len(numeric_cols) == 2:
            return "scatter"
        
        elif len(numeric_cols) == 1 and len(categorical_cols) == 1:
            return "bar"
        
        elif len(numeric_cols) == 1:
            return "histogram"
        
        else:
            return "bar"  # Default fallback