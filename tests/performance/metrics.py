"""
Performance metrics collection and analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    # Timing metrics
    total_time: float = 0.0
    scan_time: float = 0.0
    process_time: float = 0.0
    
    # Count metrics
    folders_scanned: int = 0
    files_examined: int = 0
    folders_changed: int = 0
    folders_skipped: int = 0
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_entries: int = 0
    cache_memory_bytes: int = 0
    
    # Resource metrics
    peak_memory_mb: float = 0.0
    cpu_percent: float = 0.0
    
    # Metadata
    strategy_name: str = ""
    tree_depth: int = 0
    tree_width: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            return self.cache_hits / total
        return 0.0
    
    @property
    def folders_per_second(self) -> float:
        """Calculate folder processing rate."""
        if self.total_time > 0:
            return self.folders_scanned / self.total_time
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'total_time': self.total_time,
            'scan_time': self.scan_time,
            'process_time': self.process_time,
            'folders_scanned': self.folders_scanned,
            'files_examined': self.files_examined,
            'folders_changed': self.folders_changed,
            'folders_skipped': self.folders_skipped,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_entries': self.cache_entries,
            'cache_memory_bytes': self.cache_memory_bytes,
            'cache_hit_rate': self.cache_hit_rate,
            'peak_memory_mb': self.peak_memory_mb,
            'cpu_percent': self.cpu_percent,
            'folders_per_second': self.folders_per_second,
            'strategy_name': self.strategy_name,
            'tree_depth': self.tree_depth,
            'tree_width': self.tree_width,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PerformanceMetrics':
        """Create from dictionary."""
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Remove calculated properties if present
        data.pop('cache_hit_rate', None)
        data.pop('folders_per_second', None)
        return cls(**data)


class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics_history: List[PerformanceMetrics] = []
        self.current_metrics: Optional[PerformanceMetrics] = None
    
    def start_collection(self) -> PerformanceMetrics:
        """Start collecting metrics for a new run."""
        self.current_metrics = PerformanceMetrics()
        return self.current_metrics
    
    def finish_collection(self) -> PerformanceMetrics:
        """Finish collecting and store metrics."""
        if self.current_metrics:
            self.metrics_history.append(self.current_metrics)
            metrics = self.current_metrics
            self.current_metrics = None
            return metrics
        return PerformanceMetrics()
    
    def extract_from_scanner(self, scanner: Any) -> PerformanceMetrics:
        """
        Extract metrics from a scanner instance.
        
        Args:
            scanner: FolderScanner or DazzleTreeScanner instance
            
        Returns:
            Populated PerformanceMetrics
        """
        metrics = self.current_metrics or PerformanceMetrics()
        
        # Try to extract cache statistics
        if hasattr(scanner, 'cache') and scanner.cache:
            if hasattr(scanner.cache, 'get_statistics'):
                stats = scanner.cache.get_statistics()
                metrics.cache_hits = stats.get('hits', 0)
                metrics.cache_misses = stats.get('misses', 0)
                metrics.cache_entries = stats.get('entries', 0)
                metrics.cache_memory_bytes = stats.get('memory_bytes', 0)
        
        # Try to extract adapter statistics (DazzleTreeLib)
        if hasattr(scanner, 'adapter_stack'):
            adapter = scanner.adapter_stack
            while adapter:
                # Look for cache adapter
                if hasattr(adapter, 'get_cache_stats'):
                    stats = adapter.get_cache_stats()
                    metrics.cache_hits = stats.get('hits', 0)
                    metrics.cache_misses = stats.get('misses', 0)
                    metrics.cache_entries = stats.get('size', 0)
                
                # Next adapter in stack
                if hasattr(adapter, 'base_adapter'):
                    adapter = adapter.base_adapter
                else:
                    break
        
        return metrics
    
    def compare(
        self, 
        metrics1: PerformanceMetrics, 
        metrics2: PerformanceMetrics
    ) -> Dict[str, Any]:
        """
        Compare two sets of metrics.
        
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'time_diff': metrics2.total_time - metrics1.total_time,
            'time_ratio': metrics2.total_time / metrics1.total_time if metrics1.total_time > 0 else 0,
            'throughput_diff': metrics2.folders_per_second - metrics1.folders_per_second,
            'cache_hit_rate_diff': metrics2.cache_hit_rate - metrics1.cache_hit_rate,
            'memory_diff_mb': metrics2.peak_memory_mb - metrics1.peak_memory_mb,
        }
        
        # Calculate percentage improvements
        if metrics1.total_time > 0:
            comparison['time_improvement_pct'] = (
                (metrics1.total_time - metrics2.total_time) / metrics1.total_time * 100
            )
        
        if metrics1.peak_memory_mb > 0:
            comparison['memory_improvement_pct'] = (
                (metrics1.peak_memory_mb - metrics2.peak_memory_mb) / metrics1.peak_memory_mb * 100
            )
        
        return comparison
    
    def save_to_file(self, filepath: Path):
        """Save metrics history to JSON file."""
        data = [m.to_dict() for m in self.metrics_history]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: Path):
        """Load metrics history from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.metrics_history = [PerformanceMetrics.from_dict(d) for d in data]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all collected metrics."""
        if not self.metrics_history:
            return {}
        
        times = [m.total_time for m in self.metrics_history]
        throughputs = [m.folders_per_second for m in self.metrics_history]
        hit_rates = [m.cache_hit_rate for m in self.metrics_history]
        
        return {
            'runs': len(self.metrics_history),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_throughput': sum(throughputs) / len(throughputs),
            'avg_cache_hit_rate': sum(hit_rates) / len(hit_rates) if hit_rates else 0,
        }