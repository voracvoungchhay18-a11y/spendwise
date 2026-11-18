"""Personal Spending Tracker - Streamlit entry point.  Run:  streamlit run app.py"""
import calendar
import io
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import analytics as an
import database as db
from styles import CSS

st.set_page_config(page_title="Spending Tracker", page_icon="💸", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
db.init_db()

CURRENCIES = list(an.SYMBOLS)
ICONS = {"Dashboard": "📊", "Add transaction": "➕", "History": "🧾", "Budgets": "🎯", "Analytics": "📈", "Savings goals": "🐷", "Settings": "⚙️"}
SUBS = {"Add transaction": "Record money coming in or going out.", "History": "Search, filter, edit and export your records.",
        "Budgets": "Set limits and see how much you have used.", "Analytics": "Charts and reports about your habits.",
        "Savings goals": "Save step by step for what matters.", "Settings": "Currency and categories."}
PAGES = ["Dashboard", "Add transaction", "History", "Budgets", "Analytics", "Savings goals", "Settings"]


def hero(title):
    """Gradient page header with a short subtitle."""
    sub = f"{date.today():%A, %d %B %Y}" if title == "Dashboard" else SUBS.get(title, "")
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)


def step_for(cur):
    return 100.0 if cur in an.ZERO_DECIMAL else 1.0


def num_fmt(cur):
    return "%.0f" if cur in an.ZERO_DECIMAL else "%.2f"


def progress_row(label, spent, budget, cur):
    """Progress bar + warning for one budget."""
    pct = spent / budget if budget else 0
    st.markdown(f"**{label}** · {an.money(spent, cur)} of {an.money(budget, cur)} ({pct:.0%})")
    st.progress(min(pct, 1.0))
    if pct >= 1:
        st.error(f"Over budget by {an.money(spent - budget, cur)}.")
    elif pct >= 0.8:
        st.warning(f"You have used {pct:.0%} of this budget. {an.money(budget - spent, cur)} left.")


# ------------------------------------------------------------------ Dashboard
def page_dashboard(df, cur):
    hero("Dashboard")
    today = date.today()
    week_start, month_start = today - timedelta(days=today.weekday()), today.replace(day=1)
    month_end = an.month_bounds(today.year, today.month)[1]

    if df.empty:
        st.info("No transactions yet. Open **Add transaction** in the sidebar to record your first one.")

    m_exp = an.total(df, "expense", month_start, month_end)
    m_inc = an.total(df, "income", month_start, month_end)
    budgets = db.get_budgets()
    monthly_budget = budgets.get("__monthly__", 0)

    c = st.columns(3)
    c[0].metric("Spent today", an.money(an.total(df, "expense", today, today), cur))
    c[1].metric("Spent this week", an.money(an.total(df, "expense", week_start, today), cur))
    c[2].metric("Spent this month", an.money(m_exp, cur))

    c = st.columns(3)
    c[0].metric("Income this month", an.money(m_inc, cur))
    c[1].metric("Expenses this month", an.money(m_exp, cur))
    c[2].metric("Net this month", an.money(m_inc - m_exp, cur))

    cats = an.by_category(df, month_start, month_end)
    c = st.columns(3)
    c[0].metric("Top category", cats.index[0] if len(cats) else "None yet",
                an.money(cats.iloc[0], cur) if len(cats) else None, delta_color="off")
    if monthly_budget:
        c[1].metric("Budget remaining", an.money(monthly_budget - m_exp, cur))
        days_left = (month_end - today).days + 1
        c[2].metric("Daily limit", an.money(max(monthly_budget - m_exp, 0) / days_left, cur),
                    f"{days_left} days left", delta_color="off")
    else:
        c[1].metric("Budget remaining", "Not set")
        c[2].metric("Daily limit", "Set a budget")

    last = an.prev_month(today)
    last_exp = an.total(df, "expense", *an.month_bounds(last.year, last.month))
    if last_exp > 0:
        diff = (m_exp - last_exp) / last_exp
        st.caption(f"Compared with {last:%B}: you have spent {an.money(m_exp, cur)} vs {an.money(last_exp, cur)} "
                   f"({diff:+.0%}).")

    if monthly_budget:
        progress_row("Monthly budget", m_exp, monthly_budget, cur)
    for cat, b in budgets.items():
        if cat != "__monthly__":
            spent = float(cats.get(cat, 0))
            if b and spent / b >= 0.8:
                progress_row(cat, spent, b, cur)

    if not df.empty:
        left, right = st.columns(2)
        if len(cats):
            left.plotly_chart(an.pie_chart(cats, "This month by category"), width="stretch")
        recent = df[df["date"] >= pd.Timestamp(today - timedelta(days=29))]
        if not recent.empty:
            right.plotly_chart(an.trend_chart(recent, "Last 30 days"), width="stretch")


