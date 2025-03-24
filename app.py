# ... (resto delle importazioni e configurazioni)

@app.route('/weather_rss')
def weather_rss():
    try:
        # ... (codice esistente per geolocalizzazione)

        # 2. DATI METEO CON ARROTONDAMENTO A 0.5
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=3).json()

        # Arrotondamento a scalini di 0.5 gradi
        temp_raw = weather_data['main']['temp']
        temp = round(temp_raw * 2) / 2  
        
        # Forza la visualizzazione con .0 o .5
        temp_str = f"{int(temp)}°C" if temp.is_integer() else f"{temp}°C"
        
        condition = weather_data['weather'][0]['description'].capitalize()
        icon = get_emoji(weather_data['weather'][0]['main'])

    except Exception as e:
        temp_str = "N/D"
        # ... (resto del fallback)

    # Generazione RSS
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp_str} | {condition[:20]}"
    # ... (resto del codice)
