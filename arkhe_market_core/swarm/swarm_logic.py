'''Swarm Logic - Core decision rules for Arkhe Swarm Learning'''

def apply_local_override(local_score: float, global_score: float, threshold: float = 0.08) -> bool:
    """
    Critical Rule from Phase 1 Handoff:
    Local winning strategies override global consensus.
    """
    if local_score > global_score + threshold:
        return True  # Use local strategy
    return False  # Consider global strategy

def calculate_strategy_score(performance_metrics: dict) -> float:
    """Calculate local strategy score based on multiple factors"""
    sharpe = performance_metrics.get('sharpe', 0)
    win_rate = performance_metrics.get('win_rate', 0)
    profit_factor = performance_metrics.get('profit_factor', 1)
    drawdown = performance_metrics.get('max_drawdown', 0.1)
    
    score = (sharpe * 0.4) + (win_rate * 0.3) + (profit_factor * 0.2) - (drawdown * 0.1)
    return max(0.0, score)
