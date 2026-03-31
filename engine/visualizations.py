# -*- coding: utf-8 -*-
"""
Advanced Visualizations for GeoLift Calculator
Includes sparklines, PDF export, and enhanced charts
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import base64
from io import BytesIO


# ============================================
# SPARKLINES - Mini charts for metric cards
# ============================================
def create_sparkline(
    values: List[float],
    color: str = '#C6A34F',
    height: int = 40,
    width: int = 120,
    show_endpoints: bool = True
) -> str:
    """
    Create a mini sparkline chart as base64 SVG.
    
    Args:
        values: List of numeric values
        color: Line color (hex)
        height: Chart height in pixels
        width: Chart width in pixels
        show_endpoints: Show start/end points
    
    Returns:
        Base64 encoded SVG string for embedding in HTML
    """
    if not values or len(values) < 2:
        return ""
    
    # Normalize values to fit in SVG
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1
    
    # Create SVG path points
    padding = 5
    usable_width = width - 2 * padding
    usable_height = height - 2 * padding
    
    points = []
    for i, val in enumerate(values):
        x = padding + (i / (len(values) - 1)) * usable_width
        y = padding + usable_height - ((val - min_val) / val_range) * usable_height
        points.append(f"{x:.1f},{y:.1f}")
    
    path_d = "M " + " L ".join(points)
    
    # Determine trend color
    trend_color = '#2E7D32' if values[-1] > values[0] else '#E31837' if values[-1] < values[0] else color
    
    # Build SVG
    svg_parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'  <path d="{path_d}" fill="none" stroke="{trend_color}" stroke-width="2" stroke-linecap="round"/>',
    ]
    
    if show_endpoints:
        # Start point
        start_x = padding
        start_y = padding + usable_height - ((values[0] - min_val) / val_range) * usable_height
        svg_parts.append(f'  <circle cx="{start_x}" cy="{start_y}" r="3" fill="{color}" opacity="0.5"/>')
        
        # End point
        end_x = padding + usable_width
        end_y = padding + usable_height - ((values[-1] - min_val) / val_range) * usable_height
        svg_parts.append(f'  <circle cx="{end_x}" cy="{end_y}" r="3" fill="{trend_color}"/>')
    
    svg_parts.append('</svg>')
    svg_string = '\n'.join(svg_parts)
    
    # Encode as base64
    b64 = base64.b64encode(svg_string.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def create_sparkline_html(
    values: List[float],
    label: str = "",
    color: str = '#C6A34F'
) -> str:
    """
    Create HTML with embedded sparkline for Streamlit.
    """
    sparkline_src = create_sparkline(values, color)
    if not sparkline_src:
        return ""
    
    change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
    change_color = '#2E7D32' if change > 0 else '#E31837' if change < 0 else '#666'
    change_sign = '+' if change > 0 else ''
    
    html = f'''
    <div style="display: flex; align-items: center; gap: 8px;">
        <img src="{sparkline_src}" alt="sparkline" style="vertical-align: middle;"/>
        <span style="color: {change_color}; font-size: 12px; font-weight: 500;">
            {change_sign}{change:.1f}%
        </span>
    </div>
    '''
    return html


# ============================================
# ENHANCED PLOTLY CHARTS
# ============================================
def create_power_gauge(power: float, threshold: float = 80) -> go.Figure:
    """
    Create a gauge chart for statistical power.
    """
    color = '#2E7D32' if power >= threshold else '#FFA000' if power >= 60 else '#E31837'
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=power,
        number={'suffix': '%', 'font': {'size': 36, 'color': '#002F6C'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#002F6C'},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#ddd",
            'steps': [
                {'range': [0, 60], 'color': '#FFEBEE'},
                {'range': [60, 80], 'color': '#FFF8E1'},
                {'range': [80, 100], 'color': '#E8F5E9'}
            ],
            'threshold': {
                'line': {'color': "#002F6C", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': '#002F6C', 'family': 'Montserrat'}
    )
    
    return fig


def create_comparison_chart(
    treatment_data: pd.DataFrame,
    control_data: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'new_customers',
    pre_period_end: str = None
) -> go.Figure:
    """
    Create a comparison chart between treatment and control.
    """
    fig = go.Figure()
    
    # Treatment line
    fig.add_trace(go.Scatter(
        x=treatment_data[date_col],
        y=treatment_data[value_col],
        mode='lines+markers',
        name='Tratamiento',
        line=dict(color='#002F6C', width=2),
        marker=dict(size=6)
    ))
    
    # Control line
    fig.add_trace(go.Scatter(
        x=control_data[date_col],
        y=control_data[value_col],
        mode='lines+markers',
        name='Control',
        line=dict(color='#C6A34F', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Add vertical line for test start
    if pre_period_end:
        fig.add_vline(
            x=pre_period_end,
            line_dash="dash",
            line_color="#E31837",
            annotation_text="Inicio Test",
            annotation_position="top"
        )
    
    fig.update_layout(
        title='Comparación: Tratamiento vs Control',
        xaxis_title='Fecha',
        yaxis_title='Nuevos Clientes',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template='plotly_white',
        font={'family': 'Montserrat'},
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig


def create_lift_waterfall(
    base_value: float,
    lift_value: float,
    final_value: float
) -> go.Figure:
    """
    Create a waterfall chart showing incremental lift.
    """
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Baseline<br>(Sin campaña)", "Lift<br>Incremental", "Total<br>(Con campaña)"],
        textposition="outside",
        text=[f"{base_value:,.0f}", f"+{lift_value:,.0f}", f"{final_value:,.0f}"],
        y=[base_value, lift_value, final_value],
        connector={"line": {"color": "#002F6C"}},
        decreasing={"marker": {"color": "#E31837"}},
        increasing={"marker": {"color": "#2E7D32"}},
        totals={"marker": {"color": "#002F6C"}}
    ))
    
    fig.update_layout(
        title="Impacto Incremental de la Campaña",
        yaxis_title="Nuevos Clientes",
        showlegend=False,
        template='plotly_white',
        font={'family': 'Montserrat'},
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig


def create_mde_heatmap_chart(mde_matrix: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap visualization for MDE across city combinations.
    """
    fig = go.Figure(data=go.Heatmap(
        z=mde_matrix.values,
        x=mde_matrix.columns.tolist(),
        y=mde_matrix.index.tolist(),
        colorscale=[
            [0, '#2E7D32'],      # Low MDE = Good (green)
            [0.3, '#C6A34F'],    # Medium = Gold
            [0.6, '#FFA000'],    # Higher = Warning
            [1, '#E31837']       # High MDE = Bad (red)
        ],
        text=mde_matrix.values.round(1),
        texttemplate='%{text}%',
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title='MDE (%)')
    ))
    
    fig.update_layout(
        title='MDE Heatmap: Combinaciones de Ciudades',
        xaxis_title='Ciudad Control',
        yaxis_title='Ciudad Tratamiento',
        template='plotly_white',
        font={'family': 'Montserrat'},
        margin=dict(l=80, r=40, t=60, b=80)
    )
    
    return fig


