from flask import Flask, request, jsonify, render_template
from graph import find_shortest_path, airport_coords
import pandas as pd
import os

template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

app = Flask(__name__, template_folder=template_path, static_folder=static_dir)

# Global mappings
city_to_iata = {}
iata_to_city = {}
valid_iata_codes = set()
iata_to_airport_name = {}

@app.route('/airport-mapping')
def airport_mapping():
    return jsonify(dict(sorted(city_to_iata.items())))

# Load city-to-IATA mappings
def load_mappings(city_file):
    df = pd.read_csv(city_file)
    for _, row in df.iterrows():
        city = row['City'].strip()
        iata = row['IATA'].strip().upper()
        city_to_iata[city.lower()] = iata
        iata_to_city[iata] = city
        valid_iata_codes.add(iata)

# Load airport names
def load_airport_names(airport_file):
    df = pd.read_csv(airport_file)
    for _, row in df.iterrows():
        iata_code = row['IATA'].strip().upper()
        airport_name = row['Airport Name'].strip()
        iata_to_airport_name[iata_code] = airport_name

load_mappings(r'E:\smart_travel_planner\datasets\airports.csv')
load_airport_names(r'E:\smart_travel_planner\datasets\airports.csv')

# Resolve input to IATA code
def resolve_to_iata(user_input):
    user_input = user_input.strip()
    if not user_input:
        return None
    code = user_input.upper()
    if code in valid_iata_codes:
        return code
    city = user_input.lower()
    return city_to_iata.get(city)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/shortest-path', methods=['POST'])
def shortest_path():
    try:
        data = request.get_json()
        print("Received JSON:", data)

        if data is None:
            return jsonify({'error': 'Invalid or missing JSON data'}), 400

        source_input = data.get('source')
        destination_input = data.get('destination')
        filter_option = data.get('filter')

        if not source_input or not destination_input:
            return jsonify({'error': 'Missing source or destination'}), 400

        source = resolve_to_iata(source_input)
        destination = resolve_to_iata(destination_input)

        if not source or not destination:
            return jsonify({'error': 'Invalid city name or IATA code provided'}), 400

        if filter_option not in ['minimum_stops', 'minimum_cost', 'minimum_time']:
            return jsonify({'error': 'Invalid filter option'}), 400

        path, duration_minutes, flights, stops, total_cost = find_shortest_path(
            source, destination, filter_option
        )

        if not path:
            return jsonify({'error': 'No path found'}), 404

        response = {
            'path': path,
            'duration_minutes': duration_minutes,
            'flights': [{
                'from': f.from_airport,
                'to': f.to_airport,
                'from_city': iata_to_city.get(f.from_airport.strip().upper(), "Unknown"),
                'to_city': iata_to_city.get(f.to_airport.strip().upper(), "Unknown"),
                'departure': f.departure.isoformat(),
                'arrival': f.arrival.isoformat(),
                'flight': f.flight_number,
                'cost': f.cost,
                'from_coords': airport_coords.get(f.from_airport.strip().upper()),
                'to_coords': airport_coords.get(f.to_airport.strip().upper()),
                'from_airport': iata_to_airport_name.get(f.from_airport.strip().upper(), "Unknown Airport"),
                'to_airport': iata_to_airport_name.get(f.to_airport.strip().upper(), "Unknown Airport")
            } for f in flights]
        }

        if filter_option == "minimum_stops":
            response['stops'] = stops
        elif filter_option=="minimum_cost":
            response['total_cost']=total_cost
        else:
            response['duration_minutes'] = duration_minutes

        print("Response:", response)
        return jsonify(response)

    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({'error': 'Internal server error: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
