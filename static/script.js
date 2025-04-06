document.addEventListener('DOMContentLoaded', function () {
    loadCountries();
    document.getElementById("register-country").addEventListener("change", loadStates);

    if (document.getElementById("register-form")) {
        document.getElementById("register-form").addEventListener("submit", function (event) {
            event.preventDefault();
            register();
        });
    }

    if (document.getElementById("login-form")) {
        document.getElementById("login-form").addEventListener("submit", function (event) {
            event.preventDefault();
            login();
        });
    }
});

async function register() {
    const username = document.getElementById("register-username").value.trim();
    const phone = document.getElementById("register-phone").value.trim();
    const password = document.getElementById("register-password").value;
    const country = document.getElementById("register-country").value;
    const state = document.getElementById("register-state").value;
    const place = document.getElementById("register-place").value;
    const plants = Array.from(document.querySelectorAll('#dropdown-menu input:checked')).map(input => input.value);

    if (!username || !phone || !password || !country || !state || !place) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, phone, password, country, state, place, plants })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Registration failed. Please try again.");
            return;
        }

        alert("Registration successful! You can now log in.");
        toggleForm(); // Switch to login form
    } catch (error) {
        console.error("Error during registration:", error);
        alert("An error occurred. Please try again later.");
    }
}

async function login() {
    const phone = document.getElementById("login-phone").value.trim();
    const password = document.getElementById("login-password").value;

    if (!phone || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Login failed. Please try again.");
            return;
        }

        alert(`Login successful! Welcome, ${data.user.username}`);
        localStorage.setItem("currentUser", JSON.stringify(data.user)); // Store current user for session
        window.location.href = "home.html"; // Redirect to dashboard
    } catch (error) {
        console.error("Error during login:", error);
        alert("An error occurred. Please try again later.");
    }
}

function toggleForm() {
    const loginBox = document.getElementById("login-box");
    const registerBox = document.getElementById("register-box");

    if (loginBox.style.display === "none") {
        loginBox.style.display = "block";
        registerBox.style.display = "none";
    } else {
        loginBox.style.display = "none";
        registerBox.style.display = "block";
    }
}

function loadCountries() {
    const countries = ["India", "USA", "UK"];
    const countrySelect = document.getElementById("register-country");
    countries.forEach(country => {
        let option = new Option(country, country);
        countrySelect.appendChild(option);
    });
}

function loadStates() {
    const statesByCountry = {
        "India": [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
            "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
            "Uttarakhand", "West Bengal"
        ],
        "USA": ["California", "Texas", "New York"],
        "UK": ["London", "Manchester", "Liverpool"]
    };

    const country = document.getElementById("register-country").value;
    const stateSelect = document.getElementById("register-state");
    stateSelect.innerHTML = '<option value="">Select State</option>';

    if (statesByCountry[country]) {
        statesByCountry[country].forEach(state => {
            let option = new Option(state, state);
            stateSelect.appendChild(option);
        });
    }
}