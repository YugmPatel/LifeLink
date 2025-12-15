#!/usr/bin/env python3
"""
Model Evaluation and Comparison for LifeLink Protocol Classification.
Compares custom ML model performance with Groq AI baseline.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import asyncio
from datetime import datetime
import os

# ML evaluation imports
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_curve, auc, precision_recall_curve,
    accuracy_score, precision_recall_fscore_support
)

# LifeLink imports
import sys
sys.path.append('..')
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lifelink.clients import GroqAnalyzer

class LifeLinkModelEvaluator:
    """Comprehensive model evaluation and comparison system."""
    
    def __init__(self):
        self.groq_analyzer = GroqAnalyzer()
        self.results = {}
        self.comparison_data = []
        
    def load_test_data(self, test_path="data/test_balanced.csv"):
        """Load test dataset for evaluation."""
        
        if not os.path.exists(test_path):
            print("❌ Test data not found. Generating...")
            # Generate realistic test data if not exists
            from ml_pipeline.generate_balanced_data import generate_balanced_dataset, save_balanced_dataset
            dataset = generate_balanced_dataset(n_samples=500)
            save_balanced_dataset(dataset)
        
        df = pd.read_csv(test_path)
        print(f"✅ Loaded {len(df)} test samples")
        return df
    
    async def evaluate_groq_baseline(self, test_df):
        """Evaluate Groq AI performance on test set."""
        
        print("🤖 Evaluating Groq AI baseline...")
        
        groq_predictions = []
        groq_confidences = []
        
        for idx, row in test_df.iterrows():
            try:
                # Get Groq prediction
                result = await self.groq_analyzer.analyze_ambulance_report(
                    report=row['report_text'],
                    hospital_status={}
                )
                
                predicted_protocol = result.get('protocol', 'General')
                confidence = result.get('urgency', 3) / 5.0  # Normalize urgency as confidence
                
                groq_predictions.append(predicted_protocol)
                groq_confidences.append(confidence)
                
                if idx % 50 == 0:
                    print(f"   Processed {idx+1}/{len(test_df)} samples...")
                    
            except Exception as e:
                print(f"   Error processing sample {idx}: {e}")
                groq_predictions.append('General')
                groq_confidences.append(0.5)
        
        # Calculate metrics
        y_true = test_df['protocol'].values
        y_pred = groq_predictions
        
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
        
        groq_results = {
            'model_name': 'Groq AI',
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'predictions': y_pred,
            'confidences': groq_confidences,
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
        
        print(f"✅ Groq AI Results: Accuracy={accuracy:.3f}, F1={f1:.3f}")
        
        return groq_results
    
    def evaluate_custom_model(self, test_df, model_path="artifacts"):
        """Evaluate custom trained model."""
        
        print("🔬 Evaluating custom model...")
        
        try:
            import joblib
            
            # Load model artifacts
            model = joblib.load(f"{model_path}/lifelink_protocol_classifier.pkl")
            vectorizer = joblib.load(f"{model_path}/tfidf_vectorizer.pkl")
            label_encoder = joblib.load(f"{model_path}/label_encoder.pkl")
            
            # Prepare data
            X_test = vectorizer.transform(test_df['report_text'])
            y_true = label_encoder.transform(test_df['protocol'])
            
            # Predict
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_true, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
            
            # Convert back to protocol names
            y_true_names = label_encoder.inverse_transform(y_true)
            y_pred_names = label_encoder.inverse_transform(y_pred)
            
            custom_results = {
                'model_name': 'Custom ML Model',
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'predictions': y_pred_names,
                'probabilities': y_pred_proba,
                'classification_report': classification_report(y_true_names, y_pred_names, output_dict=True)
            }
            
            print(f"✅ Custom Model Results: Accuracy={accuracy:.3f}, F1={f1:.3f}")
            
            return custom_results
            
        except Exception as e:
            print(f"❌ Error evaluating custom model: {e}")
            return None
    
    def create_confusion_matrix_plot(self, y_true, y_pred, model_name, class_names):
        """Create confusion matrix visualization."""
        
        cm = confusion_matrix(y_true, y_pred)
        
        fig = px.imshow(
            cm,
            labels=dict(x="Predicted", y="Actual", color="Count"),
            x=class_names,
            y=class_names,
            color_continuous_scale="Blues",
            title=f"Confusion Matrix - {model_name}"
        )
        
        # Add text annotations
        for i in range(len(class_names)):
            for j in range(len(class_names)):
                fig.add_annotation(
                    x=j, y=i,
                    text=str(cm[i, j]),
                    showarrow=False,
                    font=dict(color="white" if cm[i, j] > cm.max()/2 else "black")
                )
        
        return fig
    
    def create_metrics_comparison_plot(self, results_list):
        """Create model comparison visualization."""
        
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        fig = go.Figure()
        
        for result in results_list:
            if result:
                fig.add_trace(go.Scatterpolar(
                    r=[result[metric] for metric in metrics],
                    theta=metrics,
                    fill='toself',
                    name=result['model_name']
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Model Performance Comparison"
        )
        
        return fig
    
    def create_classification_report_plot(self, classification_report, model_name):
        """Create classification report visualization."""
        
        # Extract metrics for each class
        classes = [k for k in classification_report.keys() if k not in ['accuracy', 'macro avg', 'weighted avg']]
        
        metrics_data = []
        for cls in classes:
            metrics_data.append({
                'Class': cls,
                'Precision': classification_report[cls]['precision'],
                'Recall': classification_report[cls]['recall'],
                'F1-Score': classification_report[cls]['f1-score']
            })
        
        df_metrics = pd.DataFrame(metrics_data)
        
        fig = px.bar(
            df_metrics.melt(id_vars=['Class'], var_name='Metric', value_name='Score'),
            x='Class',
            y='Score',
            color='Metric',
            barmode='group',
            title=f"Per-Class Performance - {model_name}",
            range_y=[0, 1]
        )
        
        return fig
    
    def generate_evaluation_report(self, groq_results, custom_results, test_df):
        """Generate comprehensive evaluation report."""
        
        print("📊 Generating evaluation report...")
        
        # Create visualizations
        class_names = test_df['protocol'].unique()
        
        visualizations = {}
        
        # Confusion matrices
        if groq_results:
            visualizations['groq_confusion'] = self.create_confusion_matrix_plot(
                test_df['protocol'], groq_results['predictions'], 
                'Groq AI', class_names
            )
            visualizations['groq_classification'] = self.create_classification_report_plot(
                groq_results['classification_report'], 'Groq AI'
            )
        
        if custom_results:
            visualizations['custom_confusion'] = self.create_confusion_matrix_plot(
                test_df['protocol'], custom_results['predictions'],
                'Custom ML Model', class_names
            )
            visualizations['custom_classification'] = self.create_classification_report_plot(
                custom_results['classification_report'], 'Custom ML Model'
            )
        
        # Model comparison
        results_list = [r for r in [groq_results, custom_results] if r is not None]
        if len(results_list) > 1:
            visualizations['comparison'] = self.create_metrics_comparison_plot(results_list)
        
        # Performance summary
        summary = {
            'evaluation_timestamp': datetime.now().isoformat(),
            'test_samples': len(test_df),
            'class_distribution': test_df['protocol'].value_counts().to_dict(),
            'models_evaluated': len(results_list)
        }
        
        if groq_results:
            summary['groq_performance'] = {
                'accuracy': groq_results['accuracy'],
                'f1_score': groq_results['f1_score']
            }
        
        if custom_results:
            summary['custom_performance'] = {
                'accuracy': custom_results['accuracy'],
                'f1_score': custom_results['f1_score']
            }
        
        # Save results
        os.makedirs('evaluation_results', exist_ok=True)
        
        # Save summary
        with open('evaluation_results/evaluation_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed results
        detailed_results = {
            'groq_results': groq_results,
            'custom_results': custom_results,
            'summary': summary
        }
        
        with open('evaluation_results/detailed_results.json', 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print("✅ Evaluation report generated!")
        print(f"📁 Results saved to: evaluation_results/")
        
        return summary, visualizations, detailed_results
    
    async def run_complete_evaluation(self):
        """Run complete model evaluation pipeline."""
        
        print("🚀 Starting LifeLink Model Evaluation")
        print("=" * 50)
        
        # Load test data
        test_df = self.load_test_data()
        
        # Evaluate Groq baseline
        groq_results = await self.evaluate_groq_baseline(test_df)
        
        # Evaluate custom model
        custom_results = self.evaluate_custom_model(test_df)
        
        # Generate report
        summary, visualizations, detailed_results = self.generate_evaluation_report(
            groq_results, custom_results, test_df
        )
        
        print("\n🎉 Evaluation Complete!")
        
        if groq_results and custom_results:
            print(f"📊 Groq AI: F1={groq_results['f1_score']:.3f}")
            print(f"🔬 Custom Model: F1={custom_results['f1_score']:.3f}")
            
            improvement = custom_results['f1_score'] - groq_results['f1_score']
            print(f"📈 Improvement: {improvement:+.3f}")
        
        return summary, visualizations, detailed_results

async def main():
    """Main function to run model evaluation."""
    
    evaluator = LifeLinkModelEvaluator()
    results = await evaluator.run_complete_evaluation()
    
    return results

if __name__ == "__main__":
    asyncio.run(main())