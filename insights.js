document.addEventListener('DOMContentLoaded', () => {
      let hotspotMap;
      let opportunityRiskMatrix;

      const initHotspotMap = () => {
        const mapElement = document.getElementById('hotspotMap');
        if (!mapElement || hotspotMap) return;

        hotspotMap = L.map(mapElement).setView([21.0285, 105.8542], 5); // Centered on Hanoi
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '© OpenStreetMap'
        }).addTo(hotspotMap);

        L.Control.geocoder({
            defaultMarkGeocode: false
        })
        .on('markgeocode', function(e) {
            var bbox = e.geocode.bbox;
            var poly = L.polygon([
                bbox.getSouthEast(),
                bbox.getNorthEast(),
                bbox.getNorthWest(),
                bbox.getSouthWest()
            ]).addTo(hotspotMap);
            hotspotMap.fitBounds(poly.getBounds());
        })
        .addTo(hotspotMap);

        var customControl = L.Control.extend({
            options: {
                position: 'topleft'
            },

            onAdd: function (map) {
                var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                container.style.backgroundColor = 'white';
                container.style.width = '34px';
                container.style.height = '34px';
                container.style.cursor = 'pointer';
                container.innerHTML = '<a style="font-size: 1.6em; color: #333; text-decoration: none; text-align: center; display: block; line-height: 34px;" href="#" title="Locate me">📍</a>';
                container.onclick = function(e){
                    e.preventDefault();
                    map.locate({setView: true, maxZoom: 16});
                }
                return container;
            }
        });
        hotspotMap.addControl(new customControl());

        hotspotMap.on('locationfound', function(e) {
            var radius = e.accuracy;
            L.marker(e.latlng).addTo(hotspotMap)
                .bindPopup("You are within " + radius + " meters from this point").openPopup();
            L.circle(e.latlng, radius).addTo(hotspotMap);
        });

        // Placeholder marker
        L.marker([21.0285, 105.8542]).addTo(hotspotMap)
          .bindPopup('A sample marker for Hanoi.')
          .openPopup();
      };

      const initOpportunityRiskMatrix = () => {
        const ctx = document.getElementById('opportunityRiskMatrix');
        if (!ctx || opportunityRiskMatrix) return;
        
        opportunityRiskMatrix = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: [{
              label: 'Market Signals',
              data: [
                {x: 20, y: 30, r: 15},
                {x: 40, y: 10, r: 10},
                {x: 35, y: 80, r: 25},
                {x: 60, y: 60, r: 20},
              ],
              backgroundColor: 'rgba(37, 99, 235, 0.6)'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                title: {
                  display: true,
                  text: 'Risk Score'
                }
              },
              y: {
                title: {
                  display: true,
                  text: 'Opportunity Score'
                }
              }
            }
          }
        });
      };
      
      const insightsBtn = document.getElementById('btn-insights');
      if (insightsBtn) {
        insightsBtn.addEventListener('click', () => {
            // Use a small timeout to ensure the view is visible before initializing
            setTimeout(() => {
                initHotspotMap();
                initOpportunityRiskMatrix();
            }, 10);
        });
      }
    });