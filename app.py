import csv
import heapq
import math
import os
import urllib.request
from collections import deque
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

airports = {}
graph = {}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
AIRPORTS_FILE = os.path.join(DATA_DIR, "airports.dat")
ROUTES_FILE = os.path.join(DATA_DIR, "routes.dat")

AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"


def download_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(AIRPORTS_FILE):
        print("Downloading airports.dat...")
        urllib.request.urlretrieve(AIRPORTS_URL, AIRPORTS_FILE)
    if not os.path.exists(ROUTES_FILE):
        print("Downloading routes.dat...")
        urllib.request.urlretrieve(ROUTES_URL, ROUTES_FILE)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_data():
    global airports, graph
    airports = {}
    graph = {}

    with open(AIRPORTS_FILE, encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 8:
                continue
            iata = row[4].strip('"')
            if iata == r"\N" or len(iata) != 3:
                continue
            try:
                lat, lon = float(row[6]), float(row[7])
            except ValueError:
                continue
            airports[iata] = {
                "name": row[1].strip('"'),
                "city": row[2].strip('"'),
                "country": row[3].strip('"'),
                "lat": lat,
                "lon": lon,
            }
            graph[iata] = []

    with open(ROUTES_FILE, encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            src, dst = row[2].strip('"'), row[4].strip('"')
            if src not in airports or dst not in airports:
                continue
            a, b = airports[src], airports[dst]
            dist = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
            graph[src].append((dst, dist))

    print(f"Loaded {len(airports)} airports and {sum(len(v) for v in graph.values())} routes.")


def dijkstra(src, dst):
    dist = {src: 0}
    prev = {src: None}
    pq = [(0, src)]
    visited = set()

    while pq:
        cost, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == dst:
            break
        for v, w in graph.get(u, []):
            nc = cost + w
            if nc < dist.get(v, float("inf")):
                dist[v] = nc
                prev[v] = u
                heapq.heappush(pq, (nc, v))

    if dst not in dist:
        return None, None

    path = []
    cur = dst
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path, dist[dst]


def bfs(src, dst):
    if src == dst:
        return [src]
    queue = deque([[src]])
    visited = {src}

    while queue:
        path = queue.popleft()
        u = path[-1]
        for v, _ in graph.get(u, []):
            if v == dst:
                return path + [v]
            if v not in visited:
                visited.add(v)
                queue.append(path + [v])
    return None


def path_to_response(path, total_km=None):
    stops = []
    for code in path:
        a = airports[code]
        stops.append({
            "iata": code,
            "name": a["name"],
            "city": a["city"],
            "country": a["country"],
            "lat": a["lat"],
            "lon": a["lon"],
        })
    segment_km = []
    for i in range(len(path) - 1):
        a1, a2 = airports[path[i]], airports[path[i + 1]]
        segment_km.append(round(haversine(a1["lat"], a1["lon"], a2["lat"], a2["lon"])))
    return {"path": stops, "segments_km": segment_km, "total_km": round(total_km) if total_km else None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search_airports():
    q = request.args.get("q", "").strip().upper()
    if len(q) < 2:
        return jsonify([])
    results = []
    for code, a in airports.items():
        if q in code or q in a["city"].upper() or q in a["name"].upper():
            results.append({"iata": code, "name": a["name"], "city": a["city"], "country": a["country"]})
        if len(results) >= 10:
            break
    return jsonify(results)


@app.route("/route")
def find_route():
    src = request.args.get("src", "").strip().upper()
    dst = request.args.get("dst", "").strip().upper()

    if src not in airports or dst not in airports:
        return jsonify({"error": "Invalid airport code(s)."}), 400
    if src == dst:
        return jsonify({"error": "Source and destination must differ."}), 400

    dijk_path, dijk_km = dijkstra(src, dst)
    bfs_path = bfs(src, dst)

    result = {}
    if dijk_path:
        result["dijkstra"] = path_to_response(dijk_path, dijk_km)
    else:
        result["dijkstra"] = None

    if bfs_path:
        a1, a2_prev = airports[bfs_path[0]], None
        total = 0
        for i in range(len(bfs_path) - 1):
            a1, a2 = airports[bfs_path[i]], airports[bfs_path[i + 1]]
            total += haversine(a1["lat"], a1["lon"], a2["lat"], a2["lon"])
        result["bfs"] = path_to_response(bfs_path, total)
    else:
        result["bfs"] = None

    return jsonify(result)


if __name__ == "__main__":
    download_data()
    load_data()
    app.run(debug=True)