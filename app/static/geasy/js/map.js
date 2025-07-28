        document.addEventListener('DOMContentLoaded', function() {
            // Initialize map with default view (Mumbai)
            const map = L.map('map').setView([19.0760, 72.8777], 12);

            // Base map layers
            const streetMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            });

            const satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                maxZoom: 19
            });

            // Add default layer
            streetMap.addTo(map);

            // Add layer control
            const baseLayers = {
                "Street Map": streetMap,
                "Satellite View": satelliteMap
            };
            L.control.layers(baseLayers, null, {position: 'topright'}).addTo(map);

            // Check for user data
            const userDataElement = document.getElementById('user-data');
            if (userDataElement) {
                const userData = JSON.parse(userDataElement.dataset.user);
                const userLocation = [userData.lat, userData.lng];

                // Custom blue marker icon
                const blueIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34]
                });

                // Add marker to map
                const marker = L.marker(userLocation, {
                    icon: blueIcon,
                    title: userData.name
                }).addTo(map);

                // Add popup with user info
                marker.bindPopup(`
                    <div style="min-width: 200px">
                        <h5 style="margin-bottom: 5px">${userData.name}</h5>
                        <p><strong>ID:</strong> ${userData.emp_id}</p>
                        <p><strong>Time:</strong> ${userData.timestamp}</p>
                        <p><strong>Device:</strong> ${userData.device}</p>
                    </div>
                `).openPopup();

                // Center map on marker
                map.setView(userLocation, 15);
            }

            // Form validation
            const forms = document.querySelectorAll('.needs-validation');
            Array.from(forms).forEach(form => {
                form.addEventListener('submit', event => {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                }, false);
            });
        });
    