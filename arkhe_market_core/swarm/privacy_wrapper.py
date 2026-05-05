'''Privacy Wrapper inspired by HPE Swarm Learning'''

def privacy_safe_wrapper(func):
    """Decorator to ensure only aggregated, anonymous data is shared"""
    def wrapper(*args, **kwargs):
        # Filter out any sensitive data before sharing
        result = func(*args, **kwargs)
        # Ensure no API keys, positions, or raw data is included
        if isinstance(result, dict):
            safe_keys = ['local_strategy_score', 'sharpe', 'win_rate', 'total_pnl', 'report_id']
            safe_result = {k: v for k, v in result.items() if k in safe_keys}
            return safe_result
        return result
    return wrapper
