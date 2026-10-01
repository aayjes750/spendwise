# SpendWise

**Live demo:** [spendwise-aayjes.vercel.app](https://spendwise-aayjes.vercel.app) · *Work in progress*

SpendWise recommends credit cards based on how you actually spend. Enter your yearly spending by category, and it ranks 46+ cards across 12+ issuers by projected first-year net value (rewards + sign-up bonus − annual fee).

## Features

- **Single-card ranking**: the best individual card for your spending
- **Best two-card pairs**: assigns each category to whichever card in the pair earns more
- **No-annual-fee cards** and **no-fee pairs**
- **Student mode**: cards available to people with no credit history
- Handles spending caps and variable bonus categories (e.g. "your highest spending category")

## Tech stack

- **Backend:** Python, FastAPI, Pydantic (deployed on Render)
- **Frontend:** React + Vite (deployed on Vercel)
- **Tests:** pytest regression suite, run on every push via GitHub Actions

## Run locally

```bash
# backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# frontend
cd frontend
npm install
npm run dev

# tests
python3 -m pytest -v
```

## Status

Actively in development. Planned next: more cards, and saving spending profiles.
