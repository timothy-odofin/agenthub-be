"""
Resilience monitoring endpoint.

Provides API endpoints to monitor circuit breaker states and statistics.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime

from app.core.resilience import get_circuit_breaker_stats, get_all_circuit_breaker_stats
from app.core.utils.logger import get_logger
from app.core.exceptions import NotFoundError, InternalError

# Import connection managers to ensure circuit breakers are initialized
try:
    from app.infrastructure.connections.external.jira_connection_manager import JiraConnectionManager
    from app.infrastructure.connections.external.confluence_connection_manager import ConfluenceConnectionManager
except ImportError:
    # Connection managers may not be available in all environments
    pass

logger = get_logger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])


@router.get("/circuit-breakers", response_model=Dict[str, Dict[str, Any]])
async def get_all_circuit_breakers():
    """
    Get statistics for all circuit breakers.
    
    Returns:
        Dictionary of circuit breaker names to their statistics
    """
    stats = get_all_circuit_breaker_stats()
    
    logger.info(
        f"Retrieved stats for {len(stats)} circuit breakers",
        extra={"circuit_count": len(stats)}
    )
    
    return stats


@router.get("/circuit-breakers/{circuit_name}", response_model=Dict[str, Any])
async def get_circuit_breaker(circuit_name: str):
    """
    Get statistics for a specific circuit breaker.
    
    Args:
        circuit_name: Name of the circuit breaker
        
    Returns:
        Circuit breaker statistics
    """
    stats = get_circuit_breaker_stats(circuit_name)
    
    if stats is None:
        raise NotFoundError(
            message=f"Circuit breaker '{circuit_name}' not found"
        )
    
    logger.info(
        f"Retrieved stats for circuit '{circuit_name}'",
        extra={"circuit_name": circuit_name, "state": stats.get("state")}
    )
    
    return stats


@router.get("/health", response_model=Dict[str, Any])
async def get_resilience_health():
    """
    Get overall resilience health status.
    
    Checks all circuit breakers and reports:
    - Total circuits
    - Circuits by state (closed, open, half_open)
    - Any circuits that are open (indicating problems)
    
    Returns:
        Health status summary
    """
    all_stats = get_all_circuit_breaker_stats()
    
    # Count circuits by state
    state_counts = {
        "closed": 0,
        "open": 0,
        "half_open": 0
    }
    
    open_circuits = []
    
    for name, stats in all_stats.items():
        state = stats.get("state", "unknown")
        if state in state_counts:
            state_counts[state] += 1
        
        if state == "open":
            open_circuits.append({
                "name": name,
                "failure_count": stats.get("failure_count"),
                "opened_at": stats.get("opened_at")
            })
    
    # Determine overall health
    is_healthy = state_counts["open"] == 0
    
    health_status = {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "total_circuits": len(all_stats),
        "circuits_by_state": state_counts,
        "open_circuits": open_circuits
    }
    
    if not is_healthy:
        logger.warning(
            f"Resilience health degraded: {state_counts['open']} circuits open",
            extra={
                "open_circuits": [c["name"] for c in open_circuits],
                "total_circuits": len(all_stats)
            }
        )
    
    return health_status


@router.get("/summary", response_model=List[Dict[str, Any]])
async def get_resilience_summary():
    """
    Get a summary of all circuit breakers with key metrics.
    
    Returns:
        List of circuit breaker summaries
    """
    all_stats = get_all_circuit_breaker_stats()
    
    summaries = []
    for name, stats in all_stats.items():
        summary = {
            "name": name,
            "state": stats.get("state"),
            "failure_count": stats.get("failure_count"),
            "failure_threshold": stats.get("failure_threshold"),
            "success_count": stats.get("success_count"),
            "success_threshold": stats.get("success_threshold"),
            "health_percentage": _calculate_health_percentage(stats)
        }
        summaries.append(summary)
    
    # Sort by state (open first, then half_open, then closed)
    state_priority = {"open": 0, "half_open": 1, "closed": 2}
    summaries.sort(key=lambda x: state_priority.get(x["state"], 3))
    
    return summaries


def _calculate_health_percentage(stats: Dict[str, Any]) -> float:
    """
    Calculate health percentage for a circuit breaker.
    
    - CLOSED: 100%
    - HALF_OPEN: 50%
    - OPEN: 0%
    """
    state = stats.get("state", "unknown")
    
    if state == "closed":
        return 100.0
    elif state == "half_open":
        return 50.0
    elif state == "open":
        return 0.0
    else:
        return 0.0
