"""Utility subpackage for the Kyros Orchestrator service.

This package contains utility modules that provide common functionality used
throughout the Kyros Orchestrator service. These utilities include ETag generation
for HTTP caching and conditional requests, and input validation for task and job
creation to ensure data integrity.

Modules:
    etag: Provides ETag generation utilities for HTTP responses
    validation: Provides input validation utilities for task and job creation
"""

from .etag import generate_etag
