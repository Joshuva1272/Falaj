"""Split monthly forecasts into days (brief Section 4F, daily output for scoring).

Shares come from the same weekday 364 days earlier and always sum to 1 within the month.
Ramadan / Eid adjustment of the shares is not implemented yet.
"""
import pandas as pd


def daily_split(monthly_forecast: float, history: pd.Series, month: pd.Period) -> pd.Series:
    """history: daily Guests for one market indexed by date (must cover the same month last year)."""
    days = pd.date_range(month.start_time, month.end_time.normalize(), freq="D")
    ly = history.reindex(days - pd.Timedelta(days=364))
    ly.index = days
    ly = ly.fillna(ly.mean())
    return monthly_forecast * ly / ly.sum()
