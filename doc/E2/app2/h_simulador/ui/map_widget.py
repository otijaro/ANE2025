from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Crear el layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Crear el WebEngineView (para cargar el mapa)
        self.browser = QWebEngineView(self)
        layout.addWidget(self.browser)

        # Cargar el mapa con la API de Google Maps
        self.load_map()

    def load_map(self):
        # Google Maps API Key (reemplaza con tu clave API)
        api_key = "YOUR_GOOGLE_MAPS_API_KEY"
        
        # HTML básico para mostrar Google Maps con JavaScript
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google Maps</title>
            <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" 
                    async defer></script>
            <style>
                #map {{
                    height: 100%;
                    width: 100%;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                let map;
                function initMap() {{
                    // Configuración inicial del mapa (centro y zoom)
                    map = new google.maps.Map(document.getElementById("map"), {{
                        center: {{lat: 19.432608, lng: -99.133209}},  // Centro de Ciudad de México (cambiar según necesites)
                        zoom: 12
                    }});
                }}
            </script>
        </body>
        </html>
        """

        # Cargar el HTML en el widget de navegador
        self.browser.setHtml(map_html)

    def update_map(self, lat: float, lon: float):
        """Método para actualizar la posición del mapa según coordenadas (lat, lon)."""
        script = f"""
        var position = new google.maps.LatLng({lat}, {lon});
        map.setCenter(position);
        var marker = new google.maps.Marker({{
            position: position,
            map: map,
            title: 'Nueva ubicación'
        }});
        """
        self.browser.page().runJavaScript(script)
