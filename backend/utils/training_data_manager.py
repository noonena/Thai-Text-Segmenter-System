#!/usr/bin/env python3
"""
Training data manager for backend results
Handles accumulating and processing training data for model retraining
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import shutil

class TrainingDataManager:
    def __init__(self, results_dir: str = None):
        if results_dir is None:
            results_dir = Path(__file__).parent.parent / "results"
        
        self.results_dir = Path(results_dir)
        self.training_data_dir = self.results_dir / "training_data"
        self.user_exports_dir = self.results_dir / "user_exports"
        
        # Ensure directories exist
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        self.user_exports_dir.mkdir(parents=True, exist_ok=True)
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        """Load all accumulated training data"""
        cumulative_file = self.training_data_dir / "segmentation_results.json"
        
        if not cumulative_file.exists():
            return []
        
        try:
            with open(cumulative_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about accumulated training data"""
        data = self.get_training_data()
        
        if not data:
            return {
                "total_entries": 0,
                "date_range": None,
                "unique_users": 0,
                "avg_confidence": 0,
                "total_words": 0
            }
        
        dates = [datetime.fromisoformat(entry["timestamp"]) for entry in data]
        users = set(entry.get("user_id") for entry in data if entry.get("user_id"))
        confidences = [entry.get("confidence", 0) for entry in data]
        word_counts = [entry.get("word_count", 0) for entry in data]
        
        return {
            "total_entries": len(data),
            "date_range": {
                "start": min(dates).isoformat(),
                "end": max(dates).isoformat()
            },
            "unique_users": len(users),
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "total_words": sum(word_counts)
        }
    
    def export_for_retraining(self, output_path: str = None) -> str:
        """Export training data in format suitable for model retraining"""
        data = self.get_training_data()
        
        if not data:
            raise ValueError("No training data available for export")
        
        # Transform data for CRF training format
        training_samples = []
        for entry in data:
            if entry.get("segmented_words"):
                training_samples.append({
                    "text": entry["original_text"],
                    "words": entry["segmented_words"],
                    "confidence": entry.get("confidence", 0.95),
                    "timestamp": entry["timestamp"]
                })
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.training_data_dir / f"crf_retraining_data_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "total_samples": len(training_samples),
                    "source": "user_processing_results"
                },
                "samples": training_samples
            }, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def cleanup_old_exports(self, days_to_keep: int = 7):
        """Clean up old export files from user_exports directory"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file_path in self.user_exports_dir.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    print(f"Cleaned up old export: {file_path.name}")
    
    def create_user_export(self, data: List[Dict], export_format: str = "json") -> str:
        """Create export file for user download"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_export_{timestamp}.{export_format}"
        export_path = self.user_exports_dir / filename
        
        if export_format == "json":
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            # Add other formats as needed
            raise ValueError(f"Unsupported export format: {export_format}")
        
        return str(export_path)

if __name__ == "__main__":
    # Demo usage
    manager = TrainingDataManager()
    
    print("Training Data Statistics:")
    stats = manager.get_training_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nCleaning up old exports...")
    manager.cleanup_old_exports()