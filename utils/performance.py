"""
Performance monitoring utilities for the AI Language Tutor application.
"""

import time
import psutil
from typing import Dict, Any
from utils.logger import get_logger, LoggerMixin


class PerformanceMonitor(LoggerMixin):
    """Performance monitoring for the application."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {}
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer."""
        self.metrics[name] = {'start': time.time()}
    
    def end_timer(self, name: str) -> float:
        """End a performance timer and return duration."""
        if name not in self.metrics:
            return 0.0
        
        duration = time.time() - self.metrics[name]['start']
        self.metrics[name]['duration'] = duration
        self.metrics[name]['end'] = time.time()
        
        return duration
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics."""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent
        }
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


