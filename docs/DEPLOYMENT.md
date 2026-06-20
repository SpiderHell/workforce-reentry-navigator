# Deployment Guide — Render

## Prerequisites
- Render account (free tier works)
- Anthropic API key

## Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Web Service on Render**
   - New → Web Service → Connect your repo
   - Runtime: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `cd app && uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   - `ANTHROPIC_API_KEY` = your key
   - `DATABASE_URL` = `sqlite+aiosqlite:///./data/reentry_navigator.db`
   - `APP_ENV` = `production`

4. **Deploy Streamlit separately**
   - New → Web Service
   - Start command: `streamlit run streamlit_app.py`
   - Add `API_URL` = your FastAPI service URL

## Database Initialization
The app auto-creates tables on startup via `lifespan` in `main.py`.
