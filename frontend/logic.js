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

// Handle form submission
document.getElementById("flightForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const source = document.getElementById("source").value;
  const destination = document.getElementById("destination").value;
  const preference = document.querySelector('input[name="preference"]:checked').value;

  try {
    const response = await fetch("/shortest-path", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        source,
        destination,
        filter: preference
      })
    });

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
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("output").innerText = "Failed to fetch route. Please try again.";
  }
});