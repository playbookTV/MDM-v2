"""
Test endpoints for Sentry error tracking
"""

import logging
import sentry_sdk
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class TestResponse(BaseModel):
    message: str
    transaction_id: str

@router.get("/sentry/test-error")
async def test_sentry_error():
    """Test endpoint to trigger a Sentry error"""
    try:
        # Add custom context
        sentry_sdk.set_context("test_context", {
            "test_type": "manual_error",
            "endpoint": "/sentry/test-error"
        })
        
        # Add breadcrumb
        sentry_sdk.add_breadcrumb(
            message="About to trigger test error",
            level="info",
            category="test"
        )
        
        # Trigger an error
        raise ValueError("This is a test error for Sentry integration")
        
    except ValueError as e:
        # Capture the exception with extra context
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Test error triggered for Sentry")

@router.get("/sentry/test-performance")
async def test_sentry_performance():
    """Test endpoint to generate performance data"""
    import time
    import random
    
    # Start a custom transaction
    with sentry_sdk.start_transaction(name="test_performance_endpoint", op="test"):
        # Add some spans
        with sentry_sdk.start_span(op="database", description="Simulated DB query"):
            time.sleep(random.uniform(0.1, 0.3))
        
        with sentry_sdk.start_span(op="external", description="Simulated API call"):
            time.sleep(random.uniform(0.05, 0.15))
        
        # Add custom context
        sentry_sdk.set_context("performance_test", {
            "simulated_operations": ["database", "external_api"],
            "test_duration": "0.2-0.5s"
        })
        
        transaction_id = sentry_sdk.get_current_span().get_trace_id() if sentry_sdk.get_current_span() else "unknown"
        
        return TestResponse(
            message="Performance test completed",
            transaction_id=transaction_id
        )

@router.post("/sentry/test-log")
async def test_sentry_logging():
    """Test endpoint to send logs to Sentry"""
    # Test different log levels
    logger.info("This is an info log for Sentry testing")
    logger.warning("This is a warning log for Sentry testing")
    
    # Add context
    sentry_sdk.set_context("logging_test", {
        "log_levels": ["info", "warning"],
        "test_endpoint": "/sentry/test-log"
    })
    
    # This will be sent to Sentry as it's ERROR level
    logger.error("This is an error log that should appear in Sentry")
    
    return {"message": "Log test completed - check Sentry for error log"}

@router.get("/sentry/test-breadcrumbs")
async def test_sentry_breadcrumbs():
    """Test endpoint to create breadcrumb trail"""
    # Add multiple breadcrumbs
    sentry_sdk.add_breadcrumb(
        message="Starting breadcrumb test",
        level="info",
        category="test"
    )
    
    sentry_sdk.add_breadcrumb(
        message="Processing step 1",
        level="info",
        data={"step": 1, "action": "validate_input"}
    )
    
    sentry_sdk.add_breadcrumb(
        message="Processing step 2", 
        level="info",
        data={"step": 2, "action": "business_logic"}
    )
    
    # Simulate an issue
    sentry_sdk.add_breadcrumb(
        message="Issue detected in step 3",
        level="warning",
        data={"step": 3, "action": "error_handling", "issue": "simulated_problem"}
    )
    
    # Capture a message with the breadcrumb trail
    sentry_sdk.capture_message("Breadcrumb test completed with simulated issue", level="warning")
    
    return {"message": "Breadcrumb test completed - check Sentry for message with trail"}