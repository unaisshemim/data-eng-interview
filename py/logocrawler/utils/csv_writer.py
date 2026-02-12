"""Incremental CSV writer for streaming results to stdout."""

import csv
import asyncio
from typing import TextIO, List, Tuple


class IncrementalCSVWriter:
    """Async-safe buffered CSV writer that streams results incrementally.
    
    Buffers results and flushes to the output stream periodically,
    ensuring partial results are available even if the process crashes.
    """
    
    def __init__(self, stream: TextIO, buffer_size: int = 10):
        """Initialize the writer.
        
        Args:
            stream: Output stream (e.g., sys.stdout)
            buffer_size: Number of results to buffer before flushing
        """
        self.stream = stream
        self.buffer_size = buffer_size
        self._buffer: List[Tuple[str, str]] = []
        self._lock = asyncio.Lock()
        self._total_written = 0
    
    def write_header(self):
        """Write the CSV header row. Call once before any writes."""
        writer = csv.writer(self.stream)
        writer.writerow(["domain", "logo_url"])
        self.stream.flush()
    
    async def write(self, domain: str, logo_url: str):
        """Add a result to the buffer, flush if buffer is full.
        
        Args:
            domain: The domain name
            logo_url: The discovered logo URL
        """
        async with self._lock:
            self._buffer.append((domain, logo_url))
            if len(self._buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Write buffered results to stream."""
        if not self._buffer:
            return
        
        writer = csv.writer(self.stream)
        for row in self._buffer:
            writer.writerow(row)
        
        self.stream.flush()
        self._total_written += len(self._buffer)
        self._buffer.clear()
    
    async def flush(self):
        """Force flush any buffered results."""
        async with self._lock:
            self._flush_buffer()
    
    async def close(self):
        """Flush remaining buffer. Call when done writing."""
        await self.flush()
    
    @property
    def count(self) -> int:
        """Total number of results written (including buffered)."""
        return self._total_written + len(self._buffer)
