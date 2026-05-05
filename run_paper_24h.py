"""
run_paper_24h.py - Robust 24-hour headless paper trading test mode for Arkhe Market
Phase 1 of Swarm Intelligence System
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent
from arkhe_market_core.swarm import calculate_strategy_score


# ===================== CONFIG =====================
TEST_DURATION_HOURS = 24
LOOP_INTERVAL_SECONDS = 300  # 5 minutes
LOG_LEVEL = logging.INFO

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "paper_24h_test.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_final_report(agent: MultiPortfolioAgent, start_time: datetime, end_time: datetime):
    """Generate comprehensive JSON and Markdown reports + anonymous swarm report."""
    try:
        snapshot = agent.snapshot()
        metrics = agent.compute_local_metrics()

        report = {
            "test_metadata": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_hours": TEST_DURATION_HOURS,
                "total_loops": getattr(agent, "_loop_count", 0),
            },
            "portfolio_summary": {
                "total_equity": snapshot.get("total_equity", 0),
                "total_cash": snapshot.get("total_cash", 0),
                "stable_equity": snapshot.get("stable", {}).get("equity", 0),
                "alt_equity": snapshot.get("alt", {}).get("equity", 0),
                "stocks_equity": snapshot.get("stocks", {}).get("equity", 0),
                "futures_equity": snapshot.get("futures", {}).get("equity", 0),
            },
            "performance_metrics": metrics,
            "swarm": {
                "opt_in": agent.swarm_client.opt_in,
                "local_strategy_score": metrics["local_strategy_score"],
            },
        }

        with open(LOGS_DIR / "paper_test_report.json", "w") as f:
            json.dump(report, f, indent=2, sort_keys=True)

        md_content = f"""# Arkhe Market 24-Hour Paper Trading Test Report

**Test Period:** {start_time.strftime('%Y-%m-%d %H:%M')} → {end_time.strftime('%Y-%m-%d %H:%M')}
**Duration:** {TEST_DURATION_HOURS} hours
**Loops Completed:** {report['test_metadata']['total_loops']}

## Portfolio Summary
- **Total Equity**: ${report['portfolio_summary']['total_equity']:.2f}
- **Total Cash**: ${report['portfolio_summary']['total_cash']:.2f}
- **Stable Sleeve Equity**: ${report['portfolio_summary']['stable_equity']:.2f}
- **Alt Sleeve Equity**: ${report['portfolio_summary']['alt_equity']:.2f}
- **Stocks Sleeve Equity**: ${report['portfolio_summary']['stocks_equity']:.2f}
- **Futures Sleeve Equity**: ${report['portfolio_summary']['futures_equity']:.2f}

## Performance Metrics (approximate, derived from trade ledger)
- **Total PnL**: ${metrics['total_pnl']:.2f}
- **Trade Count**: {metrics['trade_count']}
- **Win Rate**: {metrics['win_rate']:.2%}
- **Profit Factor**: {metrics['profit_factor']:.2f}
- **Sharpe (per-trade, not annualized)**: {metrics['sharpe']:.2f}
- **Max Drawdown (vs. starting balance)**: {metrics['max_drawdown']:.2%}
- **Local Strategy Score**: {metrics['local_strategy_score']:.3f}

## Swarm
- **Opt-in**: {report['swarm']['opt_in']} (set ARKHE_SWARM_OPT_IN=1 to share)
- Anonymous report: `logs/daily_swarm_report.json`

## Risk Controls
- All trades executed in PAPER mode (test_mode=True forced)
- Daily drawdown limit: 3%
- Per-symbol cooldown: 5 minutes
- No real capital at risk.
"""
        with open(LOGS_DIR / "paper_test_report.md", "w") as f:
            f.write(md_content)

        logger.info("✅ Final reports generated: logs/paper_test_report.json + .md")

        # Anonymous swarm report — saved locally always; dispatched only if opted in.
        try:
            agent.generate_swarm_report()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Swarm report generation failed (non-fatal): {e}")

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)


def main():
    logger.info("🚀 Starting Arkhe Market 24-Hour Paper Trading Test")
    logger.info(f"Test duration: {TEST_DURATION_HOURS} hours | Loop every {LOOP_INTERVAL_SECONDS}s")

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=TEST_DURATION_HOURS)

    # Initialize MultiPortfolioAgent in strict paper mode
    agent = MultiPortfolioAgent(
        total_balance=100000.0,      # Large starting balance for realistic testing
        stable_allocation=0.6,
        stock_balance=40000.0,
        futures_balance=20000.0,
        test_mode=True,              # FORCE PAPER MODE
        cooldown_seconds=300,
        daily_drawdown_limit=0.03,
    )

    logger.info("✅ MultiPortfolioAgent initialized in PAPER MODE")
    logger.info("Risk controls, cooldowns, and paper execution are ACTIVE")

    loop_count = 0

    try:
        while datetime.now() < end_time:
            loop_count += 1
            agent._loop_count = loop_count  # Track loops

            loop_start = time.time()
            
            logger.info(f"=== Loop {loop_count} / ~{TEST_DURATION_HOURS*12} ===")
            
            outputs = agent.run_once()
            
            for output in outputs:
                if isinstance(output, (dict, str)):
                    logger.info(str(output)[:500])  # Truncate long outputs

            # Snapshot every 12 loops (~1 hour)
            if loop_count % 12 == 0:
                snap = agent.snapshot()
                logger.info(f"Hourly snapshot - Total Equity: ${snap.get('total_equity', 0):.2f}")

            elapsed = time.time() - loop_start
            sleep_time = max(0, LOOP_INTERVAL_SECONDS - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.warning("⏹️  Test interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}", exc_info=True)
    finally:
        end_time_actual = datetime.now()
        logger.info("🏁 Generating final 24h test report...")
        generate_final_report(agent, start_time, end_time_actual)
        logger.info("🎉 24-Hour Paper Test completed!")


if __name__ == "__main__":
    main()
