<!DOCTYPE html>
<html lang="it">
<head>
    <!-- Testa rimane identica -->
</head>
<body>
    <!-- Header rimane identico -->

    <script>
        // ... (funzioni esistenti rimangono identiche) ...

        // Nuova funzione per ottenere la posizione
        function getLocation() {
            return new Promise((resolve, reject) => {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        position => resolve({
                            lat: position.coords.latitude,
                            lon: position.coords.longitude
                        }),
                        error => {
                            console.error("Errore geolocalizzazione:", error);
                            // Default: Roma
                            resolve({ lat: 41.9028, lon: 12.4964 });
                        }
                    );
                } else {
                    console.warn("Geolocalizzazione non supportata");
                    resolve({ lat: 41.9028, lon: 12.4964 });
                }
            });
        }

        // Funzione aggiornata per ottenere i dati meteo
        async function getWeatherData() {
            try {
                const { lat, lon } = await getLocation();
                const response = await fetch(`/weather_forecast?lat=${lat}&lon=${lon}`);
                
                if (!response.ok) throw new Error(await response.text());
                const data = await response.json();
                
                if (data.error) throw new Error(data.error);
                
                updateLocationInfo(data);
                createWeeklySummary(data.forecast);
                createDailyForecast(data.forecast);
            } catch (error) {
                console.error("Errore:", error);
                showError(error.message);
            }
        }

        function updateLocationInfo(data) {
            let locationText = data.city;
            if (data.region && data.region !== data.city) {
                locationText += `, ${data.region}`;
            }
            locationText += `, ${data.country}`;
            document.getElementById('location').textContent = locationText;
        }

        function showError(message) {
            document.getElementById("forecast-container").innerHTML = `
                <div class="card">
                    <p>Errore: ${message}</p>
                    <button onclick="getWeatherData()">Riprova</button>
                </div>
            `;
        }

        // Avvia il caricamento
        getWeatherData();
    </script>
</body>
</html>
