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
import difflib

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
    groupby: List[str]
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
            "bar": ["bar", "bars", "bar chart", "column chart"],
            "line": ["line", "lines", "line chart", "trend", "time series"],
            "pie": ["pie", "pie chart", "proportion", "percentage"],
            "donut": ["donut", "donut chart", "ring chart"],
            "histogram": ["histogram", "distribution", "hist"],
            "box": ["box", "box plot", "boxplot"],
            "violin": ["violin", "violin plot"],
            "area": ["area", "area chart", "stacked area"],
            "bubble": ["bubble", "bubble chart"],
            "sunburst": ["sunburst", "sunburst chart", "circular tree"],
            "treemap": ["treemap", "tree map", "hierarchical rectangles"],
            "correlation_heatmap": ["correlation", "heatmap", "correlation matrix", "relationship map"]
        }
    
    async def parse_query(
        self,
        query: str,
        df: pd.DataFrame,
        use_ai: bool = True,
        session_id: Optional[str] = None,
        user_id: str = "anonymous"
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
                result = await self._parse_with_ai(resolved_query, df, context, user_id=user_id)
                
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
        conversation_context: Optional[Dict[str, Any]] = None,
        user_id: str = "anonymous"
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
        
        system_message = """You are an expert data visualization analyst specializing in understanding user intent and translating natural language queries into structured visualization specifications.

Your task is to:
1. Extract the user's visualization intent (what they want to see)
2. Identify the chart type (explicit or inferred from query)
3. Extract all data columns mentioned or implied
4. Determine grouping, aggregation, and filtering requirements

CRITICAL INSTRUCTIONS:
- For chart type detection: Look for keywords like "bar", "line", "pie", "histogram", "box"
- For semantic mapping: Match mentioned terms to existing columns based on meaning (e.g., "earnings" -> "Revenue", "turnover" -> "Sales").
- For column extraction: Match mentioned column names as closely as possible to those in the dataset.
- Always infer aggregations for numeric columns when grouping is specified.
- For "by" keyword queries like "age and purchase_value by user_id", extract:
  - columns: all mentioned columns
  - groupby: the column after "by"
  - aggregations: numeric columns should use appropriate aggregations (sum/mean/count)"""
        
        prompt = f"""{data_context}

User Query: "{query}"

Analyze this query and extract:
1. What data columns the user wants to see (extract column names that match exactly with dataset)
2. How they want to group or aggregate the data (detect "by" keyword)
3. What type of chart would best represent this (bar, line, pie, histogram, box)
4. Any filters, sorting, or limits mentioned

Return ONLY valid JSON (no markdown, no extra text):
{{
    "intent": "visualize",
    "chart_type": "bar|line|pie|histogram|box|null",
    "columns": ["column1", "column2"],
    "filters": {{}},
    "aggregations": {{"column_name": "sum|mean|count|max|min"}},
    "groupby": ["column_name", "column_name"],
    "sort_by": "column_name or null",
    "limit": null,
    "confidence": 0.0-1.0
}}

PARSING EXAMPLES:

Query: "plot my monthly earnings over time"
Response: {{"intent": "trend", "chart_type": "line", "columns": ["Date", "Revenue"], "aggregations": {{"Revenue": "sum"}}, "groupby": "Date", "confidence": 0.92}}

Query: "distribution of ages for our customers"
Response: {{"intent": "distribution", "chart_type": "histogram", "columns": ["age"], "aggregations": {{}}, "groupby": [], "confidence": 0.95}}

Query: "compare sales performance across different departments"
Response: {{"intent": "compare", "chart_type": "bar", "columns": ["department", "sales"], "aggregations": {{"sales": "sum"}}, "groupby": ["department"], "confidence": 0.9}}

Now carefully parse this user query: "{query}"
Return ONLY the JSON response, nothing else."""
        
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
                    "groupby": ["string"],
                    "sort_by": "string or null",
                    "limit": "number or null",
                    "confidence": "float"
                },
                user_id=user_id,
                endpoint="query"
            )
            
            # Extract results
            intent_str = response.get("intent", "visualize")
            chart_type = response.get("chart_type")
            suggested_cols = response.get("columns", [])
            groupby = response.get("groupby")
            aggregations = response.get("aggregations", {})
            
            # Post-process columns with fuzzy matching fallback
            actual_columns = df.columns.tolist()
            mapped_columns = []
            
            def get_best_match(col_name):
                # 1. Exact match (case insensitive)
                for actual in actual_columns:
                    if col_name.lower() == actual.lower():
                        return actual
                
                # 2. Fuzzy match
                matches = difflib.get_close_matches(col_name, actual_columns, n=1, cutoff=0.7)
                if matches:
                    return matches[0]
                
                return None

            for col in suggested_cols:
                match = get_best_match(col)
                if match:
                    mapped_columns.append(match)
            
            # Map groupby and aggregations keys as well
            mapped_groupby = []
            suggested_groupby = response.get("groupby", [])
            if isinstance(suggested_groupby, str):
                suggested_groupby = [suggested_groupby]
            
            for g in suggested_groupby:
                match = get_best_match(g)
                if match:
                    mapped_groupby.append(match)

            new_aggs = {}
            for col, agg in aggregations.items():
                col_match = get_best_match(col)
                if col_match:
                    new_aggs[col_match] = agg
            
            # Convert to ParsedQuery
            return ParsedQuery(
                intent=QueryIntent(intent_str),
                chart_type=chart_type,
                columns=mapped_columns,
                filters=response.get("filters", {}),
                aggregations=new_aggs,
                groupby=mapped_groupby,
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
        query_lower = query.lower()
        
        chart_patterns = {
            "bar": ["bar chart", "bar graph", "bars", " bar ", "barplot", "column chart"],
            "line": ["line chart", "line graph", "line plot", "trend"],
            "pie": ["pie chart", "pie graph"],
            "donut": ["donut chart", "donut graph", "donut", "ring chart"],
            "histogram": ["histogram", "distribution", "hist"],
            "box": ["box plot", "boxplot", "box-and-whisker"],
            "violin": ["violin plot", "violinplot", "violin"],
            "area": ["area chart", "area graph", "stacked area"],
            "bubble": ["bubble chart", "bubble graph", "bubbles"],
            "sunburst": ["sunburst chart", "sunburst graph", "sunburst"],
            "treemap": ["treemap", "tree map"],
            "correlation_heatmap": ["correlation heatmap", "correlation matrix", "heatmap"],
        }
        
        for chart_type, keywords in chart_patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return chart_type
        
        return None
    
    def _extract_columns(self, query: str, df: pd.DataFrame) -> List[str]:
        """Extract column names mentioned in query - improved extraction"""
        found_columns = []
        query_lower = query.lower()
        
        # First, look for quoted column names like 'age' or "purchase_value"
        import re
        quoted_pattern = r"['\"]([^'\"]+)['\"]"
        quoted_matches = re.findall(quoted_pattern, query)
        
        # Check quoted matches against actual columns
        for match in quoted_matches:
            for col in df.columns:
                if match.lower() == col.lower() or match.lower() == col.lower().replace('_', ' ').replace('-', ' '):
                    if col not in found_columns:
                        found_columns.append(col)
        
        # Then check for unquoted exact matches
        for col in df.columns:
            col_lower = col.lower()
            # Exact match
            if col_lower in query_lower:
                if col not in found_columns:
                    found_columns.append(col)
            # Match with word boundaries
            elif re.search(r'\b' + re.escape(col_lower.replace('_', ' ')) + r'\b', query_lower):
                if col not in found_columns:
                    found_columns.append(col)
        
        return found_columns
    
    def _detect_aggregations(
        self,
        query: str,
        columns: List[str]
    ) -> Dict[str, str]:
        """Detect aggregation functions - improved with better type detection"""
        aggregations = {}
        
        agg_keywords = {
            "sum": ["sum", "total", "add up"],
            "mean": ["average", "mean", "avg"],
            "count": ["count", "number of", "how many"],
            "max": ["maximum", "max", "highest", "largest"],
            "min": ["minimum", "min", "lowest", "smallest"]
        }
        
        # Check for explicit aggregation keywords
        detected_agg = None
        for agg_func, keywords in agg_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                detected_agg = agg_func
                break
        
        # If no explicit aggregation but columns present, apply reasonable defaults
        # Numeric columns typically get sum/count, non-numeric get count
        if columns:
            for col in columns:
                if detected_agg:
                    aggregations[col] = detected_agg

        
        return aggregations
    
    def _detect_groupby(self, query: str, df: pd.DataFrame) -> List[str]:
        """Detect groupby columns - improved to handle multiple columns after 'by'"""
        import re
        
        groupby_keywords = ["by", "per", "for each", "group by"]
        query_lower = query.lower()
        found_groups = []
        
        for keyword in groupby_keywords:
            if keyword in query_lower:
                parts = query_lower.split(keyword)
                if len(parts) > 1:
                    after_keyword = parts[-1].strip()
                    
                    # Look for columns until "as", "using", "with" or other keywords
                    cutoff_keywords = ["as", "using", "with", "where", "sort", "limit"]
                    for ck in cutoff_keywords:
                        if ck in after_keyword:
                            after_keyword = after_keyword.split(ck)[0].strip()
                    
                    # Split by "and" or commas
                    potential_names = re.split(r'[,]| and ', after_keyword)
                    
                    for name in potential_names:
                        name_clean = name.strip().strip("'\"")
                        if not name_clean:
                            continue
                        
                        # Match against actual columns
                        for col in df.columns:
                            if name_clean == col.lower() or name_clean.replace(' ', '_') == col.lower():
                                if col not in found_groups:
                                    found_groups.append(col)
        
        return found_groups
    
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
                return "line"
            return "bar"
        
        elif parsed_query.intent == QueryIntent.COMPARE:
            return "bar"
        
        elif len(numeric_cols) >= 3:
            return "pie"
        
        elif len(numeric_cols) == 2:
            return "line"
        
        elif len(numeric_cols) == 1 and len(categorical_cols) == 1:
            return "bar"
        
        elif len(numeric_cols) == 1:
            return "histogram"
        
        else:
            return "bar"  # Default fallback