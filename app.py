from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# API KEYS
FLIGHTAPI_KEY = '67fe8b573c6786aff1adcb19'
RAPIDAPI_KEY = '6855179c63mshe4838c2fb96081cp1fe454jsn645c83a158f5'
RAPIDAPI_HOST = 'aerodatabox.p.rapidapi.com'

def format_time(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").strftime("%d %b %Y %I:%M %p")
    except:
        return time_str

def calculate_duration(start, end):
    try:
        fmt = "%Y-%m-%dT%H:%M:%S"
        dep_time = datetime.strptime(start, fmt)
        arr_time = datetime.strptime(end, fmt)
        return int((arr_time - dep_time).total_seconds() / 60)
    except:
        return "N/A"

def get_airline_names_from_aerodata(airport_code):
    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{airport_code}"
    query = {
        "offsetMinutes": "-120",
        "durationMinutes": "720",
        "withLeg": "true",
        "direction": "Both",
        "withCancelled": "true",
        "withCodeshared": "true",
        "withCargo": "true",
        "withPrivate": "true",
        "withLocation": "false"
    }
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    try:
        response = requests.get(url, headers=headers, params=query)
        response.raise_for_status()
        flights = response.json().get('departures', [])
        return [f.get('airline', {}).get('name', 'Unknown') for f in flights][:5]
    except Exception as e:
        print(f"Aerodatabox error: {e}")
        return ['Unknown'] * 5

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_flights', methods=['POST'])
def get_flights():
    origin = request.form.get('origin').strip().upper()
    destination = request.form.get('destination').strip().upper()
    date = request.form.get('date').strip()

    url = f"https://api.flightapi.io/onewaytrip/{FLIGHTAPI_KEY}/{origin}/{destination}/{date}/1/0/0/Economy/USD"
    response = requests.get(url)

    if response.status_code != 200:
        return render_template("index.html", error="❌ Failed to fetch data from FlightAPI.io")

    data = response.json()
    itineraries = data.get('itineraries', [])
    legs_data = {leg['id']: leg for leg in data.get('legs', [])}
    carriers = {c['id']: c['name'] for c in data.get('carriers', [])}
    places = {p['id']: p['name'] for p in data.get('places', [])}

    aerodata_airlines = get_airline_names_from_aerodata(origin)

    flights_info = []
    for i, itinerary in enumerate(itineraries[:5]):
        try:
            leg_id = itinerary['leg_ids'][0]
            leg = legs_data.get(leg_id)
            departure_time = format_time(leg.get('departure'))
            arrival_time = format_time(leg.get('arrival'))
            duration = calculate_duration(leg.get('departure'), leg.get('arrival'))
            departure_airport = places.get(leg.get('origin_place_id'), 'Unknown')
            arrival_airport = places.get(leg.get('destination_place_id'), 'Unknown')
            airline_name = (
                aerodata_airlines[i] if i < len(aerodata_airlines)
                else carriers.get(leg.get('carriers', [])[0], 'Unknown')
            )
            price = round(itinerary['pricing_options'][0]['price']['amount'] * 86, 2)  # USD to INR
            currency = itinerary['pricing_options'][0]['price'].get('currency', 'INR')

            flights_info.append({
                'airline': airline_name,
                'from': f"{departure_airport} at {departure_time}",
                'to': f"{arrival_airport} at {arrival_time}",
                'duration': f"{duration} mins",
                'price': f"{price} {currency}"
            })
        except Exception as e:
            print(f"Error parsing flight {i + 1}: {e}")

    return render_template("index.html", flights=flights_info, origin=origin, destination=destination, date=date)

if __name__ == '__main__':
    app.run(debug=True)
