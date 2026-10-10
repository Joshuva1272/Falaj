"""AERIVA core: flight-capacity-driven forecasts of Abu Dhabi hotel guest-nights.

Modules
-------
config    file names, calendar (Ramadan / Eid), cleaning rules
data      load and clean the three challenge files
features  build the market x month panel and engineered features (Appendix A)
models    L0, L1, L2 forecasting models
backtest  rolling-origin validation, metrics, prediction-interval coverage
scenario  capacity what-if engine (Section 4H)
replay    shock replays (e.g. Kuwait 2023)
daily     split monthly forecasts into daily values for scoring
"""
__version__ = "0.1.0"
