# AI Data Analysis

Upload a CSV/Excel file, get instant charts and summary stats, and ask
questions about your data in plain English.

**Stack:** Python, Pandas, Streamlit, Plotly, OpenAI API

## 1. Set up

You need Python 3.9+ installed. Then, in this folder:

```bash
# create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

## 2. Run it

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

## 3. Try it

1. In the sidebar, upload `sample_sales_data.csv` (included in this folder)
   to see the charts and summary stats work instantly — no API key needed.
2. To try the "Ask your data" chat box, get a free API key at
   [platform.openai.com/api-keys](https://platform.openai.com/api-keys),
   paste it into the sidebar, and ask something like:
   *"Which category had the highest growth?"*

The key is only used in your own browser session to call OpenAI directly —
it is never saved to a file or sent anywhere else.

## What it does

- **KPIs** — row/column counts, how much data is missing
- **Auto charts** — trend over time (if a date column is found), a
  distribution histogram, a category breakdown, and a correlation heatmap
- **Ask your data** — type a question, and GPT answers it using a summary
  of your dataset (column names, stats, and sample rows)

## Deploying it

The easiest free option is **Streamlit Community Cloud**:

1. Push this folder to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo,
   and point it at `app.py`.
3. Done — you get a public link instantly. Users paste their own OpenAI key
   into the sidebar when they use it, so you don't need to share yours.

## Notes / things you could extend

- Right now the AI answers using a *summary* of your data (stats + sample
  rows), not the full dataset — good for privacy and cost, but it means very
  precise row-level questions may not be answerable. A next step could be
  letting GPT generate a Pandas query to run on the real data for exact
  answers.
- You could add a "Download report" button that exports the charts and
  summary as a PDF.
