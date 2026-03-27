"""
Intelligent visualization helper for database query results
Determines the best visualization type based on query and data structure
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal


def parse_database_result(raw_result: Any, query_type: str = "") -> Tuple[pd.DataFrame, Dict]:
    """
    Parse database result into a DataFrame and metadata
    Returns: (DataFrame, metadata_dict)
    """
    metadata = {
        'is_single_value': False,
        'is_list_of_values': False,
        'has_multiple_columns': False,
        'is_aggregate': False,
        'query_type': query_type,
        'raw_result_type': str(type(raw_result))
    }
    
    try:
        # Handle None case
        if raw_result is None:
            return None, metadata
            
        # Handle different result formats
        if isinstance(raw_result, (int, float, Decimal)):
            # Single numeric value
            value = float(raw_result) if isinstance(raw_result, Decimal) else raw_result
            metadata['is_single_value'] = True
            metadata['value'] = value
            return None, metadata
            
        elif isinstance(raw_result, str):
            # Try to parse string representation of lists/tuples
            try:
                import ast
                # If it looks like a string representation of a list/tuple, parse it
                stripped = raw_result.strip()
                if (stripped.startswith('[') or stripped.startswith('(')):
                    # Try to evaluate safely
                    parsed = ast.literal_eval(raw_result)
                    # Recursively parse the result
                    return parse_database_result(parsed, query_type)
            except:
                pass
            return None, {'raw_text': raw_result, **metadata}
            
        elif isinstance(raw_result, (list, tuple)):
            if not raw_result:
                return None, metadata
            
            first_item = raw_result[0]
            
            # Handle list of tuples/rows
            if isinstance(first_item, (tuple, list)):
                # Multiple columns
                metadata['has_multiple_columns'] = True
                df = pd.DataFrame(raw_result)
                
                # Convert Decimal to float in all columns
                for col in df.columns:
                    df[col] = df[col].apply(
                        lambda x: float(x) if isinstance(x, Decimal) else x
                    )
            else:
                # List of single values
                metadata['is_list_of_values'] = True
                values = [float(x) if isinstance(x, Decimal) else x for x in raw_result]
                df = pd.DataFrame({'value': values})
        
        else:
            # Unknown type, try to convert to string
            return None, metadata
            
    except Exception as e:
        import traceback
        return None, {'error': str(e), 'traceback': traceback.format_exc(), **metadata}
    
    return df, metadata


def detect_chart_type(question: str, df: pd.DataFrame, metadata: Dict) -> str:
    """
    Intelligently determine the best chart type based on question and data
    """
    question_lower = question.lower()
    
    # Single value result
    if metadata.get('is_single_value'):
        return 'metric_card'
    
    if df is None or df.empty:
        return 'text_only'
    
    # Check question keywords for chart type hints
    if any(word in question_lower for word in ['compare', 'comparison', 'by', 'distribution']):
        if len(df.columns) >= 2:
            return 'bar_chart'
    
    if any(word in question_lower for word in ['top', 'rank', 'highest', 'lowest', 'best', 'worst']):
        if len(df.columns) >= 2:
            return 'bar_chart'
    
    if any(word in question_lower for word in ['percentage', 'proportion', 'breakdown']):
        return 'pie_chart'
    
    if any(word in question_lower for word in ['trend', 'over time', 'history', 'growth']):
        return 'line_chart'
    
    # Analyze data structure
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    # If we have one categorical and one numeric -> bar chart
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        if len(df) <= 10:  # Reasonable number of bars
            return 'bar_chart'
        else:
            return 'table'
    
    # If we have 2 numeric columns -> line or scatter
    if len(numeric_cols) >= 2:
        return 'line_chart'
    
    # If single numeric column -> histogram
    if len(numeric_cols) == 1 and len(df) > 5:
        return 'bar_chart'
    
    # Default to table
    return 'table'


def create_visualization(question: str, raw_result: Any, chart_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Create the appropriate visualization based on question and data
    Returns: dict with 'chart' (plotly figure), 'chart_type', 'text_description'
    """
    df, metadata = parse_database_result(raw_result)
    
    # Detect chart type if not provided
    if not chart_type:
        chart_type = detect_chart_type(question, df, metadata)
    
    visualization = {
        'chart': None,
        'chart_type': chart_type,
        'text_description': '',
        'metadata': metadata
    }
    
    try:
        if chart_type == 'metric_card':
            # Single value - return as metric
            visualization['chart'] = None
            value = metadata.get('value', 'N/A')
            # Format large numbers
            if isinstance(value, (int, float)) and value >= 1000:
                value = f"{value:,.0f}"
            visualization['text_description'] = f"The result is: **{value}**"
            return visualization
            
        elif chart_type == 'text_only' or df is None or df.empty:
            visualization['chart'] = None
            visualization['text_description'] = str(raw_result)
            return visualization
        
        # Auto-detect column names for better labels
        if df is not None and not df.empty:
            # Standardize column names
            if len(df.columns) == 1:
                df.columns = ['value']
            elif len(df.columns) == 2:
                df.columns = ['category', 'value']
            elif len(df.columns) == 3:
                df.columns = ['category', 'subcategory', 'value']
            
            # BAR CHART
            if chart_type == 'bar_chart':
                if len(df.columns) >= 2:
                    fig = px.bar(
                        df.head(20),  # Limit to top 20 for readability
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"{question}",
                        labels={df.columns[0]: df.columns[0].replace('_', ' ').title(),
                                df.columns[1]: df.columns[1].replace('_', ' ').title()},
                        color=df.columns[1],
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(
                        template='plotly_white',
                        height=400,
                        xaxis_tickangle=-45
                    )
                    visualization['chart'] = fig
            # PIE CHART
            elif chart_type == 'pie_chart':
                if len(df.columns) >= 2 and len(df) <= 15:  # Pie charts work best with few categories
                    fig = px.pie(
                        df,
                        names=df.columns[0],
                        values=df.columns[1],
                        title=f"Breakdown: {question}"
                    )
                    fig.update_layout(template='plotly_white', height=500)
                    visualization['chart'] = fig
                else:
                    # Too many categories, use bar chart instead
                    fig = px.bar(
                        df.head(15),
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"{question}"
                    )
                    fig.update_layout(template='plotly_white', height=400)
                    visualization['chart'] = fig
            # LINE CHART
            elif chart_type == 'line_chart':
                if len(df.columns) >= 2:
                    fig = px.line(
                        df,
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"Trend: {question}",
                        markers=True
                    )
                    fig.update_layout(template='plotly_white', height=400)
                    visualization['chart'] = fig
            # SCATTER PLOT
            elif chart_type == 'scatter':
                if len(df.columns) >= 2:
                    fig = px.scatter(
                        df,
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"Distribution: {question}"
                    )
                    fig.update_layout(template='plotly_white', height=400)
                    visualization['chart'] = fig
            # TABLE
            else:
                # Return as formatted table data
                visualization['table_data'] = df
                visualization['chart'] = None
        
    except Exception as e:
        visualization['error'] = str(e)
        visualization['text_description'] = f"Error creating visualization: {str(e)}"
    
    return visualization


def format_with_chart(question: str, raw_result: Any) -> Dict[str, Any]:
    """
    Main function to format database result with intelligent visualization
    """
    # Force parse the result if it's a string representation
    if isinstance(raw_result, str):
        try:
            import ast
            # Check if it looks like a list/tuple
            stripped = raw_result.strip()
            if stripped.startswith('[') or stripped.startswith('('):
                raw_result = ast.literal_eval(raw_result)
        except:
            pass
    
    # If still a string, try to extract data from it
    if isinstance(raw_result, str) and 'Decimal' in raw_result:
        # Try to manually parse: [('Brand', Decimal('99')), ...]
        import re
        matches = re.findall(r"\('([^']+)',\s*Decimal\('(\d+)'\)\)", raw_result)
        if matches:
            raw_result = [(brand, Decimal(amt)) for brand, amt in matches]
    
    return create_visualization(question, raw_result)