# ------------------------------------------------------------------ Add transaction
def page_add(cur):
    hero("Add transaction")
    kind = st.radio("Type", ["Expense", "Income"], horizontal=True)
    cats = db.get_categories() if kind == "Expense" else db.INCOME_CATEGORIES
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input(f"Amount ({cur})", min_value=0.0, step=step_for(cur), format=num_fmt(cur))
        category = c2.selectbox("Category", cats)
        tx_date = c1.date_input("Date", value=date.today())
        method = c2.selectbox("Payment method", db.PAYMENT_METHODS)
        desc = st.text_input("Description (optional)", max_chars=200)
        if st.form_submit_button(f"Save {kind.lower()}", type="primary", width="stretch"):
            try:
                db.add_transaction(kind.lower(), amount, category, tx_date, method, desc)
                st.success(f"Saved {kind.lower()} of {an.money(amount, cur)} in {category}.")
            except ValueError as e:
                st.error(str(e))


# ------------------------------------------------------------------ History
def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Transactions")
    return buf.getvalue()


def filter_panel(df, key):
    """Shared date / category / type filters. Returns the filtered frame."""
    c1, c2, c3 = st.columns([2, 2, 1])
    lo = df["date"].min().date() if not df.empty else date.today()
    hi = max(df["date"].max().date(), date.today()) if not df.empty else date.today()
    rng = c1.date_input("Date range", value=(lo, hi), key=f"{key}_rng")
    cats = c2.multiselect("Categories", sorted(df["category"].unique()), key=f"{key}_cat")
    kinds = c3.multiselect("Type", ["expense", "income"], key=f"{key}_type")
    out = df
    if isinstance(rng, (tuple, list)) and len(rng) == 2:
        out = out[(out["date"] >= pd.Timestamp(rng[0])) & (out["date"] <= pd.Timestamp(rng[1]))]
    if cats:
        out = out[out["category"].isin(cats)]
    if kinds:
        out = out[out["type"].isin(kinds)]
    return out


