# Flight Route Shortest Path Finder

Finds the optimal flight path between two airports using **Dijkstra's algorithm** (minimum distance) and **BFS** (fewest stops), then compares both results side by side.

**Dataset:** OpenFlights — ~7,000 airports, ~67,000 real-world routes (no API key needed, downloaded automatically on first run).

---

## Repo Structure

```
flight_app/
├── app.py               # Flask backend — graph construction, Dijkstra, BFS, API routes
├── templates/
│   └── index.html       # Single-page frontend — search, results, comparison
├── data/                # Auto-created on first run
│   ├── airports.dat     # Downloaded from OpenFlights
│   └── routes.dat       # Downloaded from OpenFlights
├── requirements.txt
└── README.md
```

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app (data files download automatically on first run)
python app.py

# 3. Open in browser
http://127.0.0.1:5000
```

---

## How It Works

1. **Graph construction** — airports are nodes, routes are directed edges weighted by great-circle distance (km).
2. **Dijkstra** — finds the path with minimum total kilometers flown.
3. **BFS** — finds the path with fewest number of layovers (unweighted).
4. The UI shows both paths and highlights the tradeoff between the two.

---

## Requirements

- Python 3.8+
- Flask
- Internet connection on first run (to download data files ~3 MB total)

AI statement: Everything in this project 2 were developed by myself.