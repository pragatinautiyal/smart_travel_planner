import pandas as pd
from datetime import datetime, timedelta
import heapq
import math
from collections import namedtuple
from typing import List, Tuple, Optional, Dict

Flight = namedtuple('Flight', ['from_airport', 'to_airport', 'departure', 'arrival', 'flight_number', 'cost'])

MAX_FLIGHT_SPEED_KMPH = 900

def load_flight_data(flight_file: str) -> pd.DataFrame:
    return pd.read_csv(flight_file)

def load_airport_coordinates(coord_file: str) -> Dict[str, Tuple[float, float]]:
    df = pd.read_csv(coord_file)
    return {row['iata']: (row['latitude'], row['longitude']) for _, row in df.iterrows()}

def parse_time(time_str: str) -> datetime:
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

def build_graph(flights_df: pd.DataFrame) -> Dict[str, List[Dict]]:
    graph = {}
    for _, row in flights_df.iterrows():
        src, dest = row['FromAirport'], row['To']
        dep, arr = parse_time(row['DepartureTime']), parse_time(row['ArrivalTime'])
        cost = row['Cost']
        if src not in graph:
            graph[src] = []
        graph[src].append({
            'to': dest,
            'flight': row['Flight'],
            'departure': dep,
            'arrival': arr,
            'cost': cost
        })
    return graph

def find_min_stops_path(graph: Dict[str, List[Dict]], source: str, destination: str) -> Optional[List[str]]:
    from collections import deque
    visited = set()
    queue = deque([(source, [source])])
    while queue:
        current, path = queue.popleft()
        if current == destination:
            return path
        if current in visited:
            continue
        visited.add(current)
        for neighbor in graph.get(current, []):
            if neighbor['to'] not in path:
                queue.append((neighbor['to'], path + [neighbor['to']]))
    return None

def dijkstra(graph: Dict[str, List[Dict]], source: str, destination: str) -> Tuple[Optional[List[str]], float]:
    heap = [(0, source, [])]
    visited = set()
    while heap:
        cost, node, path = heapq.heappop(heap)
        if node == destination:
            return path + [node], cost
        if node in visited:
            continue
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor['to'] not in visited:
                heapq.heappush(heap, (cost + neighbor['cost'], neighbor['to'], path + [node]))
    return None, float('inf')

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def heuristic(current: str, destination: str, airport_coords: Dict[str, Tuple[float, float]]) -> float:
    lat1, lon1 = airport_coords.get(current, (0, 0))
    lat2, lon2 = airport_coords.get(destination, (0, 0))
    distance_km = haversine(lat1, lon1, lat2, lon2)
    # Estimated time in minutes assuming max flight speed
    return (distance_km / MAX_FLIGHT_SPEED_KMPH) * 60

def a_star(graph: Dict[str, List[Dict]], airport_coords: Dict[str, Tuple[float, float]],
           source: str, destination: str) -> Tuple[Optional[List[str]], float]:
    open_list = [(0, 0, source, [], None)]
    visited = {}

    while open_list:
        f_score, g_score, current, path, last_arrival = heapq.heappop(open_list)

        if current == destination:
            return path + [current], g_score

        if current in visited and visited[current] <= g_score:
            continue

        visited[current] = g_score

        for flight in graph.get(current, []):
            dep_time = flight['departure']
            arr_time = flight['arrival']
            duration = (arr_time - dep_time).total_seconds() / 60

            if last_arrival and dep_time < last_arrival + timedelta(minutes=90):
                continue

            wait_time = (dep_time - last_arrival).total_seconds() / 60 if last_arrival else 0
            new_g = g_score + wait_time + duration
            h = heuristic(flight['to'], destination, airport_coords)
            new_f = new_g + h

            heapq.heappush(open_list, (new_f, new_g, flight['to'], path + [current], arr_time))

    return None, float('inf')

def calculate_total_duration(path: List[str], graph: Dict[str, List[Dict]]) -> Optional[float]:
    if not path or len(path) < 2:
        return None
    total = 0
    for i in range(len(path) - 1):
        flights = [f for f in graph.get(path[i], []) if f['to'] == path[i + 1]]
        if flights:
            dep = flights[0]['departure']
            arr = flights[0]['arrival']
            total += (arr - dep).total_seconds() / 60
        else:
            return None
    return total

def calculate_total_cost(path: List[str], graph: Dict[str, List[Dict]]) -> Optional[float]:
    if not path or len(path) < 2:
        return None
    total = 0
    for i in range(len(path) - 1):
        flights = [f for f in graph.get(path[i], []) if f['to'] == path[i + 1]]
        if flights:
            total += flights[0]['cost']
        else:
            return None
    return total

def extract_flight_details(path: List[str], graph: Dict[str, List[Dict]]) -> List[Flight]:
    flights = []
    if not path or len(path) < 2:
        return flights
    for i in range(len(path) - 1):
        flight_list = [f for f in graph.get(path[i], []) if f['to'] == path[i + 1]]
        if flight_list:
            f = flight_list[0]
            flights.append(
                Flight(
                    from_airport=path[i],
                    to_airport=path[i + 1],
                    departure=f['departure'],
                    arrival=f['arrival'],
                    flight_number=f['flight'],
                    cost=f['cost']
                )
            )
    return flights

# Load data files
flight_file = r'C:\Users\DELL\Desktop\daaproject\new\all_flights.csv'
coord_file = r'C:\Users\DELL\Desktop\daaproject\new\Indian_airports.csv'

flights_df = load_flight_data(flight_file)
airport_coords = load_airport_coordinates(coord_file)
graph = build_graph(flights_df)

def find_shortest_path(source: str, destination: str, filter_option: str) -> Tuple[
    Optional[List[str]], Optional[float], List[Flight], Optional[int], Optional[float]]:
    
    if filter_option == 'minimum_stops':
        path = find_min_stops_path(graph, source, destination)
        stops = len(path) - 1 if path else None
        flights = extract_flight_details(path, graph) if path else []
        duration = calculate_total_duration(path, graph) if path else None
        return path, duration, flights, stops, None

    elif filter_option == 'minimum_cost':
        path, total_cost = dijkstra(graph, source, destination)
        if not path:
            return None, None, [], None, None
        stops = len(path) - 1
        duration = calculate_total_duration(path, graph)
        flights = extract_flight_details(path, graph)
        return path, duration, flights, stops, total_cost

    elif filter_option == 'minimum_time':
        path, duration = a_star(graph, airport_coords, source, destination)
        if not path:
            return None, None, [], None, None
        stops = len(path) - 1
        total_cost = calculate_total_cost(path, graph)
        flights = extract_flight_details(path, graph)
        return path, duration, flights, stops, total_cost

    else:
        raise ValueError("Invalid filter option")
