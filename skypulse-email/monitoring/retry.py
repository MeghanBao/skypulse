"""
SkyPulse Retry Mechanism
Automatic retry with exponential backoff
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Exception that should trigger a retry"""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger a retry"""
    pass


class BackoffStrategy(Enum):
    """Backoff strategy options"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[type] = (Exception,)


def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate delay for a given attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    if config.backoff == BackoffStrategy.EXPONENTIAL:
        delay = config.initial_delay * (config.exponential_base ** attempt)
    elif config.backoff == BackoffStrategy.LINEAR:
        delay = config.initial_delay * (attempt + 1)
    else:  # FIXED
        delay = config.initial_delay
    
    # Cap at max delay
    delay = min(delay, config.max_delay)
    
    # Add jitter
    if config.jitter and delay > 0:
        import random
        jitter_range = delay * 0.1  # 10% jitter
        delay = delay + random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay


def with_retry(config: RetryConfig = None):
    """
    Decorator to add retry logic to a function.
    
    Usage:
        @with_retry(RetryConfig(max_retries=3, initial_delay=1.0))
        def my_function():
            ...
            
        @with_retry()
        def my_function():  # Uses defaults
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if should retry
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after "
                            f"{config.max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate and apply delay
                    delay = calculate_delay(attempt, config)
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/"
                        f"{config.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
                
                except NonRetryableError as e:
                    # Don't retry non-retryable errors
                    logger.error(f"Non-retryable error: {e}")
                    raise
            
            # Should not reach here
            if last_exception:
                raise last_exception
            raise Exception("Unexpected retry loop exit")
        
        return wrapper
    return decorator


class RetryableOperation:
    """
    Class to manage retryable operations.
    More flexible than the decorator for complex cases.
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.attempt_count = 0
        self.last_exception = None
        self.success = False
    
    def run(self, func: Callable, *args, **kwargs) -> Any:
        """
        Run a function with retry logic.
        
        Args:
            func: Function to run
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of the function
            
        Raises:
            The final exception if all retries fail
        """
        self.attempt_count = 0
        self.success = False
        
        for attempt in range(self.config.max_retries + 1):
            self.attempt_count = attempt
            
            try:
                result = func(*args, **kwargs)
                self.success = True
                
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1} "
                        f"(after {attempt} retries)"
                    )
                
                return result
                
            except self.config.retryable_exceptions as e:
                self.last_exception = e
                
                if attempt >= self.config.max_retries:
                    logger.error(
                        f"Operation failed after {attempt} retries: {e}"
                    )
                    raise
                
                delay = calculate_delay(attempt, self.config)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                time.sleep(delay)
            
            except NonRetryableError as e:
                logger.error(f"Non-retryable error: {e}")
                raise
        
        # Should not reach here
        if self.last_exception:
            raise self.last_exception
        raise Exception("Unexpected retry loop exit")
    
    def get_stats(self) -> dict:
        """Get operation statistics"""
        return {
            "attempts": self.attempt_count,
            "success": self.success,
            "retries": max(0, self.attempt_count - 1) if self.success else self.attempt_count,
            "last_exception": str(self.last_exception) if self.last_exception else None,
        }


class EmailRetryManager:
    """
    Retry manager specifically for email operations.
    Handles IMAP and SMTP failures with appropriate strategies.
    """
    
    def __init__(self):
        self.config = RetryConfig(
            max_retries=3,
            initial_delay=2.0,
            max_delay=60.0,
            backoff=BackoffStrategy.EXPONENTIAL,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                IOError,
                OSError,
            )
        )
        self.stats = {
            "imap_retries": 0,
            "smtp_retries": 0,
            "imap_success": 0,
            "smtp_success": 0,
            "imap_failures": 0,
            "smtp_failures": 0,
        }
    
    @with_retry
    def connect_imap(self, imap_reader) -> bool:
        """Connect to IMAP with retry"""
        return imap_reader.connect()
    
    @with_retry
    def fetch_emails(self, imap_reader, *args, **kwargs) -> list:
        """Fetch emails with retry"""
        return imap_reader.fetch_recent_emails(*args, **kwargs)
    
    @with_retry
    def send_email(self, smtp_sender, *args, **kwargs) -> bool:
        """Send email with retry"""
        return smtp_sender.send_email(*args, **kwargs)
    
    def record_imap_success(self):
        """Record IMAP success"""
        self.stats["imap_success"] += 1
    
    def record_imap_failure(self):
        """Record IMAP failure"""
        self.stats["imap_failures"] += 1
    
    def record_smtp_success(self):
        """Record SMTP success"""
        self.stats["smtp_success"] += 1
    
    def record_smtp_failure(self):
        """Record SMTP failure"""
        self.stats["smtp_failures"] += 1
    
    def get_stats(self) -> dict:
        """Get retry manager statistics"""
        imap_total = self.stats["imap_success"] + self.stats["imap_failures"]
        smtp_total = self.stats["smtp_success"] + self.stats["smtp_failures"]
        
        return {
            "imap": {
                "success": self.stats["imap_success"],
                "failures": self.stats["imap_failures"],
                "success_rate": round(
                    self.stats["imap_success"] / imap_total * 100 
                    if imap_total > 0 else 100, 2
                ),
            },
            "smtp": {
                "success": self.stats["smtp_success"],
                "failures": self.stats["smtp_failures"],
                "success_rate": round(
                    self.stats["smtp_success"] / smtp_total * 100 
                    if smtp_total > 0 else 100, 2
                ),
            },
        }


# Global retry manager
_retry_manager: Optional[EmailRetryManager] = None


def get_retry_manager() -> EmailRetryManager:
    """Get or create global retry manager"""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = EmailRetryManager()
    return _retry_manager


if __name__ == "__main__":
    # Test retry mechanism
    print("🧪 Testing Retry Mechanism")
    print("=" * 50)
    
    # Test retry decorator
    print("\n📌 Testing @with_retry decorator")
    
    call_count = 0
    
    @with_retry(RetryConfig(max_retries=3, initial_delay=0.1))
    def unreliable_function(fail_times: int = 2):
        global call_count
        call_count += 1
        
        if call_count <= fail_times:
            raise RetryableError(f"Failed attempt {call_count}")
        
        return "Success!"
    
    try:
        result = unreliable_function(fail_times=2)
        print(f"✅ Result: {result}")
        print(f"   Total calls: {call_count}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test retry manager
    print("\n📌 Testing EmailRetryManager")
    
    manager = EmailRetryManager()
    stats = manager.get_stats()
    print(f"   Stats: {stats}")
    
    print("\n✅ Retry mechanism test completed!")