def page_history(df, cur):
    hero("Transaction history")
    if df.empty:
        st.info("Nothing here yet. Add a transaction first.")
        return
    view = filter_panel(df, "hist")
    c1, c2, c3 = st.columns([3, 2, 1])
    q = c1.text_input("Search description, category or payment method")
    sort_by = c2.selectbox("Sort by", ["Date", "Amount", "Category"])
    asc = c3.selectbox("Order", ["Newest/High first", "Oldest/Low first"]) == "Oldest/Low first"
    if q:
        blob = view[["description", "category", "payment_method"]].fillna("").agg(" ".join, axis=1)
        view = view[blob.str.contains(q, case=False, regex=False)]
    view = view.sort_values({"Date": "date", "Amount": "amount", "Category": "category"}[sort_by], ascending=asc)

    st.caption(f"{len(view)} transactions · expenses {an.money(an.total(view, 'expense'), cur)} · "
               f"income {an.money(an.total(view, 'income'), cur)}")
    st.dataframe(view.drop(columns="id").assign(date=view["date"].dt.date), hide_index=True, width="stretch",
                 column_config={"amount": st.column_config.NumberColumn(format="%.2f"),
                                "payment_method": "Payment method"})
    exp = view.drop(columns="id").assign(date=view["date"].dt.date)
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("Export CSV", exp.to_csv(index=False).encode("utf-8"), "transactions.csv", "text/csv")
    d2.download_button("Export Excel", to_excel(exp), "transactions.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("Edit or delete")
    labels = {int(r.id): f"{r.date:%Y-%m-%d} · {r.category} · {an.money(r.amount, cur)} · {r.description or '-'}"
              for r in view.itertuples()}
    if not labels:
        return
    tid = st.selectbox("Choose a transaction", list(labels), format_func=labels.get)
    row = df[df["id"] == tid].iloc[0]
    with st.form(f"edit_{tid}"):
        c1, c2 = st.columns(2)
        kinds = ["expense", "income"]
        kind = c1.selectbox("Type", kinds, index=kinds.index(row["type"]))
        all_cats = list(dict.fromkeys(db.get_categories() + db.INCOME_CATEGORIES + [row["category"]]))
        category = c2.selectbox("Category", all_cats, index=all_cats.index(row["category"]))
        amount = c1.number_input("Amount", min_value=0.0, value=float(row["amount"]), step=step_for(cur),
                                 format=num_fmt(cur))
        tx_date = c2.date_input("Date", value=row["date"].date())
        methods = list(dict.fromkeys(db.PAYMENT_METHODS + [row["payment_method"]]))
        method = c1.selectbox("Payment method", methods, index=methods.index(row["payment_method"]))
        desc = c2.text_input("Description", value=row["description"] or "")
        confirm = st.checkbox("Confirm delete")
        b1, b2 = st.columns(2)
        save = b1.form_submit_button("Save changes", type="primary", width="stretch")
        delete = b2.form_submit_button("Delete transaction", width="stretch")
    try:
        if save:
            db.update_transaction(tid, kind, amount, category, tx_date, method, desc)
            st.success("Saved changes.")
            st.rerun()
        if delete:
            if confirm:
                db.delete_transaction(tid)
                st.success("Deleted.")
                st.rerun()
            else:
                st.warning("Tick 'Confirm delete' first.")
    except ValueError as e:
        st.error(str(e))


# ------------------------------------------------------------------ Budgets
def page_budgets(df, cur):
    hero("Budgets")
    today = date.today()
    start, end = an.month_bounds(today.year, today.month)
    budgets = db.get_budgets()
    cats = db.get_categories()
    with st.form("budget_form"):
        st.subheader("Monthly budget")
        monthly = st.number_input(f"Total budget ({cur}). Use 0 to remove.", min_value=0.0, step=step_for(cur) * 10,
                                  value=float(budgets.get("__monthly__", 0)), format=num_fmt(cur))
        st.subheader("Category budgets")
        cols = st.columns(2)
        vals = {c: cols[i % 2].number_input(c, min_value=0.0, step=step_for(cur) * 5, format=num_fmt(cur),
                                            value=float(budgets.get(c, 0)), key=f"b_{c}")
                for i, c in enumerate(cats)}
        if st.form_submit_button("Save budgets", type="primary", width="stretch"):
            db.set_budget("__monthly__", monthly)
            for c, v in vals.items():
                db.set_budget(c, v)
            st.success("Budgets saved.")
            st.rerun()

    st.subheader(f"Usage in {today:%B %Y}")
    spent_by_cat = an.by_category(df, start, end)
    if not budgets:
        st.info("Set a budget above to see your progress here.")
    if "__monthly__" in budgets:
        progress_row("Monthly budget", an.total(df, "expense", start, end), budgets["__monthly__"], cur)
    for c in cats:
        if c in budgets:
            progress_row(c, float(spent_by_cat.get(c, 0)), budgets[c], cur)


# ------------------------------------------------------------------ Analytics
def page_analytics(df, cur):
    hero("Analytics & reports")
    if df.empty:
        st.info("Add some transactions to unlock charts.")
        return
    view = filter_panel(df, "ana")
    t1, t2, t3, t4, t5 = st.tabs(["By category", "Monthly", "Trends", "Income vs expenses", "Monthly summary"])
    with t1:
        cats = an.by_category(view)
        st.plotly_chart(an.pie_chart(cats), width="stretch") if len(cats) else st.info("No expenses in this filter.")
    with t2:
        if view[view["type"] == "expense"].empty:
            st.info("No expenses in this filter.")
        else:
            st.plotly_chart(an.monthly_bar(view), width="stretch")
    with t3:
        if view[view["type"] == "expense"].empty:
            st.info("No expenses in this filter.")
        else:
            st.plotly_chart(an.trend_chart(view), width="stretch")
    with t4:
        st.plotly_chart(an.income_vs_expense(view), width="stretch")
    with t5:
        months = sorted(df["date"].dt.strftime("%Y-%m").unique(), reverse=True)
        sel = st.selectbox("Month", months)
        y, m = map(int, sel.split("-"))
        s, e = an.month_bounds(y, m)
        inc, exp = an.total(df, "income", s, e), an.total(df, "expense", s, e)
        p = an.prev_month(s)
        prev_exp = an.total(df, "expense", *an.month_bounds(p.year, p.month))
        c = st.columns(4)
        c[0].metric("Income", an.money(inc, cur))
        c[1].metric("Expenses", an.money(exp, cur))
        c[2].metric("Saved", an.money(inc - exp, cur))
        c[3].metric("Savings rate", f"{(inc - exp) / inc:.0%}" if inc else "n/a")
        cats = an.by_category(df, s, e)
        if len(cats):
            st.write(f"**{calendar.month_name[m]} {y}:** your biggest category was **{cats.index[0]}** "
                     f"({an.money(cats.iloc[0], cur)}, {cats.iloc[0] / exp:.0%} of spending).")
            if prev_exp:
                st.write(f"Spending was {(exp - prev_exp) / prev_exp:+.0%} compared with {p:%B}.")
            st.dataframe(cats.rename("Spent").reset_index(), hide_index=True, width="stretch")


# ------------------------------------------------------------------ Savings goals
def page_goals(cur):
    hero("Savings goals")
    with st.form("goal_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 2, 2])
        name = c1.text_input("Goal name")
        target = c2.number_input(f"Target ({cur})", min_value=0.0, step=step_for(cur) * 10, format=num_fmt(cur))
        saved = c3.number_input("Already saved", min_value=0.0, step=step_for(cur) * 10, format=num_fmt(cur))
        if st.form_submit_button("Create goal", type="primary"):
            try:
                db.add_goal(name, target, saved)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    goals = db.get_goals()
    if goals.empty:
        st.info("No goals yet. Create one above.")
    for g in goals.itertuples():
        with st.container(border=True):
            pct = min(g.saved / g.target, 1.0)
            st.markdown(f"**{g.name}** · {an.money(g.saved, cur)} of {an.money(g.target, cur)} ({pct:.0%})")
            st.progress(pct)
            if g.saved >= g.target:
                st.success("Goal reached!")
            c1, c2, c3 = st.columns([2, 1, 1])
            amt = c1.number_input("Amount", min_value=0.0, step=step_for(cur) * 10, key=f"ga_{g.id}",
                                  format=num_fmt(cur), label_visibility="collapsed")
            if c2.button("Add funds", key=f"gadd_{g.id}", width="stretch") and amt > 0:
                db.add_to_goal(g.id, amt)
                st.rerun()
            if c3.button("Delete", key=f"gdel_{g.id}", width="stretch"):
                db.delete_goal(g.id)
                st.rerun()


# ------------------------------------------------------------------ Settings
def page_settings(cur):
    hero("Settings")
    st.subheader("Currency")
    new = st.selectbox("Display currency", CURRENCIES, index=CURRENCIES.index(cur))
    st.caption("This changes the symbol and formatting only. Amounts are not converted.")
    if new != cur and st.button("Save currency", type="primary"):
        db.set_setting("currency", new)
        st.rerun()

    st.subheader("Custom categories")
    with st.form("cat_form", clear_on_submit=True):
        name = st.text_input("New expense category")
        if st.form_submit_button("Add category"):
            try:
                db.add_category(name)
                st.success(f"Added '{name.strip()}'.")
            except ValueError as e:
                st.error(str(e))
    custom = db.get_custom_categories()
    if custom:
        rm = st.selectbox("Delete a custom category", custom)
        st.caption("Its transactions will move to 'Other'.")
        if st.button("Delete category"):
            db.delete_category(rm)
            st.rerun()


# ------------------------------------------------------------------ Router
def main():
    cur = db.get_setting("currency", "USD")
    with st.sidebar:
        st.markdown('<div class="brand">Spend<span>Wise</span></div><div class="hint">Know where your money goes</div>',
                    unsafe_allow_html=True)
        page = st.radio("Navigate", PAGES, label_visibility="collapsed", format_func=lambda x: f"{ICONS[x]}  {x}")
        st.caption(f"Currency: {cur}")
    df = db.load_transactions()
    try:
        {"Dashboard": lambda: page_dashboard(df, cur), "Add transaction": lambda: page_add(cur),
         "History": lambda: page_history(df, cur), "Budgets": lambda: page_budgets(df, cur),
         "Analytics": lambda: page_analytics(df, cur), "Savings goals": lambda: page_goals(cur),
         "Settings": lambda: page_settings(cur)}[page]()
    except Exception as e:  # last-resort guard so one bad page never crashes the app
        st.error(f"Something went wrong: {e}")


main()
