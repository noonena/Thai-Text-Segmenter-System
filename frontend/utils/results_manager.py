#!/usr/bin/env python3
"""
Results manager utility for frontend downloads
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

class FrontendResultsManager:
    def __init__(self, results_dir: str = None):
        if results_dir is None:
            results_dir = Path(__file__).parent.parent / "results"
        
        self.results_dir = Path(results_dir)
        self.downloads_dir = self.results_dir / "downloads"
        
        # Ensure directory exists
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    def save_download(self, filename: str, content: str, file_type: str = "html") -> str:
        """Save processed content for user download"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = self.downloads_dir / safe_filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Log the download
        self._log_download(safe_filename, file_type, len(content))
        
        return str(file_path)
    
    def _log_download(self, filename: str, file_type: str, size: int):
        """Log download information"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "file_type": file_type,
            "size_bytes": size
        }
        
        log_file = self.downloads_dir / "download_log.json"
        logs = []
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get statistics about downloads"""
        log_file = self.downloads_dir / "download_log.json"
        
        if not log_file.exists():
            return {
                "total_downloads": 0,
                "file_types": {},
                "total_size_mb": 0,
                "recent_downloads": []
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {
                "total_downloads": 0,
                "file_types": {},
                "total_size_mb": 0,
                "recent_downloads": []
            }
        
        file_types = {}
        total_size = 0
        recent_downloads = []
        
        for log in logs:
            file_type = log.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_size += log.get("size_bytes", 0)
            
            # Get last 5 downloads
            if len(recent_downloads) < 5:
                recent_downloads.append({
                    "filename": log.get("filename"),
                    "timestamp": log.get("timestamp"),
                    "type": file_type
                })
        
        return {
            "total_downloads": len(logs),
            "file_types": file_types,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "recent_downloads": recent_downloads
        }
    
    def cleanup_old_downloads(self, days_to_keep: int = 30):
        """Clean up old download files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for file_path in self.downloads_dir.glob("*"):
            if file_path.is_file() and file_path.name != "download_log.json":
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    cleaned_count += 1
        
        return cleaned_count

if __name__ == "__main__":
    # Demo usage
    manager = FrontendResultsManager()
    
    print("Frontend Download Statistics:")
    stats = manager.get_download_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    cleaned = manager.cleanup_old_downloads()
    print(f"\nCleaned up {cleaned} old download files")