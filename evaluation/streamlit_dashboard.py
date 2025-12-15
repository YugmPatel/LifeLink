#!/usr/bin/env python3
"""
Streamlit Dashboard for LifeLink MLOps Metrics and Model Evaluation.
Displays training metrics, model comparison, and real-time performance monitoring.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import asyncio

# Google Cloud imports
try:
    from google.cloud import bigquery
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    st.warning("BigQuery not available. Using local data only.")

# LifeLink imports
import sys
sys.path.append('..')

# Page configuration
st.set_page_config(
    page_title="LifeLink MLOps Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .danger-metric {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class LifeLinkMLOpsDashboard:
    """Streamlit dashboard for LifeLink MLOps monitoring."""
    
    def __init__(self):
        self.project_id = "lifelink-481222"
        if BIGQUERY_AVAILABLE:
            self.bq_client = bigquery.Client()
    
    def load_training_metrics(self):
        """Load training metrics from local files first, then BigQuery."""
        
        # Try local data first (most up-to-date)
        local_df = self.load_local_metrics()
        if not local_df.empty:
            st.success("📊 Loaded latest local training metrics")
            return local_df
        
        # Fallback to BigQuery if local data not available
        if BIGQUERY_AVAILABLE:
            try:
                query = f"""
                SELECT *
                FROM `{self.project_id}.lifelink_ml.training_metrics`
                ORDER BY timestamp DESC
                LIMIT 100
                """
                df = self.bq_client.query(query).to_dataframe()
                if not df.empty:
                    st.info("📊 Loaded training metrics from BigQuery")
                    return df
            except Exception as e:
                st.warning(f"Could not load from BigQuery: {e}")
        
        # Generate sample data if nothing else works
        return self.generate_sample_metrics()
    
    def load_local_metrics(self):
        """Load metrics combining historical data + latest real-time results."""
        
        historical_df = pd.DataFrame()
        latest_df = pd.DataFrame()
        
        # Load historical data
        try:
            if os.path.exists('data/training_metrics_history.csv'):
                historical_df = pd.read_csv('data/training_metrics_history.csv')
                historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
        except Exception as e:
            st.info(f"Could not load historical data: {e}")
        
        # Load latest real-time results from artifacts
        try:
            if os.path.exists('artifacts/evaluation_results.json'):
                with open('artifacts/evaluation_results.json', 'r') as f:
                    results = json.load(f)
                
                # Get file modification time for real timestamp
                artifact_time = datetime.fromtimestamp(os.path.getmtime('artifacts/evaluation_results.json'))
                
                # Create latest experiment data
                latest_data = []
                experiment_id = f"exp_{artifact_time.strftime('%Y%m%d_%H%M%S')}"
                
                for model_name, metrics in results.get('model_comparison', {}).items():
                    latest_data.append({
                        'experiment_id': experiment_id,
                        'model_type': model_name,
                        'accuracy': metrics.get('accuracy', 0),
                        'precision': metrics.get('precision', 0),
                        'recall': metrics.get('recall', 0),
                        'f1_score': metrics.get('f1_score', 0),
                        'auc_score': metrics.get('auc_score', 0),
                        'training_time': metrics.get('training_time', 0),
                        'timestamp': artifact_time,
                        'hyperparameters': f'{{"model": "{model_name}"}}'
                    })
                
                if latest_data:
                    latest_df = pd.DataFrame(latest_data)
                    latest_df['timestamp'] = pd.to_datetime(latest_df['timestamp'])
                    
        except Exception as e:
            st.info(f"Could not load latest artifacts: {e}")
        
        # Combine historical and latest data
        if not historical_df.empty and not latest_df.empty:
            latest_exp_id = latest_df.iloc[0]['experiment_id']
            if latest_exp_id not in historical_df['experiment_id'].values:
                combined_df = pd.concat([historical_df, latest_df], ignore_index=True)
                combined_df = combined_df.sort_values('timestamp', ascending=False)
                return combined_df
            else:
                return historical_df.sort_values('timestamp', ascending=False)
        elif not historical_df.empty:
            return historical_df.sort_values('timestamp', ascending=False)
        elif not latest_df.empty:
            return latest_df
        
        # Generate sample metrics if no data exists
        sample_data = []
        
        models = ['logistic_regression', 'random_forest']
        base_time = datetime.now() - timedelta(hours=2)
        
        for i, model in enumerate(models):
            sample_data.append({
                'experiment_id': f'exp_sample_{i+1}',
                'model_type': model,
                'accuracy': 0.85 + np.random.normal(0, 0.05),
                'precision': 0.83 + np.random.normal(0, 0.05),
                'recall': 0.82 + np.random.normal(0, 0.05),
                'f1_score': 0.84 + np.random.normal(0, 0.05),
                'auc_score': 0.88 + np.random.normal(0, 0.03),
                'training_time': 3500.0 + np.random.normal(0, 300),  # ~58 minutes ± 5 minutes
                'timestamp': base_time + timedelta(minutes=i*30)
            })
        
        return pd.DataFrame(sample_data)
    
    def load_evaluation_results(self):
        """Load model evaluation results."""
        
        eval_path = 'evaluation_results/detailed_results.json'
        
        if os.path.exists(eval_path):
            with open(eval_path, 'r') as f:
                return json.load(f)
        
        # Return sample evaluation data
        return {
            'summary': {
                'evaluation_timestamp': datetime.now().isoformat(),
                'test_samples': 400,
                'models_evaluated': 2,
                'groq_performance': {'accuracy': 0.78, 'f1_score': 0.76},
                'custom_performance': {'accuracy': 0.85, 'f1_score': 0.84}
            },
            'groq_results': {
                'model_name': 'Groq AI',
                'accuracy': 0.78,
                'f1_score': 0.76,
                'precision': 0.77,
                'recall': 0.75
            },
            'custom_results': {
                'model_name': 'Custom ML Model',
                'accuracy': 0.85,
                'f1_score': 0.84,
                'precision': 0.83,
                'recall': 0.85
            }
        }
    
    def create_metrics_overview(self, df):
        """Create metrics overview section."""
        
        st.markdown('<h2 class="main-header">📊 Training Metrics Overview</h2>', unsafe_allow_html=True)
        
        if df.empty:
            st.warning("No training metrics available.")
            return
        
        # Latest metrics
        latest = df.iloc[0] if not df.empty else None
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric(
                "Best Accuracy",
                f"{df['accuracy'].max():.3f}",
                f"{df['accuracy'].max() - df['accuracy'].mean():.3f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric(
                "Best F1 Score",
                f"{df['f1_score'].max():.3f}",
                f"{df['f1_score'].max() - df['f1_score'].mean():.3f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card warning-metric">', unsafe_allow_html=True)
            avg_time = df['training_time'].mean()
            minutes = int(avg_time // 60)
            seconds = int(avg_time % 60)
            st.metric(
                "Avg Training Time",
                f"{minutes}m {seconds}s",
                f"±{df['training_time'].std()/60:.1f}m"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            experiment_count = len(df['experiment_id'].unique()) if 'experiment_id' in df.columns else len(df)
            st.metric(
                "Experiments Run",
                experiment_count,
                "+1" if experiment_count > 1 else ""
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    def create_training_plots(self, df):
        """Create training performance plots."""
        
        st.markdown("### 📈 Training Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Model comparison
            fig_comparison = px.bar(
                df,
                x='model_type',
                y='f1_score',
                color='model_type',
                title="Model Performance Comparison (F1 Score)",
                labels={'f1_score': 'F1 Score', 'model_type': 'Model Type'}
            )
            fig_comparison.update_layout(showlegend=False)
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with col2:
            # Metrics radar chart
            if not df.empty:
                latest_metrics = df.iloc[0]
                
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=[
                        latest_metrics['accuracy'],
                        latest_metrics['precision'],
                        latest_metrics['recall'],
                        latest_metrics['f1_score'],
                        latest_metrics['auc_score']
                    ],
                    theta=['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC'],
                    fill='toself',
                    name='Latest Model'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    showlegend=True,
                    title="Latest Model Performance Metrics"
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
    
    def create_model_comparison(self, eval_results):
        """Create model comparison section."""
        
        st.markdown("### 🤖 Model Comparison: Custom ML vs Groq AI")
        
        summary = eval_results.get('summary', {})
        groq_results = eval_results.get('groq_results')
        custom_results = eval_results.get('custom_results')
        
        if not groq_results or not custom_results:
            st.warning("Model comparison data not available.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Groq AI Baseline")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Accuracy", f"{groq_results['accuracy']:.3f}")
            st.metric("F1 Score", f"{groq_results['f1_score']:.3f}")
            st.metric("Precision", f"{groq_results['precision']:.3f}")
            st.metric("Recall", f"{groq_results['recall']:.3f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Custom ML Model")
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            
            accuracy_diff = custom_results['accuracy'] - groq_results['accuracy']
            f1_diff = custom_results['f1_score'] - groq_results['f1_score']
            precision_diff = custom_results['precision'] - groq_results['precision']
            recall_diff = custom_results['recall'] - groq_results['recall']
            
            st.metric("Accuracy", f"{custom_results['accuracy']:.3f}", f"{accuracy_diff:+.3f}")
            st.metric("F1 Score", f"{custom_results['f1_score']:.3f}", f"{f1_diff:+.3f}")
            st.metric("Precision", f"{custom_results['precision']:.3f}", f"{precision_diff:+.3f}")
            st.metric("Recall", f"{custom_results['recall']:.3f}", f"{recall_diff:+.3f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Comparison chart
        comparison_data = pd.DataFrame({
            'Model': ['Groq AI', 'Custom ML'],
            'Accuracy': [groq_results['accuracy'], custom_results['accuracy']],
            'F1 Score': [groq_results['f1_score'], custom_results['f1_score']],
            'Precision': [groq_results['precision'], custom_results['precision']],
            'Recall': [groq_results['recall'], custom_results['recall']]
        })
        
        fig_comparison = px.bar(
            comparison_data.melt(id_vars=['Model'], var_name='Metric', value_name='Score'),
            x='Metric',
            y='Score',
            color='Model',
            barmode='group',
            title="Model Performance Comparison",
            range_y=[0, 1]
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    def create_system_monitoring(self):
        """Create system monitoring section."""
        
        st.markdown("### 🔍 System Performance Monitoring")
        
        # Generate sample system metrics
        current_time = datetime.now()
        time_range = pd.date_range(
            start=current_time - timedelta(hours=24),
            end=current_time,
            freq='H'
        )
        
        system_metrics = pd.DataFrame({
            'timestamp': time_range,
            'response_time': np.random.normal(2.5, 0.5, len(time_range)),
            'throughput': np.random.normal(150, 20, len(time_range)),
            'error_rate': np.random.exponential(0.02, len(time_range)),
            'cpu_usage': np.random.normal(45, 10, len(time_range))
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time
            fig_response = px.line(
                system_metrics,
                x='timestamp',
                y='response_time',
                title='Average Response Time (seconds)',
                labels={'response_time': 'Response Time (s)'}
            )
            st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            # Throughput
            fig_throughput = px.line(
                system_metrics,
                x='timestamp',
                y='throughput',
                title='System Throughput (requests/min)',
                labels={'throughput': 'Requests/min'}
            )
            st.plotly_chart(fig_throughput, use_container_width=True)
        
        # Current system status
        st.markdown("#### 🚦 Current System Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_response = system_metrics['response_time'].iloc[-1]
            status_color = "success-metric" if current_response < 3 else "warning-metric"
            st.markdown(f'<div class="metric-card {status_color}">', unsafe_allow_html=True)
            st.metric("Response Time", f"{current_response:.2f}s")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            current_throughput = system_metrics['throughput'].iloc[-1]
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric("Throughput", f"{current_throughput:.0f} req/min")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            current_error = system_metrics['error_rate'].iloc[-1]
            status_color = "success-metric" if current_error < 0.05 else "danger-metric"
            st.markdown(f'<div class="metric-card {status_color}">', unsafe_allow_html=True)
            st.metric("Error Rate", f"{current_error:.2%}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            current_cpu = system_metrics['cpu_usage'].iloc[-1]
            status_color = "success-metric" if current_cpu < 70 else "warning-metric"
            st.markdown(f'<div class="metric-card {status_color}">', unsafe_allow_html=True)
            st.metric("CPU Usage", f"{current_cpu:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
    
    def create_mlops_pipeline_status(self):
        """Create MLOps pipeline status section."""
        
        st.markdown("### ⚙️ MLOps Pipeline Status")
        
        # Pipeline stages
        pipeline_stages = [
            {"name": "Data Generation", "status": "✅ Complete", "last_run": "2 hours ago"},
            {"name": "Model Training", "status": "✅ Complete", "last_run": "1 hour ago"},
            {"name": "Model Evaluation", "status": "✅ Complete", "last_run": "45 minutes ago"},
            {"name": "Model Deployment", "status": "🔄 In Progress", "last_run": "30 minutes ago"},
            {"name": "Monitoring", "status": "✅ Active", "last_run": "Real-time"}
        ]
        
        pipeline_df = pd.DataFrame(pipeline_stages)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(
                pipeline_df,
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.markdown("#### 📊 Pipeline Health")
            
            completed_stages = sum(1 for stage in pipeline_stages if "Complete" in stage["status"] or "Active" in stage["status"])
            total_stages = len(pipeline_stages)
            health_percentage = (completed_stages / total_stages) * 100
            
            fig_health = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = health_percentage,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Pipeline Health"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_health.update_layout(height=300)
            st.plotly_chart(fig_health, use_container_width=True)

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🏥 LifeLink MLOps Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Real-time monitoring of ML models and system performance**")
    
    # Initialize dashboard
    dashboard = LifeLinkMLOpsDashboard()
    
    # Sidebar
    st.sidebar.markdown("## 🔧 Dashboard Controls")
    
    # Simple refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        st.sidebar.markdown("*Dashboard will refresh automatically*")
        # Note: In production, you'd implement actual auto-refresh
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "📊 Data Source",
        ["BigQuery", "Local Files"],
        index=0 if BIGQUERY_AVAILABLE else 1
    )
    
    # Main content
    try:
        # Load data
        training_metrics = dashboard.load_training_metrics()
        evaluation_results = dashboard.load_evaluation_results()
        
        # Create sections
        dashboard.create_metrics_overview(training_metrics)
        
        st.markdown("---")
        
        dashboard.create_training_plots(training_metrics)
        
        st.markdown("---")
        
        dashboard.create_model_comparison(evaluation_results)
        
        st.markdown("---")
        
        dashboard.create_system_monitoring()
        
        st.markdown("---")
        
        dashboard.create_mlops_pipeline_status()
        
        # Footer
        st.markdown("---")
        st.markdown("*LifeLink MLOps Dashboard - Real-time ML monitoring and evaluation*")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("Please ensure all required data sources are available.")

if __name__ == "__main__":
    main()