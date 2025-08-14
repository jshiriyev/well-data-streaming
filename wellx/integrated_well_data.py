import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import base64

# Page configuration
st.set_page_config(
    page_title="Petroleum Well Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class WellDashboard:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'well_data' not in st.session_state:
            st.session_state.well_data = {
                'well_name': 'Well-001',
                'field': 'Example Field',
                'operator': 'ABC Oil & Gas',
                'spud_date': '2023-01-15',
                'completion_date': '2023-03-10',
                'current_status': 'Producing',
                'total_depth': 9245,
                'casing_size': '7" x 5.5"'
            }
        
        if 'production_data' not in st.session_state:
            st.session_state.production_data = self.generate_sample_production_data()
            
        if 'formation_data' not in st.session_state:
            st.session_state.formation_data = self.generate_sample_formation_data()
            
        if 'intervention_data' not in st.session_state:
            st.session_state.intervention_data = self.generate_sample_intervention_data()
    
    def generate_sample_production_data(self):
        """Generate sample production data"""
        dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='D')
        np.random.seed(42)
        
        # Base production with decline
        oil_base = 150
        gas_base = 800
        water_base = 50
        pressure_base = 2500
        temp_base = 180
        
        data = []
        for i, date in enumerate(dates):
            decline_factor = 0.998 ** i  # 0.2% daily decline
            noise = 1 + np.random.normal(0, 0.05)  # 5% noise
            
            oil = oil_base * decline_factor * noise
            gas = gas_base * decline_factor * noise
            water = water_base * (1 + i * 0.001) * noise  # Water cut increase
            pressure = pressure_base * decline_factor * (1 + np.random.normal(0, 0.02))
            temperature = temp_base + np.random.normal(0, 5)
            
            data.append({
                'date': date,
                'oil_rate': max(0, oil),
                'gas_rate': max(0, gas),
                'water_rate': max(0, water),
                'pressure': max(0, pressure),
                'temperature': temperature,
                'total_fluid': oil + water,
                'gor': gas/oil if oil > 0 else 0,
                'water_cut': water/(oil + water) if (oil + water) > 0 else 0
            })
        
        return pd.DataFrame(data)
    
    def generate_sample_formation_data(self):
        """Generate sample formation data"""
        return pd.DataFrame([
            {'depth': 8500, 'formation': 'Reservoir A', 'porosity': 18, 'permeability': 250, 'saturation': 65, 'net_pay': 45},
            {'depth': 8750, 'formation': 'Reservoir B', 'porosity': 22, 'permeability': 180, 'saturation': 70, 'net_pay': 38},
            {'depth': 9000, 'formation': 'Reservoir C', 'porosity': 15, 'permeability': 120, 'saturation': 55, 'net_pay': 28}
        ])
    
    def generate_sample_intervention_data(self):
        """Generate sample intervention data"""
        return pd.DataFrame([
            {'date': '2024-01-15', 'type': 'Workover', 'description': 'Tubing replacement', 'cost': 85000, 'duration': 3},
            {'date': '2024-03-22', 'type': 'Stimulation', 'description': 'Acid stimulation', 'cost': 45000, 'duration': 1},
            {'date': '2024-05-10', 'type': 'PLT', 'description': 'Production logging', 'cost': 25000, 'duration': 2}
        ])
    
    def render_sidebar(self):
        """Render sidebar with well information and controls"""
        st.sidebar.header("🛢️ Well Information")
        
        # Well basic info
        well_data = st.session_state.well_data
        st.sidebar.text_input("Well Name", value=well_data['well_name'], key="well_name_input")
        st.sidebar.text_input("Field", value=well_data['field'], key="field_input")
        st.sidebar.text_input("Operator", value=well_data['operator'], key="operator_input")
        
        st.sidebar.divider()
        
        # Data upload section
        st.sidebar.header("📊 Data Management")
        
        uploaded_production = st.sidebar.file_uploader(
            "Upload Production Data", 
            type=['csv', 'xlsx'], 
            help="Upload production data in CSV or Excel format"
        )
        
        uploaded_formation = st.sidebar.file_uploader(
            "Upload Formation Data", 
            type=['csv', 'xlsx'],
            help="Upload formation analysis data"
        )
        
        if uploaded_production:
            self.load_production_data(uploaded_production)
        
        if uploaded_formation:
            self.load_formation_data(uploaded_formation)
        
        st.sidebar.divider()
        
        # Analysis options
        st.sidebar.header("⚙️ Analysis Options")
        analysis_period = st.sidebar.selectbox(
            "Analysis Period",
            ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All data"]
        )
        
        return analysis_period
    
    def load_production_data(self, uploaded_file):
        """Load production data from uploaded file"""
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Validate and process the data
            df['date'] = pd.to_datetime(df['date'])
            st.session_state.production_data = df
            st.sidebar.success("Production data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {str(e)}")
    
    def load_formation_data(self, uploaded_file):
        """Load formation data from uploaded file"""
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.formation_data = df
            st.sidebar.success("Formation data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {str(e)}")
    
    def render_header(self):
        """Render main header"""
        well_data = st.session_state.well_data
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title(f"🛢️ {well_data['well_name']}")
            st.caption(f"{well_data['field']} | {well_data['operator']}")
        
        with col2:
            if st.button("📄 Generate Report", type="primary"):
                self.generate_pdf_report()
        
        with col3:
            if st.button("📥 Export Data"):
                self.export_data()
    
    def render_production_tab(self):
        """Render production analysis tab"""
        st.header("📈 Production Analytics")
        
        production_data = st.session_state.production_data
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        latest_data = production_data.iloc[-1]
        
        with col1:
            st.metric(
                "Oil Rate", 
                f"{latest_data['oil_rate']:.1f} bbl/d",
                delta=f"{latest_data['oil_rate'] - production_data.iloc[-30]['oil_rate']:.1f}"
            )
        
        with col2:
            st.metric(
                "Gas Rate", 
                f"{latest_data['gas_rate']:.0f} Mcf/d",
                delta=f"{latest_data['gas_rate'] - production_data.iloc[-30]['gas_rate']:.0f}"
            )
        
        with col3:
            st.metric(
                "Water Cut", 
                f"{latest_data['water_cut']*100:.1f}%",
                delta=f"{(latest_data['water_cut'] - production_data.iloc[-30]['water_cut'])*100:.1f}%"
            )
        
        with col4:
            st.metric(
                "Pressure", 
                f"{latest_data['pressure']:.0f} psi",
                delta=f"{latest_data['pressure'] - production_data.iloc[-30]['pressure']:.0f}"
            )
        
        # Production trends
        col1, col2 = st.columns(2)
        
        with col1:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Production Rates', 'Pressure & Temperature'),
                vertical_spacing=0.1
            )
            
            # Production rates
            fig.add_trace(
                go.Scatter(x=production_data['date'], y=production_data['oil_rate'], 
                          name='Oil Rate', line=dict(color='green')), row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=production_data['date'], y=production_data['gas_rate']/10, 
                          name='Gas Rate (÷10)', line=dict(color='blue')), row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=production_data['date'], y=production_data['water_rate'], 
                          name='Water Rate', line=dict(color='red')), row=1, col=1
            )
            
            # Pressure and temperature
            fig.add_trace(
                go.Scatter(x=production_data['date'], y=production_data['pressure'], 
                          name='Pressure', line=dict(color='purple')), row=2, col=1
            )
            
            fig.update_layout(height=600, title_text="Production Trends")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Decline curve analysis
            fig = px.scatter(
                production_data, 
                x='date', 
                y='oil_rate',
                title='Oil Rate Decline Analysis',
                trendline='ols'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            # Water cut analysis
            fig = px.line(
                production_data, 
                x='date', 
                y='water_cut',
                title='Water Cut Trend',
                labels={'water_cut': 'Water Cut (fraction)'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_reservoir_tab(self):
        """Render reservoir analysis tab"""
        st.header("🗻 Reservoir Analysis")
        
        formation_data = st.session_state.formation_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Formation Properties")
            st.dataframe(formation_data, use_container_width=True)
            
            # Porosity vs Permeability
            fig = px.scatter(
                formation_data, 
                x='porosity', 
                y='permeability',
                size='net_pay',
                color='formation',
                title='Porosity vs Permeability',
                labels={'porosity': 'Porosity (%)', 'permeability': 'Permeability (mD)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Formation tops visualization
            fig = go.Figure()
            
            for _, row in formation_data.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['formation']],
                    y=[row['net_pay']],
                    name=row['formation'],
                    text=f"{row['depth']} ft",
                    textposition='auto'
                ))
            
            fig.update_layout(
                title='Net Pay by Formation',
                xaxis_title='Formation',
                yaxis_title='Net Pay (ft)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Reservoir quality index
            formation_data['rqi'] = formation_data['permeability'] * formation_data['porosity'] / 100
            
            fig = px.bar(
                formation_data, 
                x='formation', 
                y='rqi',
                title='Reservoir Quality Index',
                color='rqi',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_intervention_tab(self):
        """Render intervention analysis tab"""
        st.header("🔧 Intervention Analysis")
        
        intervention_data = st.session_state.intervention_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Intervention History")
            st.dataframe(intervention_data, use_container_width=True)
            
            # Total costs
            total_cost = intervention_data['cost'].sum()
            st.metric("Total Intervention Cost", f"${total_cost:,.0f}")
            
        with col2:
            # Cost by intervention type
            fig = px.pie(
                intervention_data, 
                values='cost', 
                names='type',
                title='Intervention Costs by Type'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Timeline
            fig = px.timeline(
                intervention_data,
                x_start='date',
                x_end='date',
                y='type',
                color='cost',
                title='Intervention Timeline'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_analysis_tab(self):
        """Render advanced analysis tab"""
        st.header("🧪 Advanced Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Core Analysis Upload")
            core_file = st.file_uploader("Upload Core Analysis", type=['csv', 'xlsx', 'las'])
            
            st.subheader("Fluid Analysis Upload")
            fluid_file = st.file_uploader("Upload Fluid Analysis", type=['csv', 'xlsx'])
            
        with col2:
            st.subheader("Well Logs Upload")
            log_file = st.file_uploader("Upload Well Logs", type=['las', 'csv'])
            
            st.subheader("Formation Tops")
            tops_file = st.file_uploader("Upload Formation Tops", type=['csv', 'xlsx'])
        
        # PVT Analysis section
        st.subheader("PVT Analysis")
        
        # Sample PVT data
        pvt_data = pd.DataFrame({
            'pressure': np.linspace(1000, 3000, 20),
            'oil_fvf': 1.2 + 0.0002 * np.linspace(1000, 3000, 20),
            'gas_fvf': 0.8 + 0.0001 * np.linspace(1000, 3000, 20),
            'solution_gor': 500 + 0.1 * np.linspace(1000, 3000, 20)
        })
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Oil FVF', 'Gas FVF', 'Solution GOR', 'Viscosity'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['oil_fvf'], name='Oil FVF'), row=1, col=1)
        fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['gas_fvf'], name='Gas FVF'), row=1, col=2)
        fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['solution_gor'], name='Solution GOR'), row=2, col=1)
        
        fig.update_layout(height=600, title_text="PVT Properties")
        st.plotly_chart(fig, use_container_width=True)
    
    def generate_pdf_report(self):
        """Generate PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Well Report - {st.session_state.well_data['well_name']}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Well info
        well_info = f"""
        Field: {st.session_state.well_data['field']}<br/>
        Operator: {st.session_state.well_data['operator']}<br/>
        Status: {st.session_state.well_data['current_status']}<br/>
        Report Date: {datetime.now().strftime('%Y-%m-%d')}
        """
        story.append(Paragraph(well_info, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Production summary
        production_data = st.session_state.production_data
        latest = production_data.iloc[-1]
        
        prod_table_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Oil Rate', f"{latest['oil_rate']:.1f}", 'bbl/d'],
            ['Gas Rate', f"{latest['gas_rate']:.0f}", 'Mcf/d'],
            ['Water Rate', f"{latest['water_rate']:.1f}", 'bbl/d'],
            ['Pressure', f"{latest['pressure']:.0f}", 'psi']
        ]
        
        table = Table(prod_table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
        buffer.seek(0)
        
        st.download_button(
            label="📄 Download PDF Report",
            data=buffer.getvalue(),
            file_name=f"well_report_{st.session_state.well_data['well_name']}.pdf",
            mime="application/pdf"
        )
    
    def export_data(self):
        """Export data to Excel"""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.production_data.to_excel(writer, sheet_name='Production', index=False)
            st.session_state.formation_data.to_excel(writer, sheet_name='Formation', index=False)
            st.session_state.intervention_data.to_excel(writer, sheet_name='Interventions', index=False)
        
        buffer.seek(0)
        
        st.download_button(
            label="📊 Download Excel Data",
            data=buffer.getvalue(),
            file_name=f"well_data_{st.session_state.well_data['well_name']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    def run(self):
        """Main application runner"""
        # Render sidebar
        analysis_period = self.render_sidebar()
        
        # Render header
        self.render_header()
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Production", 
            "🗻 Reservoir", 
            "🔧 Interventions", 
            "📊 Construction",
            "🧪 Analysis"
        ])
        
        with tab1:
            self.render_production_tab()
        
        with tab2:
            self.render_reservoir_tab()
        
        with tab3:
            self.render_intervention_tab()
        
        with tab4:
            st.header("🏗️ Well Construction")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Well Details")
                well_data = st.session_state.well_data
                
                construction_info = pd.DataFrame([
                    ['Spud Date', well_data['spud_date']],
                    ['Completion Date', well_data['completion_date']],
                    ['Total Depth', f"{well_data['total_depth']} ft"],
                    ['Casing Size', well_data['casing_size']],
                    ['Status', well_data['current_status']]
                ], columns=['Parameter', 'Value'])
                
                st.dataframe(construction_info, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("Completion Schematic")
                st.info("Upload completion diagram or well schematic here")
                completion_file = st.file_uploader("Upload Completion Diagram", type=['pdf', 'png', 'jpg'])
        
        with tab5:
            self.render_analysis_tab()

# Run the application
if __name__ == "__main__":
    dashboard = WellDashboard()
    dashboard.run()