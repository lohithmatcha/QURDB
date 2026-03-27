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
import ast


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
            stripped = raw_result.strip()
            
            # Try to extract data from string representations like "[('Brand', Decimal('99')), ...]"
            if 'Decimal' in raw_result:
                # Pattern: [('Brand', Decimal('99')), ...]
                matches = re.findall(r"\(['\"]([^'\"]+)['\"],\s*Decimal\(['\"]?([0-9.]+)['\"]?\)\)", raw_result)
                if matches:
                    parsed_result = [(name, Decimal(val)) for name, val in matches]
                    return parse_database_result(parsed_result, query_type)
                
                # Pattern: (Decimal('99'),) - single value
                single_decimal_match = re.search(r"Decimal\(['\"]?([0-9.]+)['\"]?\)", raw_result)
                if single_decimal_match and not matches:
                    value = float(Decimal(single_decimal_match.group(1)))
                    metadata['is_single_value'] = True
                    metadata['value'] = value
                    return None, metadata
            
            # Try standard AST parsing
            if (stripped.startswith('[') or stripped.startswith('(')):
                try:
                    parsed = ast.literal_eval(raw_result)
                    return parse_database_result(parsed, query_type)
                except:
                    pass
            
            # If still a string, return as text
            return None, {'raw_text': raw_result, **metadata}
            
        elif isinstance(raw_result, (list, tuple)):
            if not raw_result:
                return None, metadata
            
            first_item = raw_result[0]
            
            # Handle list of tuples/rows (most common case)
            if isinstance(first_item, (tuple, list)):
                # Multiple columns
                metadata['has_multiple_columns'] = True
                
                # Convert to list of lists for DataFrame
                rows = []
                for item in raw_result:
                    if isinstance(item, (tuple, list)):
                        # Convert each element, handling Decimals
                        row = []
                        for cell in item:
                            if isinstance(cell, Decimal):
                                row.append(float(cell))
                            else:
                                row.append(cell)
                        rows.append(row)
                    else:
                        rows.append([item])
                
                # Create DataFrame
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # Convert Decimal to float in all columns
                    for col in df.columns:
                        df[col] = df[col].apply(
                            lambda x: float(x) if isinstance(x, Decimal) else x
                        )
                    
                    # Try to infer column names from data
                    if len(df.columns) == 1:
                        df.columns = ['value']
                    elif len(df.columns) == 2:
                        # Check if first column is numeric (might be swapped)
                        if pd.api.types.is_numeric_dtype(df.iloc[:, 0]) and not pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                            df.columns = ['value', 'category']
                            df = df[['category', 'value']]  # Swap for better visualization
                        else:
                            df.columns = ['category', 'value']
                    elif len(df.columns) >= 3:
                        # Handle 3+ columns - assign meaningful names to avoid duplicates
                        # Check which columns are numeric by index position
                        numeric_indices = []
                        categorical_indices = []
                        
                        for i in range(len(df.columns)):
                            if pd.api.types.is_numeric_dtype(df.iloc[:, i]):
                                numeric_indices.append(i)
                            else:
                                categorical_indices.append(i)
                        
                        # Create unique column names
                        col_names = []
                        numeric_count = 0
                        categorical_count = 0
                        
                        for i in range(len(df.columns)):
                            if i in numeric_indices:
                                if len(numeric_indices) == 2:
                                    # For 2 numeric columns, name them meaningfully (e.g., min/max)
                                    if numeric_count == 0:
                                        col_names.append('min_value')
                                    else:
                                        col_names.append('max_value')
                                    numeric_count += 1
                                else:
                                    # For more than 2 numeric columns, use indexed names
                                    col_names.append(f'value_{numeric_count + 1}')
                                    numeric_count += 1
                            else:
                                if categorical_count == 0:
                                    col_names.append('category')
                                else:
                                    col_names.append(f'category_{categorical_count + 1}')
                                categorical_count += 1
                        
                        df.columns = col_names
                    
                    return df, metadata
                else:
                    return None, metadata
            else:
                # List of single values
                metadata['is_list_of_values'] = True
                values = []
                for x in raw_result:
                    if isinstance(x, Decimal):
                        values.append(float(x))
                    elif isinstance(x, (tuple, list)) and len(x) == 1:
                        # Handle [(value,), (value,), ...]
                        val = x[0]
                        values.append(float(val) if isinstance(val, Decimal) else val)
                    else:
                        values.append(x)
                
                df = pd.DataFrame({'value': values})
                return df, metadata
        
        else:
            # Unknown type, try to convert to string and parse
            str_repr = str(raw_result)
            if 'Decimal' in str_repr or '[' in str_repr:
                return parse_database_result(str_repr, query_type)
            return None, metadata
            
    except Exception as e:
        import traceback
        error_info = {
            'error': str(e), 
            'traceback': traceback.format_exc(), 
            **metadata
        }
        return None, error_info
    
    return None, metadata


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
    pie_keywords = ['percentage', 'proportion', 'breakdown', 'distribution of', 'share', 'ratio', 'percent']
    if any(word in question_lower for word in pie_keywords):
        if len(df.columns) >= 2 and len(df) <= 15:
            return 'pie_chart'
    
    if any(word in question_lower for word in ['compare', 'comparison', 'by', 'top', 'rank', 'highest', 'lowest', 'best', 'worst', 'range', 'min', 'max', 'minimum', 'maximum']):
        if len(df.columns) >= 2:
            return 'bar_chart'
    
    if any(word in question_lower for word in ['trend', 'over time', 'history', 'growth', 'over time']):
        return 'line_chart'
    
    # Analyze data structure
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    # If we have one categorical and one numeric -> bar chart
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        if len(df) <= 20:  # Reasonable number of bars
            # For small datasets with clear categories, prefer bar chart
            if len(df) <= 10:
                return 'bar_chart'
            else:
                return 'bar_chart'  # Still use bar chart for up to 20 items
        else:
            return 'table'
    
    # If we have 2 numeric columns -> line or scatter
    if len(numeric_cols) >= 2:
        if 'trend' in question_lower or 'time' in question_lower:
            return 'line_chart'
        return 'scatter'
    
    # If single numeric column with multiple values -> bar chart
    if len(numeric_cols) == 1 and len(df) > 1:
        return 'bar_chart'
    
    # Default to table for complex data
    return 'table'


