document.addEventListener("DOMContentLoaded", () => {
    const map = L.map("map").setView([47.818, 12.994], 13);

    const baseLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    const colors = ["#FF5733", "#33FF57", "#5733FF", "#FFC300", "#DAF7A6"];
    const layers = {};
    const ctx = document.getElementById("elevationChart").getContext("2d");

    const elevationChart = new Chart(ctx, {
        type: "line",
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { type: "linear", title: { display: true, text: "Distance (km)" } },
                y: { title: { display: true, text: "Elevation (m)" }, suggestedMin: 0, suggestedMax: 600 },
            },
        },
    });

    // Update chart logic
    function updateChart() {
        elevationChart.data.datasets = [];
        Object.keys(layers).forEach(route => {
            if (map.hasLayer(layers[route].layer)) {
                elevationChart.data.datasets.push({
                    label: route,
                    data: layers[route].elevationData,
                    borderColor: layers[route].color,
                    borderWidth: 0.5,
                    pointRadius: 1,
                });
            }
        });
        elevationChart.update();
    }

    function loadGeoJson(route, color) {
        fetch(`data/${route}/${route}.geojson`)
            .then(response => response.json())
            .then(data => {
                const elevationData = [];
                const coordinates = data.features.flatMap(f => f.geometry.coordinates);
                let totalDistance = 0;

                const geoJsonLayer = L.geoJSON(data, {
                    style: { color: color },
                    onEachFeature: (feature, layer) => {
                        if (feature.properties) {
                            layer.bindPopup(`Name: ${feature.properties.name || "Unknown"}`);
                        }
                    },
                }).addTo(map);

                coordinates.forEach(([lon, lat], i) => {
                    if (i > 0) {
                        const [prevLon, prevLat] = coordinates[i - 1];
                        totalDistance += haversine(prevLat, prevLon, lat, lon);
                    }
                    elevationData.push({
                        x: totalDistance.toFixed(2),
                        y: data.features[i]?.properties?.START_Elevation || null,
                    });
                });

                layers[route] = { layer: geoJsonLayer, elevationData, color };
                updateChart();
            })
            .catch(err => console.error("Error loading GeoJSON:", err));
    }

    function haversine(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const toRad = x => (x * Math.PI) / 180;
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    const layerSelect = document.getElementById("layers");
    layerSelect.addEventListener("change", e => {
        const selectedRoute = e.target.value;
        if (!layers[selectedRoute]) loadGeoJson(selectedRoute, colors[Math.floor(Math.random() * colors.length)]);
    });
});
