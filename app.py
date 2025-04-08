from flask import Flask, Response, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__, template_folder='templates')
API_KEY = "c261fa04a85ef65367fee878d0313041"
DEFAULT_LOC = {'lat': 41.9028, 'lon': 12.4964}
TIMEOUT = 10

def gestisci_errori(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.Timeout:
            return jsonify({'errore': 'Servizio non disponibile'}), 504
        except Exception as e:
            return jsonify({'errore': 'Errore interno'}), 500
    return wrapper

emoji_meteo = {
    200: '⛈️', 201: '⛈️', 202: '⛈️', 210: '🌩️', 211: '🌩️', 
    212: '🌩️', 221: '🌩️', 230: '⛈️', 231: '⛈️', 232: '⛈️',
    300: '🌧️', 301: '🌧️', 302: '🌧️', 310: '🌧️', 311: '🌧️',
    312: '🌧️', 313: '🌧️', 314: '🌧️', 321: '🌧️',
    500: '🌦️', 501: '🌧️', 502: '🌧️', 503: '🌧️', 504: '🌧️',
    511: '🌨️', 520: '🌧️', 521: '🌧️', 522: '🌧️', 531: '🌧️',
    600: '❄️', 601: '❄️', 602: '❄️', 611: '🌨️', 612: '🌨️',
    613: '🌨️', 615: '🌨️', 616: '🌨️', 620: '🌨️', 621: '🌨️', 622: '🌨️',
    701: '🌫️', 711: '🌫️', 721: '🌫️', 731: '🌫️', 741: '🌁',
    751: '🌫️', 761: '🌫️', 762: '🌫️', 771: '🌫️', 781: '🌪️',
    800: '☀️', 801: '⛅', 802: '⛅', 803: '☁️', 804: '☁️'
}

def crea_rss(titolo, descrizione):
    rss = ET.Element("rss", version="2.0")
    canale = ET.SubElement(rss, "channel")
    item = ET.SubElement(canale, "item")
    ET.SubElement(item, "title").text = titolo
    ET.SubElement(item, "description").text = descrizione
    return Response(f'<?xml version="1.0"?>\n{ET.tostring(rss, encoding="unicode")}', mimetype="application/xml")

@app.route('/weather_rss')
@gestisci_errori
def meteo_rss():
    lat, lon = request.args.get('lat'), request.args.get('lon')
    if not lat or not lon:
        return crea_rss('❓ Attiva geolocalizzazione', 'Posizione non disponibile')

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=it"
        dati = requests.get(url, timeout=3).json()
        meteo = dati['weather'][0]
        return crea_rss(
            f"{emoji_meteo.get(meteo['id'], '🌡️')} {round(dati['main']['temp'])}°C {meteo['description']}",
            f"{dati.get('name', '')}, {dati.get('sys', {}).get('country', '')}"
        )
    except:
        return crea_rss('❓ Errore meteo', 'Dati non disponibili')

@app.route('/weather_forecast')
@gestisci_errori
def previsioni():
    lat = request.args.get('lat', type=float) or DEFAULT_LOC['lat']
    lon = request.args.get('lon', type=float) or DEFAULT_LOC['lon']
    
    try:
        url_corrente = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=it"
        url_previsioni = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=it"
        corrente, previsioni = requests.get(url_corrente, timeout=TIMEOUT).json(), requests.get(url_previsioni, timeout=TIMEOUT).json()

        giorni = {}
        for ora in previsioni['list']:
            data = datetime.fromtimestamp(ora['dt']).strftime('%Y-%m-%d')
            if data not in giorni:
                giorni[data] = {'ore': [], 'min': ora['main']['temp_min'], 'max': ora['main']['temp_max']}
            
            giorni[data]['ore'].append(ora)
            giorni[data]['min'] = min(giorni[data]['min'], ora['main']['temp_min'])
            giorni[data]['max'] = max(giorni[data]['max'], ora['main']['temp_max'])

        risultato = {
            'city': corrente.get('name', ''),
            'country': corrente.get('sys', {}).get('country', ''),
            'forecast': [{
                'date': data,
                'temp_min': round(giorno['min']),
                'temp_max': round(giorno['max']),
                'condition': giorno['ore'][0]['weather'][0]['description'],
                'icon': f"http://openweathermap.org/img/wn/{giorno['ore'][0]['weather'][0]['icon']}@2x.png",
                'hourly': [{
                    'time': datetime.fromtimestamp(ora['dt']).strftime('%H:%M'),
                    'temp': round(ora['main']['temp']),
                    'precip': ora.get('rain', {}).get('3h', 0) or ora.get('snow', {}).get('3h', 0),
                    'condition': ora['weather'][0]['description'],
                    'icon': f"http://openweathermap.org/img/wn/{ora['weather'][0]['icon']}.png"
                } for ora in giorno['ore'][:8]]
            } for data, giorno in giorni.items()]
        }
        return jsonify(risultato)
    except Exception as e:
        return jsonify({'errore': str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=os.environ.get('DEBUG') == 'True')
