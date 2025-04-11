import requests
from datetime import datetime

# API Keys
FLIGHTAPI_KEY = '67f8e5528403a0d39db01c26'
RAPIDAPI_KEY = '6855179c63mshe4838c2fb96081cp1fe454jsn645c83a158f5'
RAPIDAPI_HOST = 'aerodatabox.p.rapidapi.com'

# Format helpers
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

# Aerodatabox - Airline names from airport
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
        airline_names = [f.get('airline', {}).get('name', 'Unknown') for f in flights]
        return airline_names[:5]  # Return names for the first 5 flights
    except Exception as e:
        print(f"Error fetching from Aerodatabox: {e}")
        return ['Unknown'] * 5

# FlightAPI.io - Main flight details
def get_flight_details(origin, destination, date):
    print(f"\n🛫 Flights from {origin} to {destination} on {date}:\n")

    # Fetch Aerodatabox airline names
    aerodata_airlines = get_airline_names_from_aerodata(origin)

    # FlightAPI.io request
    url = f"https://api.flightapi.io/onewaytrip/{FLIGHTAPI_KEY}/{origin}/{destination}/{date}/1/0/0/Economy/USD"
    response = requests.get(url)

    if response.status_code != 200:
        print("❌ Failed to fetch data from FlightAPI.io")
        return

    data = response.json()
    itineraries = data.get('itineraries', [])
    legs_data = {leg['id']: leg for leg in data.get('legs', [])}
    carriers = {c['id']: c['name'] for c in data.get('carriers', [])}
    places = {p['id']: p['name'] for p in data.get('places', [])}

    if not itineraries:
        print("No flights found.")
        return

    for i, itinerary in enumerate(itineraries[:5], start=1):
        try:
            leg_id = itinerary['leg_ids'][0]
            leg = legs_data.get(leg_id)
            if not leg:
                raise ValueError("Leg not found")

            departure_time = leg.get('departure')
            arrival_time = leg.get('arrival')
            duration = calculate_duration(departure_time, arrival_time)
            departure_airport = places.get(leg.get('origin_place_id'), 'Unknown')
            arrival_airport = places.get(leg.get('destination_place_id'), 'Unknown')
            airline_name = (
                aerodata_airlines[i - 1] if i <= 5 else carriers.get(leg.get('carriers', [])[0], 'Unknown')
            )
            price = itinerary['pricing_options'][0]['price']['amount']
            currency = itinerary['pricing_options'][0]['price'].get('currency', 'INR')
            price *= 86


            print(f"✈️ Flight {i}: {airline_name}")
            print(f"   From: {departure_airport} at {format_time(departure_time)}")
            print(f"   To:   {arrival_airport} at {format_time(arrival_time)}")
            print(f"   Duration: {duration} mins")
            print(f"   Price: {price} {currency}\n")
        except Exception as e:
            print(f"⚠️ Error processing flight {i}: {e}")

origin = input("Enter source airport code (e.g., DEL): ").strip().upper()
destination = input("Enter destination airport code (e.g., PAT): ").strip().upper()
date = input("Enter date of travel (YYYY-MM-DD): ").strip()

get_flight_details(origin, destination, date)

