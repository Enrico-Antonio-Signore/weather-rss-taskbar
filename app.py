from flask import Flask, Response, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime
from functools import wraps

# Configurazione iniziale
app = Flask(__name__, template_folder='templates')
WEATHER_API_KEY = "534016f5b5f34a0ca29102123252503"
DEFAULT_LOCATION = {'lat': 41.9028, 'lon': 12.4964}  # Coordinate di Roma come fallback
API_TIMEOUT = 10  # Timeout in secondi per le richieste API

# ==============================================
# DECORATORI & HELPER FUNCTIONS
# ==============================================

def handle_errors(f):
    """Decoratore per la gestione centralizzata degli errori"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.Timeout:
            app.logger.error("Timeout nel collegamento al servizio meteo")
            return jsonify({'error': 'Il servizio meteo non risponde'}), 504
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Errore di connessione: {str(e)}")
            return jsonify({'error': 'Errore di connessione al servizio meteo'}), 502
        except KeyError as e:
            app.logger.error(f"Dati API non validi: {str(e)}")
            return jsonify({'error': 'Formato dati meteo non riconosciuto'}), 502
        except Exception as e:
            app.logger.error(f"Errore imprevisto: {str(e)}")
            return jsonify({'error': 'Errore interno del server'}), 500
    return wrapper

def get_emoji(condition):
    """Restituisce l'emoji corrispondente alla condizione meteo"""
    emoji_map = {
        'clear': '☀️', 'sunny': '☀️', 'cloud': '☁️', 'cloudy': '☁️',
        'rain': '🌧️', 'thunder': '⛈️', 'snow': '❄️', 'mist': '🌫️',
        'fog': '🌁', 'drizzle': '🌦️', 'shower': '🌧️', 'overcast': '☁️'
    }
    return emoji_map.get(condition.lower().split()[0], '🌡️')

def translate_condition(condition_en):
    """Traduce le condizioni meteo da inglese a italiano"""
    translation_map = {
        'Sunny': 'Soleggiato',
        'Clear': 'Sereno',
        'Partly cloudy': 'Parzialmente nuvoloso',
        'Cloudy': 'Nuvoloso',
        'Overcast': 'Coperto',
        'Mist': 'Foschia',
        'Fog': 'Nebbia',
        'Light rain': 'Pioggia leggera',
        'Moderate rain': 'Pioggia moderata',
        'Heavy rain': 'Pioggia intensa',
        'Light snow': 'Neve leggera',
        'Moderate snow': 'Neve moderata',
        'Heavy snow': 'Neve intensa',
        'Light rain shower': 'Rovescio leggero',
        'Moderate rain shower': 'Rovescio moderato',
        'Heavy rain shower': 'Rovescio intenso',
        'Thunderstorm': 'Temporale',
        'Patchy rain possible': 'Possibili piogge sparse',
        'Patchy snow possible': 'Possibili nevicate sparse'
    }
    return translation_map.get(condition_en, condition_en)

def format_time(time_str, full=False):
    """Formatta l'ora in formato HH:MM"""
    try:
        if full:  # Per timestamp completi (YYYY-MM-DD HH:MM)
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M').strftime('%H:%M')
        else:     # Per ore in formato 12h (03:45 PM)
            return datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M')
    except ValueError:
        return time_str  # Fallback se il formato non è riconosciuto

def generate_rss_response(title, description):
    """Genera una risposta RSS standardizzata"""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "description").text = description
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?>\n{ET.tostring(rss, encoding="unicode", method="xml")}',
        mimetype="application/xml"
    )

# ==============================================
# API ENDPOINTS
# ==============================================

@app.route('/weather_rss')
@handle_errors
def weather_rss():
    """
    Endpoint RSS per applicazioni esterne
    Formato: /weather_rss?lat=XX.X&lon=YY.Y
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return generate_rss_response('❓ Attiva la geolocalizzazione', 'Posizione non disponibile')

    try:
        current_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}&lang=it"
        current_data = requests.get(current_url, timeout=3).json()
        
        condition_en = current_data['current']['condition']['text']
        condition_it = translate_condition(condition_en)
        temp_c = round(current_data['current']['temp_c'])
        return generate_rss_response(
            f"{get_emoji(condition_en)} {temp_c}°C {condition_it[:20]}",
            f"{current_data['location']['name']}, {current_data['location']['country']}"
        )
    except Exception:
        return generate_rss_response('❓ Errore meteo', 'Dati non disponibili')

@app.route('/weather_forecast')
@handle_errors
def weather_forecast():
    """
    Endpoint JSON per l'applicazione web
    Formato: /weather_forecast?lat=XX.X&lon=YY.Y
    """
    lat = request.args.get('lat', type=float) or DEFAULT_LOCATION['lat']
    lon = request.args.get('lon', type=float) or DEFAULT_LOCATION['lon']
    
    forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=7&aqi=no&alerts=no&lang=it"
    forecast_data = requests.get(forecast_url, timeout=API_TIMEOUT).json()

    location = forecast_data['location']
    processed_data = {
        'city': location['name'],
        'region': location.get('region', ''),
        'country': location['country'],
        'forecast': []
    }

    for day in forecast_data['forecast']['forecastday']:
        processed_day = {
            'date': day['date'],
            'temp_min': round(day['day']['mintemp_c'], 1),
            'temp_max': round(day['day']['maxtemp_c'], 1),
            'condition': day['day']['condition']['text'],
            'icon': day['day']['condition']['icon'],
            'sunrise': format_time(day['astro']['sunrise']),
            'sunset': format_time(day['astro']['sunset']),
            'humidity': day['day']['avghumidity'],
            'wind': round(day['day']['maxwind_kph']),
            'hourly': []
        }

        for hour in day['hour']:
            processed_day['hourly'].append({
                'time': format_time(hour['time'], full=True),
                'temp': round(hour['temp_c'], 1),
                'precip': round(hour['precip_mm'], 1),
                'condition': hour['condition']['text'],
                'icon': hour['condition']['icon']
            })

        processed_data['forecast'].append(processed_day)

    return jsonify(processed_data)

# ==============================================
# MAIN ROUTE
# ==============================================

@app.route('/')
def homepage():
    """Pagina principale dell'applicazione"""
    return render_template('index.html')

# ==============================================
# AVVIO APPLICAZIONE
# ==============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )
