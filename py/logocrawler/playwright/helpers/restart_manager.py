"""Browser restart manager for memory management.

Handles browser context restarts based on:
- Domain count threshold (every N domains)
- Memory usage threshold (configurable percentage)
"""

import sys
from typing import Optional

from ...config import (
    MEMORY_RESTART_THRESHOLD,
    MEMORY_CHECK_INTERVAL,
    RESTART_EVERY_N_DOMAINS,
)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    sys.stderr.write("[WARN] psutil not installed - memory monitoring disabled\n")


def get_memory_percent() -> float:
    """
    Get current process memory usage as percentage of system memory.
    
    Returns:
        Memory percentage (0.0-1.0) or 0.0 if psutil unavailable.
    """
    if not PSUTIL_AVAILABLE:
        return 0.0
    
    try:
        process = psutil.Process()
        return process.memory_percent() / 100.0  # Convert to 0-1 range
    except Exception:
        return 0.0


class RestartManager:
    """
    Manages browser context restarts for memory efficiency.
    
    Usage:
        manager = RestartManager()
        
        for domain in domains:
            # ... process domain ...
            if manager.should_restart():
                # Restart browser context
                manager.record_restart()
    """
    
    def __init__(
        self,
        restart_every_n: int = RESTART_EVERY_N_DOMAINS,
        memory_threshold: float = MEMORY_RESTART_THRESHOLD,
        memory_check_interval: int = MEMORY_CHECK_INTERVAL,
    ):
        """
        Initialize restart manager.
        
        Args:
            restart_every_n: Restart after processing this many domains
            memory_threshold: Restart if memory usage exceeds this (0.0-1.0)
            memory_check_interval: Check memory every N domains
        """
        self.restart_every_n = restart_every_n
        self.memory_threshold = memory_threshold
        self.memory_check_interval = memory_check_interval
        
        self._domains_since_restart = 0
        self._total_restarts = 0
    
    def increment(self) -> None:
        """Record that a domain was processed."""
        self._domains_since_restart += 1
    
    def should_restart(self) -> bool:
        """
        Check if browser context should be restarted.
        
        Returns:
            True if restart is recommended.
        """
        # Check domain count threshold
        if self._domains_since_restart >= self.restart_every_n:
            sys.stderr.write(
                f"[RESTART] Domain count threshold reached "
                f"({self._domains_since_restart}/{self.restart_every_n})\n"
            )
            return True
        
        # Check memory periodically (not every domain for perf)
        if self._domains_since_restart % self.memory_check_interval == 0:
            mem_pct = get_memory_percent()
            if mem_pct > self.memory_threshold:
                sys.stderr.write(
                    f"[RESTART] Memory threshold exceeded "
                    f"({mem_pct:.1%} > {self.memory_threshold:.1%})\n"
                )
                return True
        
        return False
    
    def record_restart(self) -> None:
        """Record that a restart occurred."""
        self._domains_since_restart = 0
        self._total_restarts += 1
        sys.stderr.write(f"[RESTART] Context restarted (total restarts: {self._total_restarts})\n")
    
    @property
    def domains_processed(self) -> int:
        """Get domains processed since last restart."""
        return self._domains_since_restart
    
    @property
    def total_restarts(self) -> int:
        """Get total number of restarts."""
        return self._total_restarts
