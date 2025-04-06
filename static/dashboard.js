document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.getElementById("logout");
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            alert("Logging out...");
            localStorage.removeItem("currentUser");
            window.location.href = "index.html"; // Redirect to login page
        });
    }
});

// Toggle Disease Identification Box
function toggleDiseaseBox() {
    var box = document.getElementById("disease-box");
    box.classList.toggle("hidden");
}



// Function to fetch user's location and get weather
document.addEventListener("DOMContentLoaded", () => {
    fetchWeather();
});

function fetchWeather() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                // Fetch weather data
                fetch(`https://wttr.in/${lat},${lon}?format=%C+%t`)
                    .then((response) => response.text())
                    .then((data) => {
                        document.getElementById("weather-info").innerHTML = `🌤️ ${data}`;
                    })
                    .catch(() => {
                        document.getElementById("weather-info").innerHTML = "🌦 Weather unavailable";
                    });

                // Fetch place name using Nominatim reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
                    .then((response) => response.json())
                    .then((data) => {
                        if (data && data.address) {
                            const place = data.display_name || "Unknown location";
                            document.getElementById("location-info").textContent = `Place: ${place}`;
                        } else {
                            document.getElementById("location-info").textContent = "Place not found.";
                        }
                    })
                    .catch(() => {
                        document.getElementById("location-info").textContent = "Failed to fetch place.";
                    });
            },
            () => {
                document.getElementById("weather-info").innerHTML = "🌦 Location access denied";
                document.getElementById("location-info").textContent = "Location access denied.";
            }
        );
    } else {
        document.getElementById("weather-info").innerHTML = "🌦 Geolocation not supported";
        document.getElementById("location-info").textContent = "Geolocation not supported.";
    }
}


// Fetch weather on page load
document.addEventListener("DOMContentLoaded", function () {
    fetchWeather();
});



// Handle Disease Identification form submission
function submitDiseaseForm() {
    const plantSelect = document.getElementById("plant-select");
    const imageUpload = document.getElementById("image-upload").files[0];
    const resultElement = document.getElementById("disease-result");

    if (!plantSelect.value) {
        alert("Please select a crop.");
        return;
    }

    if (!imageUpload) {
        alert("Please upload an image.");
        return;
    }

    const currentUser = JSON.parse(localStorage.getItem("currentUser"));
    if (!currentUser) {
        alert("You must be logged in to submit a post.");
        return;
    }

    const formData = new FormData();
    formData.append("crop", plantSelect.value);
    formData.append("image", imageUpload);

    fetch("http://127.0.0.1:5000/predict", { // Change this to your Flask backend URL
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultElement.innerHTML = `<span style="color: red;">Error: ${data.error}</span>`;
        } else {
            resultElement.innerHTML = `<strong>Prediction:</strong> ${data.prediction}`;

            // Submit the post to the backend
            const postFormData = new FormData();
            postFormData.append("image", imageUpload);
            postFormData.append("prediction", data.prediction);
            postFormData.append("user_id", currentUser.id);

            fetch("http://127.0.0.1:5000/submit_post", {
                method: "POST",
                body: postFormData
            })
            .then(postResponse => postResponse.json())
            .then(postData => {
                if (postData.error) {
                    alert(`Error submitting post: ${postData.error}`);
                } else {
                    alert("Post submitted successfully!");
                }
            })
            .catch(error => {
                console.error("Error submitting post:", error);
                alert("Failed to submit post.");
            });
        }
    })
    .catch(error => {
        resultElement.innerHTML = `<span style="color: red;">Failed to get prediction.</span>`;
        console.error("Error:", error);
    });
}
