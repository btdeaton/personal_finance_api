from fastapi import Request, HTTPException, status
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.request_counts = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_rate_limited(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()
        minute_ago = current_time - 60
        
        with self.lock:
            # Clean up old requests
            self.request_counts[client_ip] = [t for t in self.request_counts[client_ip] if t > minute_ago]
            
            # Check rate limit
            if len(self.request_counts[client_ip]) >= self.requests_per_minute:
                return True
            
            # Add current request
            self.request_counts[client_ip].append(current_time)
            return False

# Create global rate limiter instance
rate_limiter = RateLimiter()