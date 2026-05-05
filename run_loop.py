"""
run_loop.py – Headless loop for continuous signal execution.
"""

import time
from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent


def main() -> None:
    agent = MultiPortfolioAgent(
        total_balance=100.0,
        stable_allocation=0.7,
        stock_symbols=["NVDA", "AAPL", "MSFT", "AMZN", "META"],
        futures_symbols=["ES", "NQ", "GC", "CL"],
        stock_balance=1000.0,
        futures_balance=500.0,
        test_mode=True,
        cooldown_seconds=900,
    )

    print("Arkhe Market run loop started – all markets")
    try:
        while True:
            outputs = agent.run_once()
            for line in outputs:
                print(line)
            print("---")
            time.sleep(300)
    except KeyboardInterrupt:
        print("Loop stopped.")


if __name__ == "__main__":
    main()