def create_visualization(question: str, raw_result: Any, chart_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Create the appropriate visualization based on question and data
    Returns: dict with 'chart' (plotly figure), 'chart_type', 'text_description', 'table_data'
    """
    df, metadata = parse_database_result(raw_result)
    
    # Detect chart type if not provided
    if not chart_type:
        chart_type = detect_chart_type(question, df, metadata)
    
    visualization = {
        'chart': None,
        'chart_type': chart_type,
        'text_description': '',
        'metadata': metadata,
        'table_data': None
    }
    
    try:
        # Handle single value
        if chart_type == 'metric_card':
            value = metadata.get('value', 'N/A')
            # Format large numbers
            if isinstance(value, (int, float)):
                if value >= 1000:
                    value_str = f"{value:,.0f}"
                elif isinstance(value, float):
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
            else:
                value_str = str(value)
            visualization['text_description'] = f"The result is: **{value_str}**"
            return visualization
            
        # Handle text-only results
        if chart_type == 'text_only' or df is None or df.empty:
            visualization['text_description'] = str(raw_result)
            if df is not None and not df.empty:
                visualization['table_data'] = df
            return visualization
        
        # Ensure we have proper column structure
        if df is not None and not df.empty:
            # Identify categorical and numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
            
            # BAR CHART
            if chart_type == 'bar_chart':
                if len(df.columns) >= 2:
                    # Special handling for price range queries (min_value and max_value columns)
                    if 'min_value' in df.columns and 'max_value' in df.columns:
                        # Create grouped bar chart for min/max values
                        cat_col = 'category' if 'category' in df.columns else df.columns[0]
                        
                        # Create a long format for grouped bar chart
                        df_melted = pd.melt(
                            df,
                            id_vars=[cat_col],
                            value_vars=['min_value', 'max_value'],
                            var_name='type',
                            value_name='price'
                        )
                        
                        # Create grouped bar chart
                        fig = px.bar(
                            df_melted,
                            x=cat_col,
                            y='price',
                            color='type',
                            title=f"📊 {question}",
                            labels={
                                cat_col: cat_col.replace('_', ' ').title(),
                                'price': 'Price',
                                'type': 'Type'
                            },
                            barmode='group',
                            color_discrete_map={
                                'min_value': '#1f77b4',
                                'max_value': '#ff7f0e'
                            }
                        )
                        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside', textfont=dict(color='#000000', size=11))
                        fig.update_layout(
                            template='plotly_white',
                            height=500,
                            showlegend=True,
                            xaxis_tickangle=-45,
                            plot_bgcolor='#ffffff',
                            paper_bgcolor='#ffffff',
                            font=dict(size=12, color='#000000', family='Inter'),
                            title_font=dict(size=16, color='#000000', family='Poppins'),
                            xaxis=dict(
                                title_font=dict(color='#000000', size=13),
                                tickfont=dict(color='#000000', size=11),
                                gridcolor='#e1e8ed',
                                linecolor='#000000'
                            ),
                            yaxis=dict(
                                title_font=dict(color='#000000', size=13),
                                tickfont=dict(color='#000000', size=11),
                                gridcolor='#e1e8ed',
                                linecolor='#000000'
                            ),
                            legend=dict(
                                title='Price Type',
                                title_font=dict(color='#000000', size=12),
                                font=dict(color='#000000', size=11),
                                labels={'min_value': 'Min Price', 'max_value': 'Max Price'}
                            ),
                            margin=dict(l=20, r=20, t=60, b=100)
                        )
                    else:
                        # Standard bar chart
                        # Find category and value columns
                        cat_col = df.columns[0]
                        val_col = df.columns[-1] if len(numeric_cols) > 0 else df.columns[1]
                        
                        # Ensure value column is numeric
                        if val_col not in numeric_cols:
                            # Find first numeric column
                            if numeric_cols:
                                val_col = numeric_cols[0]
                            else:
                                # Try to convert
                                df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
                        
                        # Sort by value for better visualization
                        df_sorted = df.sort_values(by=val_col, ascending=False).head(20)
                        
                        # Create bar chart
                        fig = px.bar(
                            df_sorted,
                            x=cat_col,
                            y=val_col,
                            title=f"📊 {question}",
                            labels={
                                cat_col: cat_col.replace('_', ' ').title(),
                                val_col: val_col.replace('_', ' ').title()
                            },
                            color=val_col,
                            color_continuous_scale='viridis',
                            text=val_col
                        )
                    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside', textfont=dict(color='#000000', size=11))
                    fig.update_layout(
                        template='plotly_white',
                        height=500,
                        showlegend=False,
                        xaxis_tickangle=-45,
                        plot_bgcolor='#ffffff',
                        paper_bgcolor='#ffffff',
                        font=dict(size=12, color='#000000', family='Inter'),
                        title_font=dict(size=16, color='#000000', family='Poppins'),
                        xaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        yaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        margin=dict(l=20, r=20, t=60, b=100)
                    )
                    visualization['chart'] = fig
                else:
                    # Single column - create simple bar chart
                    fig = px.bar(
                        df.head(20),
                        x=df.index,
                        y=df.columns[0],
                        title=f"📊 {question}",
                        labels={df.columns[0]: df.columns[0].replace('_', ' ').title()}
                    )
                    fig.update_layout(
                        template='plotly_white',
                        height=400,
                        plot_bgcolor='#ffffff',
                        paper_bgcolor='#ffffff',
                        font=dict(size=12, color='#000000', family='Inter'),
                        title_font=dict(size=16, color='#000000', family='Poppins'),
                        xaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        yaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        )
                    )
                    visualization['chart'] = fig
            
            # PIE CHART
            elif chart_type == 'pie_chart':
                if len(df.columns) >= 2 and len(df) <= 15:
                    # Find category and value columns
                    cat_col = df.columns[0]
                    val_col = df.columns[-1] if len(numeric_cols) > 0 else df.columns[1]
                    
                    # Ensure value column is numeric
                    if val_col not in numeric_cols:
                        df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
                    
                    # Remove any rows with null values
                    df_clean = df.dropna(subset=[val_col])
                    
                    if not df_clean.empty:
                        # Create pie chart
                        fig = px.pie(
                            df_clean,
                            names=cat_col,
                            values=val_col,
                            title=f"🍩 {question}",
                            hole=0.4,  # Donut chart for modern look
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(
                            textposition='outside',
                            textinfo='label+percent',
                            textfont=dict(color='#000000', size=13, family='Inter'),
                            insidetextfont=dict(color='#000000', size=12, family='Inter'),
                            outsidetextfont=dict(color='#000000', size=13, family='Inter'),
                            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>',
                            marker=dict(line=dict(color='#ffffff', width=2))
                        )
                        fig.update_layout(
                            template='plotly_white',
                            height=500,
                            showlegend=True,
                            legend=dict(
                                orientation="v",
                                yanchor="middle",
                                y=0.5,
                                xanchor="left",
                                x=1.05,
                                font=dict(color='#000000', size=12),
                                title_font=dict(color='#000000', size=13)
                            ),
                            plot_bgcolor='#ffffff',
                            paper_bgcolor='#ffffff',
                            font=dict(size=12, color='#000000', family='Inter'),
                            title_font=dict(size=16, color='#000000', family='Poppins')
                        )
                        visualization['chart'] = fig
                    else:
                        # Fallback to bar chart
                        visualization['chart_type'] = 'bar_chart'
                        return create_visualization(question, raw_result, 'bar_chart')
                else:
                    # Too many categories, use bar chart instead
                    visualization['chart_type'] = 'bar_chart'
                    return create_visualization(question, raw_result, 'bar_chart')
            
            # LINE CHART
            elif chart_type == 'line_chart':
                if len(df.columns) >= 2:
                    x_col = df.columns[0]
                    y_col = df.columns[-1] if len(numeric_cols) > 0 else df.columns[1]
                    
                    fig = px.line(
                        df,
                        x=x_col,
                        y=y_col,
                        title=f"📈 {question}",
                        markers=True,
                        labels={
                            x_col: x_col.replace('_', ' ').title(),
                            y_col: y_col.replace('_', ' ').title()
                        }
                    )
                    fig.update_layout(
                        template='plotly_white',
                        height=400,
                        plot_bgcolor='#ffffff',
                        paper_bgcolor='#ffffff',
                        font=dict(size=12, color='#000000', family='Inter'),
                        title_font=dict(size=16, color='#000000', family='Poppins'),
                        xaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        yaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        legend=dict(
                            font=dict(color='#000000', size=11),
                            title_font=dict(color='#000000', size=12)
                        )
                    )
                    visualization['chart'] = fig
            
            # SCATTER PLOT
            elif chart_type == 'scatter':
                if len(df.columns) >= 2:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    
                    fig = px.scatter(
                        df,
                        x=x_col,
                        y=y_col,
                        title=f"📊 {question}",
                        labels={
                            x_col: x_col.replace('_', ' ').title(),
                            y_col: y_col.replace('_', ' ').title()
                        }
                    )
                    fig.update_layout(
                        template='plotly_white',
                        height=400,
                        plot_bgcolor='#ffffff',
                        paper_bgcolor='#ffffff',
                        font=dict(size=12, color='#000000', family='Inter'),
                        title_font=dict(size=16, color='#000000', family='Poppins'),
                        xaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        yaxis=dict(
                            title_font=dict(color='#000000', size=13),
                            tickfont=dict(color='#000000', size=11),
                            gridcolor='#e1e8ed',
                            linecolor='#000000'
                        ),
                        legend=dict(
                            font=dict(color='#000000', size=11),
                            title_font=dict(color='#000000', size=12)
                        )
                    )
                    visualization['chart'] = fig
            
            # TABLE
            else:
                # Return as formatted table data
                visualization['table_data'] = df
                visualization['chart'] = None
        
    except Exception as e:
        import traceback
        visualization['error'] = str(e)
        visualization['traceback'] = traceback.format_exc()
        visualization['text_description'] = f"Error creating visualization: {str(e)}"
        # Still try to return table data if available
        if df is not None and not df.empty:
            visualization['table_data'] = df
    
    return visualization


def format_with_chart(question: str, raw_result: Any) -> Dict[str, Any]:
    """
    Main function to format database result with intelligent visualization
    """
    # Force parse the result if it's a string representation
    if isinstance(raw_result, str):
        try:
            # Check if it looks like a list/tuple
            stripped = raw_result.strip()
            if stripped.startswith('[') or stripped.startswith('('):
                raw_result = ast.literal_eval(raw_result)
        except:
            # Try manual parsing for Decimal strings
            if 'Decimal' in raw_result:
                # Pattern: [('Brand', Decimal('99')), ...]
                matches = re.findall(r"\(['\"]([^'\"]+)['\"],\s*Decimal\(['\"]?([0-9.]+)['\"]?\)\)", raw_result)
                if matches:
                    raw_result = [(brand, Decimal(amt)) for brand, amt in matches]
                else:
                    # Single Decimal value
                    single_match = re.search(r"Decimal\(['\"]?([0-9.]+)['\"]?\)", raw_result)
                    if single_match:
                        raw_result = Decimal(single_match.group(1))
    
    return create_visualization(question, raw_result)

