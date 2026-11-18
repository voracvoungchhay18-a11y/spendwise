"""Custom CSS: dark glass look, gradient accents, pill navigation, responsive tweaks."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');
:root { --ok:#3DDC97; --blue:#5B8CFF; --bad:#FF6B6B; --line:rgba(255,255,255,.08); --card:rgba(255,255,255,.04); }
html, body, [class*="css"], .stApp { font-family: 'Manrope', sans-serif; }
.stApp {
  background:
    radial-gradient(900px 500px at 85% -10%, rgba(91,140,255,.16), transparent 60%),
    radial-gradient(800px 500px at -10% 10%, rgba(61,220,151,.12), transparent 55%),
    #0B0F15;
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }

/* header */
.hero { margin: 0 0 1.4rem 0; padding: 1.4rem 1.6rem; border-radius: 22px; border: 1px solid var(--line);
  background: linear-gradient(135deg, rgba(61,220,151,.14), rgba(91,140,255,.10) 55%, rgba(255,255,255,.02)); }
.hero h1 { margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -.03em; padding: 0; }
.hero p { margin: .25rem 0 0; color: #9AA6B5; font-size: .95rem; }
h2, h3 { font-weight: 800; letter-spacing: -.02em; }

/* metric cards */
div[data-testid="stMetric"] {
  position: relative; overflow: hidden; background: linear-gradient(160deg, rgba(255,255,255,.065), rgba(255,255,255,.02));
  border: 1px solid var(--line); border-radius: 20px; padding: 18px 22px; transition: transform .15s, border-color .15s;
}
div[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: rgba(61,220,151,.45); }
div[data-testid="stMetric"]::before { content:""; position:absolute; left:0; top:16px; bottom:16px; width:4px; border-radius:0 4px 4px 0;
  background: linear-gradient(var(--ok), var(--blue)); }
div[data-testid="stMetricLabel"] p { color: #9AA6B5; font-weight: 600; font-size: .85rem; }
div[data-testid="stMetricValue"] { font-weight: 800; font-size: 1.7rem; letter-spacing: -.02em; }

/* containers */
div[data-testid="stForm"], div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--card); border: 1px solid var(--line); border-radius: 20px; }
div[data-testid="stPlotlyChart"] { background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 6px; }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
div[data-testid="stAlert"] { border-radius: 14px; border: 1px solid var(--line); }

/* inputs and buttons */
input, textarea, div[data-baseweb="select"] > div { border-radius: 12px !important; }
.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
  border-radius: 12px; font-weight: 700; border: 1px solid var(--line); transition: transform .12s, box-shadow .12s; }
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-1px); }
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background: linear-gradient(135deg, #3DDC97, #2EC4D6) !important; color: #04170E !important; border: 0 !important;
  box-shadow: 0 6px 18px rgba(61,220,151,.25); }

/* progress */
div[data-testid="stProgress"] [role="progressbar"] > div { background: linear-gradient(90deg, #3DDC97, #5B8CFF) !important; border-radius: 8px; }

/* tabs */
button[data-baseweb="tab"] { font-weight: 700; border-radius: 10px 10px 0 0; }

/* sidebar */
section[data-testid="stSidebar"] { background: rgba(8,11,16,.92); border-right: 1px solid var(--line); }
.brand { font-size: 1.5rem; font-weight: 800; letter-spacing: -.03em; margin-bottom: .1rem; }
.brand span { background: linear-gradient(90deg, #3DDC97, #5B8CFF); -webkit-background-clip: text; color: transparent; }
.hint { color: #8A96A5; font-size: .88rem; margin-bottom: 1rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: .6rem .85rem; border-radius: 12px; width: 100%;
  border: 1px solid transparent; transition: background .12s; cursor: pointer; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(255,255,255,.05); }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(135deg, rgba(61,220,151,.18), rgba(91,140,255,.14)); border-color: rgba(61,220,151,.35); }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-weight: 700; font-size: .98rem; }

@media (max-width: 700px) {
  .block-container { padding: 1rem .8rem; }
  .hero { padding: 1rem 1.1rem; } .hero h1 { font-size: 1.5rem; }
  div[data-testid="stMetricValue"] { font-size: 1.3rem; }
}
</style>
"""
