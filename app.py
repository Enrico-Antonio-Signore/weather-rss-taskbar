from flask import Flask, Response, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
WEATHER_API_KEY = "534016f5b5f34a0ca29102123252503"

def get_emoji(weather_condition):
    condition = weather_condition.lower()
    weather_icons = {
        'clear': '☀️', 'sunny': '☀️', 'cloud': '☁️', 'cloudy': '☁️',
        'rain': '🌧️', 'thunder': '⛈️', 'snow': '❄️', 'mist': '🌫️',
        'fog': '🌁', 'drizzle': '🌦️', 'shower': '🌧️', 'overcast': '☁️'
    }
    return weather_icons.get(condition.split()[0], '🌡️')

@app.route('/weather_rss')
def weather_rss():
    """Endpoint RSS esistente (mantenuto invariato)"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return Response('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><item><title>❓ Attiva la geolocalizzazione</title><description>Posizione non disponibile</description></item></channel></rss>', mimetype="application/xml")

        weather_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}"
        weather_data = requests.get(weather_url, timeout=3).json()

        temp = weather_data['current']['temp_c']
        condition = weather_data['current']['condition']['text']
        city = weather_data['location']['name']
        country = weather_data['location']['country']

    except Exception as e:
        print(f"Errore in /weather_rss: {str(e)}")
        return Response('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><item><title>❓ Errore meteo</title><description>Dati non disponibili</description></item></channel></rss>', mimetype="application/xml")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{get_emoji(condition)} {temp}°C {condition[:20]}"
    ET.SubElement(item, "description").text = f"{city}, {country}"

    xml_str = ET.tostring(rss, encoding='unicode', method='xml')
    return Response(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}', mimetype="application/xml")

@app.route('/weather_forecast')
def weather_forecast():
    """Endpoint migliorato per l'interfaccia web"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if not lat or not lon:
            return jsonify({'error': 'Coordinate mancanti'}), 400

        forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=7&aqi=no&alerts=no"
        response = requests.get(forecast_url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': 'Errore API meteo'}), 500

        forecast_data = response.json()
        location = forecast_data['location']

        daily_forecast = []
        for day in forecast_data['forecast']['forecastday']:
            hourly_data = []
            for hour in day['hour']:
                time_obj = datetime.strptime(hour['time'], '%Y-%m-%d %H:%M')
                hourly_data.append({
                    'time': time_obj.strftime('%H:%M'),
                    'temp': hour['temp_c'],
                    'precip': hour['precip_mm'],
                    'condition': hour['condition']['text'],
                    'icon': hour['condition']['icon']
                })
            
            sunrise_time = datetime.strptime(day['astro']['sunrise'], '%I:%M %p')
            sunset_time = datetime.strptime(day['astro']['sunset'], '%I:%M %p')
            
            daily_forecast.append({
                'date': day['date'],
                'temp_min': day['day']['mintemp_c'],
                'temp_max': day['day']['maxtemp_c'],
                'condition': day['day']['condition']['text'],
                'icon': day['day']['condition']['icon'],
                'sunrise': sunrise_time.strftime('%H:%M'),
                'sunset': sunset_time.strftime('%H:%M'),
                'humidity': day['day']['avghumidity'],
                'wind': round(day['day']['maxwind_kph']),
                'hourly': hourly_data
            })

        return jsonify({
            'city': location['name'],
            'region': location.get('region', ''),
            'country': location['country'],
            'forecast': daily_forecast
        })

    except Exception as e:
        print(f"Errore in /weather_forecast: {str(e)}")
        return jsonify({'error': 'Errore interno del server'}), 500

@app.route('/')
def homepage():
    """Pagina principale con geolocalizzazione client-side"""
    return render_template('weather.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
