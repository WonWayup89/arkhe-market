'''Arkhe Main - Swarm Coordinator (Central Intelligence Layer)'''

from .swarm_logic import apply_local_override, calculate_strategy_score
from typing import Dict, List, Optional

class SwarmCoordinator:
    def __init__(self):
        self.global_strategy_scores = {}  # symbol -> score from swarm
    
    def update_global_consensus(self, symbol: str, global_score: float):
        self.global_strategy_scores[symbol] = global_score
    
    def should_use_local_strategy(self, symbol: str, local_performance: Dict) -> bool:
        """Apply the critical rule: local winning strategies override global consensus"""
        local_score = calculate_strategy_score(local_performance)
        global_score = self.global_strategy_scores.get(symbol, 0.0)
        
        use_local = apply_local_override(local_score, global_score)
        print(f"[Swarm] {symbol}: Local={local_score:.3f} vs Global={global_score:.3f} → {'LOCAL OVERRIDE' if use_local else 'Consider Global'}")
        return use_local
