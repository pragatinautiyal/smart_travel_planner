const themeToggle = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("theme");

// Set initial theme
if (savedTheme === 'dark') {
  document.documentElement.setAttribute('data-theme', 'dark');
  themeToggle.checked = true;
} else {
  document.documentElement.setAttribute('data-theme', 'light');
  themeToggle.checked = false;
}

// Toggle theme on switch change
themeToggle.addEventListener('change', toggleTheme);

function toggleTheme() {
  if (themeToggle.checked) {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem("theme", "dark");
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem("theme", "light");
  }
}
const today = new Date();
const year = today.getFullYear();
const month = ("0" + (today.getMonth() + 1)).slice(-2); // Format month as 2 digits
const day = ("0" + today.getDate()).slice(-2); // Format day as 2 digits
const formattedDate = `${year}-${month}-${day}`;
document.getElementById('date').setAttribute('min', formattedDate);

let map, mapInitialized = false;

document.getElementById("flightForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const source = document.getElementById("source").value;
  const destination = document.getElementById("destination").value;
  const preference = document.querySelector('input[name="preference"]:checked').value;

  try {
    const response = await fetch("/shortest-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, destination, filter: preference })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Server error: ${response.status} - ${errText}`);
    }

    const result = await response.json();

    if (result.error) {
      document.getElementById("output").innerText = result.error;
      return;
    }

    document.getElementById("output").innerHTML = `
      <h3>Optimal Route: ${result.path.join(" → ")}</h3>
      <p>Duration: ${result.duration_minutes} minutes</p>
      ${result.stops !== undefined 
        ? `<p>Stops: ${result.stops}</p>` 
        : `<p>Total Cost: ₹${result.total_cost}</p>`}
    `;

    document.getElementById("map").style.display = "block";
    displayFlightMap(result.flights);

  } catch (error) {
    console.error("Error fetching route:", error);
    document.getElementById("output").innerText = "Failed to fetch route. Please try again.";
  }
});

function displayFlightMap(flights) {
  if (!mapInitialized) {
    map = L.map('map').setView([22.5937, 78.9629], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    mapInitialized = true;
  } else {
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Polyline) {
        map.removeLayer(layer);
      }
    });
  }

  const routeCoords = [];
  const visited = new Set();

  flights.forEach(flight => {
    const fromKey = flight.from + JSON.stringify(flight.from_coords);
    const toKey = flight.to + JSON.stringify(flight.to_coords);

    if (!visited.has(fromKey)) {
      L.marker(flight.from_coords).addTo(map).bindPopup(flight.from_airport);
      visited.add(fromKey);
    }

    if (!visited.has(toKey)) {
      L.marker(flight.to_coords).addTo(map).bindPopup(flight.to_airport);
      visited.add(toKey);
    }

    routeCoords.push(flight.from_coords);
    routeCoords.push(flight.to_coords);
  });

  // Remove duplicate consecutive coords
  const uniqueRoute = routeCoords.filter((coord, index, arr) => {
    return index === 0 || JSON.stringify(coord) !== JSON.stringify(arr[index - 1]);
  });

  const routeLine = L.polyline(uniqueRoute, {
    color: 'red',
    weight: 4,
    opacity: 0.9,
    dashArray: '10,10'
  }).addTo(map);

  map.fitBounds(routeLine.getBounds());
}