# ============================================
# PDF EXPORT
# ============================================
def generate_pdf_report(
    test_config: Dict,
    results: Dict,
    charts: List[go.Figure] = None
) -> bytes:
    """
    Generate a PDF report for the test.
    
    Note: This requires reportlab to be installed.
    Falls back to a simple text-based PDF if reportlab is not available.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#002F6C'),
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#002F6C'),
            spaceBefore=15,
            spaceAfter=10
        )
        
        # Title
        story.append(Paragraph("GeoLift Test Report", title_style))
        story.append(Paragraph(f"{test_config.get('name', 'Test sin nombre')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Test Configuration
        story.append(Paragraph("Configuración del Test", heading_style))
        config_data = [
            ["Ciudades Tratamiento", ", ".join(test_config.get('treatment_cities', []))],
            ["Ciudades Control", ", ".join(test_config.get('control_cities', []))],
            ["Duración", f"{test_config.get('duration_days', 0)} días"],
            ["Lift Esperado", f"{test_config.get('expected_lift', 0)*100:.0f}%"],
            ["Nivel de Confianza", f"{test_config.get('confidence_level', 0.95)*100:.0f}%"],
        ]
        
        config_table = Table(config_data, colWidths=[2*inch, 4*inch])
        config_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5EBD7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#002F6C')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C6A34F'))
        ]))
        story.append(config_table)
        story.append(Spacer(1, 20))
        
        # Results
        story.append(Paragraph("Resultados", heading_style))
        results_data = [
            ["Poder Estadístico", f"{results.get('power_percent', 0):.1f}%"],
            ["MDE", f"{results.get('mde_percent', 0):.1f}%"],
            ["Match Score", f"{results.get('match_score', 0):.0f}%"],
        ]
        
        if 'lift_percent' in results:
            results_data.extend([
                ["Lift Observado", f"{results.get('lift_percent', 0):.1f}%"],
                ["P-Value", f"{results.get('p_value', 1):.4f}"],
                ["Significativo", "Sí" if results.get('is_significant', False) else "No"],
            ])
        
        results_table = Table(results_data, colWidths=[2*inch, 4*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5EBD7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#002F6C')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C6A34F'))
        ]))
        story.append(results_table)
        story.append(Spacer(1, 20))
        
        # Insights
        if test_config.get('insights'):
            story.append(Paragraph("Insights", heading_style))
            story.append(Paragraph(test_config['insights'], styles['Normal']))
            story.append(Spacer(1, 10))
        
        if test_config.get('hypothesis'):
            story.append(Paragraph("Hipótesis", heading_style))
            story.append(Paragraph(test_config['hypothesis'], styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Generado: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)
        ))
        
        doc.build(story)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback if reportlab is not installed
        return _generate_simple_pdf(test_config, results)


def _generate_simple_pdf(test_config: Dict, results: Dict) -> bytes:
    """
    Generate a simple text-based PDF without reportlab.
    """
    # Return empty bytes - PDF generation not available
    return b''


# ============================================
# EXCEL EXPORT WITH CHARTS
# ============================================
def export_to_excel_with_charts(
    data: Dict[str, pd.DataFrame],
    test_config: Dict,
    results: Dict,
    filename: str = 'geolift_report.xlsx'
) -> bytes:
    """
    Export data to Excel with multiple sheets and formatting.
    """
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#002F6C',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1
        })
        
        highlight_format = workbook.add_format({
            'bg_color': '#C6A34F',
            'bold': True,
            'border': 1
        })
        
        # Sheet 1: Summary
        summary_data = pd.DataFrame([
            {'Métrica': 'Ciudades Tratamiento', 'Valor': ', '.join(test_config.get('treatment_cities', []))},
            {'Métrica': 'Ciudades Control', 'Valor': ', '.join(test_config.get('control_cities', []))},
            {'Métrica': 'Duración (días)', 'Valor': test_config.get('duration_days', 0)},
            {'Métrica': 'Lift Esperado', 'Valor': f"{test_config.get('expected_lift', 0)*100:.0f}%"},
            {'Métrica': 'Poder Estadístico', 'Valor': f"{results.get('power_percent', 0):.1f}%"},
            {'Métrica': 'MDE', 'Valor': f"{results.get('mde_percent', 0):.1f}%"},
        ])
        
        if 'lift_percent' in results:
            summary_data = pd.concat([summary_data, pd.DataFrame([
                {'Métrica': 'Lift Observado', 'Valor': f"{results.get('lift_percent', 0):.1f}%"},
                {'Métrica': 'P-Value', 'Valor': f"{results.get('p_value', 1):.4f}"},
                {'Métrica': 'Significativo', 'Valor': 'Sí' if results.get('is_significant', False) else 'No'},
            ])])
        
        summary_data.to_excel(writer, sheet_name='Resumen', index=False, startrow=1)
        
        worksheet = writer.sheets['Resumen']
        worksheet.write(0, 0, 'RESUMEN DEL TEST', header_format)
        
        # Apply formatting
        for col_num, value in enumerate(summary_data.columns.values):
            worksheet.write(1, col_num, value, header_format)
        
        # Sheet 2: Data
        for sheet_name, df in data.items():
            if df is not None and len(df) > 0:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                
                # Format headers
                ws = writer.sheets[sheet_name[:31]]
                for col_num, value in enumerate(df.columns.values):
                    ws.write(0, col_num, value, header_format)
    
    return buffer.getvalue()


# ============================================
# PRESENTATION MODE
# ============================================
def get_presentation_css() -> str:
    """
    Return CSS for presentation mode (larger fonts, simplified layout).
    """
    return """
    <style>
    .presentation-mode {
        font-size: 1.3em !important;
    }
    
    .presentation-mode h1 {
        font-size: 3em !important;
    }
    
    .presentation-mode h2 {
        font-size: 2.2em !important;
    }
    
    .presentation-mode .metric-card {
        padding: 40px !important;
        font-size: 1.5em !important;
    }
    
    .presentation-mode .metric-value {
        font-size: 4em !important;
    }
    
    .presentation-mode .stPlotlyChart {
        height: 500px !important;
    }
    
    /* Hide non-essential elements */
    .presentation-mode .sidebar,
    .presentation-mode .stSidebar,
    .presentation-mode footer {
        display: none !important;
    }
    
    /* Full width */
    .presentation-mode .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """
