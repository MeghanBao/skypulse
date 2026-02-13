"""
SkyPulse Monitoring Module
Health checks, metrics, and alerting
"""

import psutil
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enum"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    service: str
    status: ServiceStatus
    message: str = ""
    latency_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthChecker:
    """Health check service for SkyPulse"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.email_checks = 0
        self.email_successes = 0
        self.deals_found = 0
        self.notifications_sent = 0
        self.errors = []
        self.last_error_time: Optional[datetime] = None
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks.
        
        Returns:
            Dictionary of health check results
        """
        checks = {
            "system": self.check_system(),
            "database": self.check_database(),
            "memory": self.check_memory(),
            "uptime": self.check_uptime(),
            "email": self.check_email_service(),
        }
        return checks
    
    def check_system(self) -> HealthCheckResult:
        """Check system health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check if system is healthy
            status = ServiceStatus.HEALTHY
            if cpu_percent > 90 or memory.percent > 90:
                status = ServiceStatus.DEGRADED
            
            return HealthCheckResult(
                service="system",
                status=status,
                message="System is running normally",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                }
            )
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return HealthCheckResult(
                service="system",
                status=ServiceStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    def check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        try:
            from models.database import get_db, engine
            
            start = datetime.utcnow()
            
            # Try to get database connection
            with get_db() as db:
                db.execute("SELECT 1")
            
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            
            return HealthCheckResult(
                service="database",
                status=ServiceStatus.HEALTHY,
                message="Database connection successful",
                latency_ms=latency,
                details={
                    "connected": True,
                    "engine": str(engine.url)
                }
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                service="database",
                status=ServiceStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )
    
    def check_memory(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            # Convert to MB
            memory_mb = mem_info.rss / (1024 * 1024)
            
            status = ServiceStatus.HEALTHY
            if memory_mb > 500:
                status = ServiceStatus.DEGRADED
            elif memory_mb > 1000:
                status = ServiceStatus.UNHEALTHY
            
            return HealthCheckResult(
                service="memory",
                status=status,
                message=f"Memory usage: {memory_mb:.1f} MB",
                details={
                    "memory_mb": round(memory_mb, 2),
                    "rss_bytes": mem_info.rss,
                    "vms_bytes": mem_info.vms,
                }
            )
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return HealthCheckResult(
                service="memory",
                status=ServiceStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}"
            )
    
    def check_uptime(self) -> HealthCheckResult:
        """Check service uptime"""
        try:
            uptime = datetime.utcnow() - self.start_time
            uptime_seconds = uptime.total_seconds()
            
            # Format uptime
            if uptime_seconds < 3600:
                uptime_str = f"{int(uptime_seconds / 60)} minutes"
            elif uptime_seconds < 86400:
                uptime_str = f"{int(uptime_seconds / 3600)} hours"
            else:
                uptime_str = f"{int(uptime_seconds / 86400)} days"
            
            return HealthCheckResult(
                service="uptime",
                status=ServiceStatus.HEALTHY,
                message=f"Service uptime: {uptime_str}",
                details={
                    "uptime_seconds": uptime_seconds,
                    "start_time": self.start_time.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Uptime check failed: {e}")
            return HealthCheckResult(
                service="uptime",
                status=ServiceStatus.UNHEALTHY,
                message=f"Uptime check failed: {str(e)}"
            )
    
    def check_email_service(self) -> HealthCheckResult:
        """Check email service connectivity"""
        try:
            from email_service.imap_reader import EmailReader
            
            reader = EmailReader()
            start = datetime.utcnow()
            
            connected = reader.connect()
            reader.disconnect()
            
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            
            if connected:
                return HealthCheckResult(
                    service="email",
                    status=ServiceStatus.HEALTHY,
                    message="Email service connected successfully",
                    latency_ms=latency,
                    details={
                        "connected": True,
                        "checks": self.email_checks,
                        "successes": self.email_successes,
                    }
                )
            else:
                return HealthCheckResult(
                    service="email",
                    status=ServiceStatus.DEGRADED,
                    message="Email service connection failed",
                    details={
                        "connected": False,
                        "checks": self.email_checks,
                        "successes": self.email_successes,
                    }
                )
        except Exception as e:
            logger.error(f"Email service check failed: {e}")
            return HealthCheckResult(
                service="email",
                status=ServiceStatus.UNHEALTHY,
                message=f"Email service check failed: {str(e)}"
            )
    
    def record_email_check(self, success: bool):
        """Record email check result"""
        self.email_checks += 1
        if success:
            self.email_successes += 1
    
    def record_deal_found(self):
        """Record deal found"""
        self.deals_found += 1
    
    def record_notification_sent(self):
        """Record notification sent"""
        self.notifications_sent += 1
    
    def record_error(self, error: str):
        """Record error"""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
        })
        self.last_error_time = datetime.utcnow()
        
        # Keep only last 100 errors
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "email": {
                "checks": self.email_checks,
                "successes": self.email_successes,
                "success_rate": round(
                    (self.email_successes / self.email_checks * 100) 
                    if self.email_checks > 0 else 0, 2
                ),
            },
            "deals": {
                "found": self.deals_found,
                "notifications_sent": self.notifications_sent,
            },
            "errors": {
                "count": len(self.errors),
                "last_error": self.errors[-1] if self.errors else None,
            },
            "uptime": {
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            },
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all health data to dictionary"""
        checks = self.check_all()
        
        # Determine overall status
        statuses = [c.status for c in checks.values()]
        if ServiceStatus.UNHEALTHY in statuses:
            overall = ServiceStatus.UNHEALTHY
        elif ServiceStatus.DEGRADED in statuses:
            overall = ServiceStatus.DEGRADED
        else:
            overall = ServiceStatus.HEALTHY
        
        return {
            "status": overall.value,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {name: {
                "status": result.status.value,
                "message": result.message,
                "latency_ms": round(result.latency_ms, 2),
                "details": result.details,
            } for name, result in checks.items()},
            "statistics": self.get_stats(),
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create global health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def health_check() -> Dict[str, Any]:
    """Run all health checks and return results"""
    checker = get_health_checker()
    return checker.to_dict()


if __name__ == "__main__":
    # Test health checker
    print("🧪 Testing Health Checker")
    print("=" * 50)
    
    checker = HealthChecker()
    
    # Run all checks
    print("\n📊 Running health checks...")
    results = checker.check_all()
    
    for name, result in results.items():
        status_emoji = {
            ServiceStatus.HEALTHY: "✅",
            ServiceStatus.DEGRADED: "⚠️",
            ServiceStatus.UNHEALTHY: "❌",
            ServiceStatus.UNKNOWN: "❓",
        }[result.status]
        
        print(f"{status_emoji} {name}: {result.status.value}")
        print(f"   {result.message}")
        if result.latency_ms > 0:
            print(f"   Latency: {result.latency_ms:.2f}ms")
    
    print("\n📈 Statistics:")
    print(f"   {checker.get_stats()}")
