"""Browser-based logging system with rolling 60-day window."""

import json
from datetime import datetime, timedelta

try:
    from js import console, window
except ImportError:
    # Fallback for non-PyScript environments
    class FakeConsole:
        def error(self, msg): print(f"[ERROR] {msg}")
        def log(self, msg): print(f"[LOG] {msg}")
    console = FakeConsole()


class BrowserLogger:
    """Browser-based logger with automatic rolling 60-day window."""
    
    STORAGE_KEY = "pysheet.logs"
    MAX_LOG_ENTRIES = 10000
    ROLLING_WINDOW_DAYS = 60
    
    @staticmethod
    def _load_logs() -> dict:
        """Load logs from browser storage."""
        try:
            logs_json = window.localStorage.getItem(BrowserLogger.STORAGE_KEY)
            if logs_json:
                return json.loads(logs_json)
        except Exception:
            pass
        return {"logs": [], "errors": []}
    
    @staticmethod
    def _save_logs(logs_data: dict):
        """Save logs to browser storage with pruning."""
        # Remove logs older than rolling window
        now = datetime.now()
        cutoff_date = now - timedelta(days=BrowserLogger.ROLLING_WINDOW_DAYS)
        
        logs_data["logs"] = [
            log for log in logs_data.get("logs", [])
            if datetime.fromisoformat(log.get("timestamp", "")) > cutoff_date
        ]
        
        # Limit total entries
        if len(logs_data["logs"]) > BrowserLogger.MAX_LOG_ENTRIES:
            logs_data["logs"] = logs_data["logs"][-BrowserLogger.MAX_LOG_ENTRIES:]
        
        try:
            window.localStorage.setItem(BrowserLogger.STORAGE_KEY, json.dumps(logs_data))
        except Exception:
            pass
    
    @staticmethod
    def _parse_date(timestamp_str: str) -> str:
        """Extract date from ISO timestamp."""
        try:
            return datetime.fromisoformat(timestamp_str).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return ""
    
    @staticmethod
    def log(message: str, data: dict = None):
        """Log a message with optional data."""
        logs_data = BrowserLogger._load_logs()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data or {}
        }
        logs_data["logs"].append(entry)
        BrowserLogger._save_logs(logs_data)
        console.log(f"[LOG] {message}")
    
    @staticmethod
    def error(message: str, exc: Exception = None):
        """Log an error with optional exception."""
        logs_data = BrowserLogger._load_logs()
        exc_str = str(exc) if exc else ""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "exception": exc_str
        }
        logs_data["errors"].append(entry)
        BrowserLogger._save_logs(logs_data)
        console.error(f"[ERROR] {message}: {exc_str}")
    
    @staticmethod
    def get_stats():
        """Get statistics about stored logs."""
        logs_data = BrowserLogger._load_logs()
        now = datetime.now()
        
        # Calculate oldest log date
        oldest_log = None
        if logs_data.get("logs"):
            try:
                oldest_log = min(logs_data["logs"], key=lambda x: x.get("timestamp", "")).get("timestamp")
            except (ValueError, KeyError):
                pass
        
        # Count logs by date
        logs_by_date = {}
        for entry in logs_data.get("logs", []):
            date_str = BrowserLogger._parse_date(entry.get("timestamp", ""))
            if date_str:
                logs_by_date[date_str] = logs_by_date.get(date_str, 0) + 1
        
        return {
            "total_logs": len(logs_data.get("logs", [])),
            "total_errors": len(logs_data.get("errors", [])),
            "days_with_logs": len(logs_by_date),
            "oldest_log": oldest_log,
            "logs_by_date": logs_by_date,
            "storage_bytes": len(json.dumps(logs_data))
        }
