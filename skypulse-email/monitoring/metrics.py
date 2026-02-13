"""
SkyPulse Metrics Module
Prometheus-compatible metrics collection
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class Counter:
    """Simple counter metric"""
    name: str
    description: str = ""
    value: int = 0
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Gauge:
    """Simple gauge metric"""
    name: str
    description: str = ""
    value: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Histogram:
    """Simple histogram metric"""
    name: str
    description: str = ""
    buckets: list = field(default_factory=lambda: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0])
    values: list = field(default_factory=list)
    count: int = 0
    sum_: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collect and export metrics for SkyPulse"""
    
    def __init__(self, service_name: str = "skypulse"):
        self.service_name = service_name
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.start_time = datetime.utcnow()
        self._lock = threading.Lock()
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default metrics"""
        # Counters
        self.counter("emails_processed", "Total emails processed")
        self.counter("deals_found", "Total deals found")
        self.counter("notifications_sent", "Total notifications sent")
        self.counter("errors_total", "Total errors")
        self.counter("api_requests", "Total API requests")
        
        # Gauges
        self.gauge("uptime_seconds", "Service uptime in seconds")
        self.gauge("active_subscriptions", "Number of active subscriptions")
        self.gauge("memory_usage_bytes", "Memory usage in bytes")
        
        # Histograms
        self.histogram("email_processing_seconds", "Email processing time", 
                      buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0])
        self.histogram("api_latency_seconds", "API request latency",
                      buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5])
    
    def counter(self, name: str, description: str = "", tags: Dict[str, str] = None) -> Counter:
        """Get or create a counter"""
        key = self._make_key(name, tags)
        if key not in self.counters:
            self.counters[key] = Counter(
                name=name,
                description=description,
                tags=tags or {}
            )
        return self.counters[key]
    
    def gauge(self, name: str, description: str = "", tags: Dict[str, str] = None) -> Gauge:
        """Get or create a gauge"""
        key = self._make_key(name, tags)
        if key not in self.gauges:
            self.gauges[key] = Gauge(
                name=name,
                description=description,
                tags=tags or {}
            )
        return self.gauges[key]
    
    def histogram(self, name: str, description: str = "", 
                 buckets: list = None, tags: Dict[str, str] = None) -> Histogram:
        """Get or create a histogram"""
        key = self._make_key(name, tags)
        if key not in self.histograms:
            self.histograms[key] = Histogram(
                name=name,
                description=description,
                buckets=buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
                tags=tags or {}
            )
        return self.histograms[key]
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Make unique key for metric"""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}{{}}".format(tag_str)
        return name
    
    # Convenience methods
    def inc_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter"""
        counter = self.counter(name, tags=tags)
        with self._lock:
            counter.value += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set gauge value"""
        gauge = self.gauge(name, tags=tags)
        with self._lock:
            gauge.value = value
    
    def observe_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Observe a value in histogram"""
        hist = self.histogram(name, tags=tags)
        with self._lock:
            hist.values.append(value)
            hist.count += 1
            hist.sum_ += value
    
    # Specific metric methods
    def email_processed(self, success: bool, duration_seconds: float):
        """Record email processing"""
        self.inc_counter("emails_processed")
        self.observe_histogram("email_processing_seconds", duration_seconds)
        if not success:
            self.inc_counter("errors_total", tags={"type": "email"})
    
    def deal_found(self):
        """Record deal found"""
        self.inc_counter("deals_found")
    
    def notification_sent(self):
        """Record notification sent"""
        self.inc_counter("notifications_sent")
    
    def api_request(self, path: str, duration_seconds: float, status_code: int):
        """Record API request"""
        self.inc_counter("api_requests", tags={"path": path, "status": str(status_code)})
        self.observe_histogram("api_latency_seconds", duration_seconds, tags={"path": path})
    
    def error(self, error_type: str):
        """Record error"""
        self.inc_counter("errors_total", tags={"type": error_type})
    
    def update_uptime(self):
        """Update uptime gauge"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        self.set_gauge("uptime_seconds", uptime)
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Comments
        lines.append(f"# SkyPulse Metrics - {datetime.utcnow().isoformat()}")
        lines.append(f"# Service: {self.service_name}")
        lines.append("")
        
        # Counters
        lines.append("# Counters")
        for key, counter in self.counters.items():
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            tags = ""
            if counter.tags:
                tag_str = ",".join(f'{k}="{v}"' for k, v in sorted(counter.tags.items()))
                tags = f"{{{tag_str}}}"
            lines.append(f"{counter.name}{tags} {counter.value}")
            lines.append("")
        
        # Gauges
        lines.append("# Gauges")
        for key, gauge in self.gauges.items():
            if gauge.name == "uptime_seconds":
                self.update_uptime()  # Update before export
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            tags = ""
            if gauge.tags:
                tag_str = ",".join(f'{k}="{v}"' for k, v in sorted(gauge.tags.items()))
                tags = f"{{{tag_str}}}"
            lines.append(f"{gauge.name}{tags} {gauge.value}")
            lines.append("")
        
        # Histograms
        lines.append("# Histograms")
        for key, hist in self.histograms.items():
            lines.append(f"# HELP {hist.name} {hist.description}")
            lines.append(f"# TYPE {hist.name} histogram")
            tags = ""
            if hist.tags:
                tag_str = ",".join(f'{k}="{v}"' for k, v in sorted(hist.tags.items()))
                tags = f"{{{tag_str}}}"
            
            # Calculate bucket counts
            cumulative = 0
            for bucket in hist.buckets:
                bucket_count = sum(1 for v in hist.values if v <= bucket)
                cumulative = bucket_count
                lines.append(f"{hist.name}_bucket{tags},le=\"{bucket}\" {cumulative}")
            
            # +Inf bucket (all values)
            lines.append(f"{hist.name}_bucket{tags},le=\"+Inf\" {hist.count}")
            
            # _sum and _count
            lines.append(f"{hist.name}_sum{tags} {hist.sum_}")
            lines.append(f"{hist.name}_count{tags} {hist.count}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary as dictionary"""
        self.update_uptime()
        
        return {
            "service": self.service_name,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "counters": {
                name: counter.value 
                for name, counter in self.counters.items()
            },
            "gauges": {
                name: gauge.value 
                for name, gauge in self.gauges.items()
            },
            "histograms": {
                name: {
                    "count": hist.count,
                    "sum": round(hist.sum_, 2),
                    "avg": round(hist.sum_ / hist.count, 2) if hist.count > 0 else 0,
                }
                for name, hist in self.histograms.items()
            },
        }


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_email_processed(success: bool, duration_seconds: float):
    """Convenience function to record email processing"""
    metrics = get_metrics()
    metrics.email_processed(success, duration_seconds)


def record_deal_found():
    """Convenience function to record deal found"""
    metrics = get_metrics()
    metrics.deal_found()


def record_notification_sent():
    """Convenience function to record notification sent"""
    metrics = get_metrics()
    metrics.notification_sent()


if __name__ == "__main__":
    # Test metrics
    print("🧪 Testing Metrics Collector")
    print("=" * 50)
    
    metrics = MetricsCollector()
    
    # Record some data
    print("\n📊 Recording sample metrics...")
    
    metrics.email_processed(success=True, duration_seconds=1.5)
    metrics.email_processed(success=True, duration_seconds=0.8)
    metrics.email_processed(success=False, duration_seconds=2.3)
    metrics.deal_found()
    metrics.deal_found()
    metrics.notification_sent()
    
    print("✅ Recorded sample data")
    
    # Print summary
    print("\n📈 Summary:")
    summary = metrics.get_summary()
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    print("\n📄 Prometheus Format (first 50 lines):")
    prom_output = metrics.get_prometheus_format()
    print("\n".join(prom_output.split("\n")[:50]))
