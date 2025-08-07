"""
Metrics configuration for the training validation service.

This module sets up Prometheus metrics collection and provides utility functions
for recording custom metrics.
"""
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
import time

# Custom metrics
VALIDATION_REQUESTS = Counter(
    'training_validation_requests_total',
    'Total number of validation requests',
    ['endpoint', 'method', 'status']
)

VALIDATION_DURATION = Histogram(
    'training_validation_duration_seconds',
    'Duration of validation requests in seconds',
    ['endpoint']
)

VALIDATION_SESSIONS = Gauge(
    'training_validation_sessions_total',
    'Total number of validation sessions',
    ['status']
)

DOCUMENTS_PROCESSED = Counter(
    'training_validation_documents_processed_total',
    'Total number of documents processed',
    ['status']
)

def setup_metrics(app):
    """
    Configure Prometheus metrics collection for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Instrument the FastAPI app with default metrics
    Instrumentator().instrument(app).expose(app)
    
    # Add custom metrics collection
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Record request metrics
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        VALIDATION_REQUESTS.labels(
            endpoint=endpoint,
            method=method,
            status=status_code
        ).inc()
        
        VALIDATION_DURATION.labels(endpoint=endpoint).observe(process_time)
        
        return response
