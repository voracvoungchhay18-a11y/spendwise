"""Pure calculation + Plotly chart helpers (no Streamlit calls here)."""
import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

SYMBOLS = {"USD": "$", "KHR": "៛", "EUR": "€", "GBP": "£", "JPY": "¥", "THB": "฿"}
ZERO_DECIMAL = {"KHR", "JPY"}
INCOME_C, EXPENSE_C = "#3DDC97", "#FF6B6B"
PALETTE = ["#3DDC97", "#5B8CFF", "#FFB84D", "#FF6B6B", "#B07CFF", "#2EC4D6", "#F78FB3", "#9AA5B1", "#C7E85A"]


def money(x, cur="USD"):
    """Format a number with the currency symbol (KHR/JPY show no decimals)."""
    d = 0 if cur in ZERO_DECIMAL else 2
    s = f"{SYMBOLS.get(cur, '')}{abs(x):,.{d}f}"
    return f"-{s}" if x < 0 else s


def total(df, kind, start=None, end=None):
    """Sum of amounts of one type between two dates (inclusive)."""
    m = df["type"] == kind
    if start is not None:
        m &= df["date"] >= pd.Timestamp(start)
    if end is not None:
        m &= df["date"] <= pd.Timestamp(end)
    return float(df.loc[m, "amount"].sum())


def month_bounds(year, month):
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def prev_month(d):
    return (d.replace(day=1) - timedelta(days=1)).replace(day=1)


def by_category(df, start=None, end=None):
    m = df["type"] == "expense"
    if start is not None:
        m &= df["date"] >= pd.Timestamp(start)
    if end is not None:
        m &= df["date"] <= pd.Timestamp(end)
    return df[m].groupby("category")["amount"].sum().sort_values(ascending=False)


def _style(fig, h=340):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=40, b=10), height=h, font=dict(family="Manrope, sans-serif", color="#C9D1DB"), colorway=PALETTE,
                      legend=dict(orientation="h", y=-0.15))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    return fig


def pie_chart(cat_series, title="Spending by category"):
    fig = px.pie(values=cat_series.values, names=cat_series.index, hole=.55, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:,.2f} (%{percent})<extra></extra>")
    fig.update_layout(title=title)
    return _style(fig)


def monthly_bar(df, title="Monthly spending"):
    e = df[df["type"] == "expense"].copy()
    e["month"] = e["date"].dt.strftime("%Y-%m")
    g = e.groupby("month")["amount"].sum().reset_index()
    fig = px.bar(g, x="month", y="amount", color_discrete_sequence=[EXPENSE_C], title=title)
    fig.update_traces(marker_cornerradius=6)
    return _style(fig)


def income_vs_expense(df, title="Income vs expenses"):
    d = df.copy()
    d["month"] = d["date"].dt.strftime("%Y-%m")
    g = d.groupby(["month", "type"])["amount"].sum().reset_index()
    fig = px.bar(g, x="month", y="amount", color="type", barmode="group", title=title,
                 color_discrete_map={"income": INCOME_C, "expense": EXPENSE_C})
    fig.update_traces(marker_cornerradius=6)
    return _style(fig)


def trend_chart(df, title="Daily spending trend"):
    e = df[df["type"] == "expense"].groupby("date")["amount"].sum()
    if e.empty:
        return _style(go.Figure())
    e = e.reindex(pd.date_range(e.index.min(), e.index.max()), fill_value=0)
    fig = go.Figure()
    fig.add_bar(x=e.index, y=e.values, name="Daily", marker_color="rgba(91,140,255,.45)")
    fig.add_scatter(x=e.index, y=e.rolling(7, min_periods=1).mean(), name="7-day average",
                    line=dict(color=INCOME_C, width=3))
    fig.update_layout(title=title)
    return _style(fig)
