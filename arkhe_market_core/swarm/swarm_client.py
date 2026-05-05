'''Swarm Client - Sends anonymous reports to Arkhe Main'''

from .daily_report_generator import generate_anonymous_daily_report, save_report
from typing import Dict

def send_daily_swarm_report(portfolio_state: Dict, performance: Dict, decisions: list):
    """Send anonymous daily report (no sensitive data)"""
    report = generate_anonymous_daily_report(portfolio_state, performance, decisions)
    save_report(report)
    # In future: POST to Arkhe Main swarm endpoint (decentralized)
    print(f"[Swarm Client] Report {report['report_id']} sent to Arkhe Main (anonymous)")
    return report
