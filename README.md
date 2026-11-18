# SpendWise - Personal Spending Tracker

Streamlit + SQLite + Pandas + Plotly. Data is saved in `data/tracker.db` (created on first run).

## Install & run
```bash
cd spending_tracker
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501. To back up your data, copy `data/tracker.db`.

## Structure
```
spending_tracker/
├── app.py            # UI pages + navigation
├── database.py       # SQLite schema and CRUD
├── analytics.py      # calculations + Plotly charts
├── styles.py         # dark theme CSS
├── requirements.txt
├── .streamlit/config.toml
└── data/tracker.db   # created automatically
```
