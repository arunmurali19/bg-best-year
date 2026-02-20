# How to Run

## Prerequisites

- Python 3.10+
- pip

## Quick Start

```bash
# 1. Activate the virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Regenerate tournament data from BGG CSV
python data_pipeline/generate_tournament.py

# 4. Start the web app (auto-initializes DB on first run)
python scripts/run.py
```

The app will be available at **http://127.0.0.1:5000**.

## URLs

| Page | URL |
|------|-----|
| Home (vote) | http://127.0.0.1:5000/ |
| Bracket | http://127.0.0.1:5000/bracket |
| Results | http://127.0.0.1:5000/results |
| Admin | http://127.0.0.1:5000/admin/admin123 |

## Admin Operations

Access the admin panel at `/admin/admin123` (change the secret via `ADMIN_SECRET` environment variable).

From the admin panel you can:

- **View vote tallies** for all active matchups
- **Advance to the next round** - closes current matchups, tallies votes, and sets up the next round
- **Reset the tournament** - clears all votes and resets the bracket

## Workflow

1. Start the app
2. Share the URL with voters
3. Once enough votes are in for the current round, go to the admin panel and click "Advance to Next Round"
4. Repeat until the Final is decided

## Re-initializing

To start fresh:

```bash
# Delete the database
rm webapp/tournament.db

# Re-run (auto-initializes)
python scripts/run.py
```

To regenerate tournament seeding from the CSV:

```bash
python data_pipeline/generate_tournament.py
rm webapp/tournament.db
python scripts/run.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_SECRET` | `admin123` | Admin panel URL secret |
| `SECRET_KEY` | `dev-secret-...` | Flask session secret |

Set these as environment variables before running.
