"""
cryptobot — a strategy factory that breeds trading bots and then tries very hard to
kill them.

    python3 -m cryptobot.run evolve --markets synthetic
    python3 -m cryptobot.run null-test
    python3 -m cryptobot.run report

Read cryptobot/README.md before trusting any number this produces, and validate.py
before believing the phrase "proven profit".
"""

__all__ = ["data", "indicators", "strategies", "backtest", "stats", "universe",
           "bot", "validate", "evolve"]
