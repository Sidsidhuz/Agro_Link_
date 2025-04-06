document.addEventListener('DOMContentLoaded', function () {
    // Retrieve the current user from localStorage
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));

    // Update the username in the header
    const usernameElement = document.getElementById('logged-in-username');
    usernameElement.textContent = currentUser && currentUser.username ? currentUser.username : 'Guest';

    // Add event listener to the search form
    const searchForm = document.getElementById('search-form');
    const searchQueryInput = document.getElementById('search-query');
    const searchResultsContainer = document.getElementById('search-results');

    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent page refresh
            const query = searchQueryInput.value.trim(); // Get the user's search query

            if (query) {
                searchUsers(query); // Call the searchUsers function with the query value
            } else {
                alert('Please enter a username to search.');
            }
        });
    }

    // Clear session data on logout
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            localStorage.removeItem('currentUser'); // Only remove the currentUser key
            window.location.href = 'index.html'; // Redirect to the login page
        });
    }

    // Function to fetch user details
    async function searchUsers(query) {
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: query })
            });

            const data = await response.json();
            console.log('Search response:', data); // Debug log

            if (!response.ok) {
                alert(data.error || 'No users found with the given username.');
                return;
            }

            // Display the list of recommended usernames
            searchResultsContainer.innerHTML = ''; // Clear previous results
            data.users.forEach(user => {
                const userElement = document.createElement('div');
                userElement.textContent = user.username;
                userElement.classList.add('search-result');
                userElement.addEventListener('click', function () {
                    const loggedInUserId = currentUser.id; // Retrieve the logged-in user's ID
                    window.location.href = `/view_profile.html?user_id=${loggedInUserId}&profile_user_id=${user.id}`; // Redirect to the profile page
                });
                searchResultsContainer.appendChild(userElement);
            });
        } catch (error) {
            console.error('Error fetching search results:', error);
            alert('An error occurred while fetching search results.');
        }
    }

    // Add event listener for input changes
    searchQueryInput.addEventListener('input', function () {
        const query = searchQueryInput.value.trim();
        if (query.length > 0) {
            fetchSearchResults(query); // Fetch results dynamically
        } else {
            searchResultsContainer.innerHTML = ''; // Clear results if input is empty
        }
    });

    // Function to fetch and display search results
    async function fetchSearchResults(query) {
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: query })
            });

            const data = await response.json();

            if (!response.ok) {
                searchResultsContainer.innerHTML = '<p>No users found.</p>';
                return;
            }

            // Clear previous results
            searchResultsContainer.innerHTML = '';

            // Display the list of recommended usernames
            data.users.forEach(user => {
                const userElement = document.createElement('div');
                userElement.classList.add('search-result');
                userElement.innerHTML = `
                    <img src="${user.profile_picture || 'default-profile.png'}" alt="Profile Picture">
                    <span>${user.username}</span>
                `;
                userElement.addEventListener('click', function () {
                    const loggedInUserId = currentUser.id; // Retrieve the logged-in user's ID
                    window.location.href = `/view_profile.html?user_id=${loggedInUserId}&profile_user_id=${user.id}`; // Redirect to the profile page
                });
                searchResultsContainer.appendChild(userElement);
            });
        } catch (error) {
            console.error('Error fetching search results:', error);
            searchResultsContainer.innerHTML = '<p>An error occurred while fetching search results.</p>';
        }
    }

    // Fetch all posts and display them
    fetch('/all_posts')
        .then(response => response.json())
        .then(data => {
            console.log('Posts data:', data); // Debugging: Check what the server is returning
            const postsContainer = document.getElementById('posts-container');

            if (!postsContainer) {
                console.error('Error: posts-container not found');
                return;
            }

            if (!data.posts || data.posts.length === 0) {
                postsContainer.innerHTML = '<p>No posts available.</p>';
                return;
            }

            data.posts.forEach(post => {
                const postElement = document.createElement('div');
                postElement.innerHTML = `
                    <p><strong>Username:</strong> ${post.username}</p>
                    <img src="${post.image_path}" alt="Post Image" style="width: 100px; height: 100px;" onerror="this.src='fallback.jpg';">
                    <p><strong>Prediction:</strong> ${post.prediction}</p>
                    <p><strong>Timestamp:</strong> ${post.timestamp}</p>
                `;
                postsContainer.appendChild(postElement);
            });
        })
        .catch(error => {
            console.error('Error fetching posts:', error);
        });

    // Predict crop and display results
    const predictButton = document.getElementById('predict-button');
    const fileInput = document.getElementById('file-input');

    if (predictButton && fileInput) {
        predictButton.addEventListener('click', function () {
            const file = fileInput.files[0];
            if (!file) {
                alert('Please upload a file to predict.');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            fetch('/predict', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        const resultContainer = document.getElementById('result-container');
                        resultContainer.innerHTML = `
                            <p><strong>Crop:</strong> ${data.crop}</p>
                            <p><strong>Prediction:</strong> ${data.prediction}</p>
                            <img src="${data.image_path}" alt="Uploaded Image" style="width: 150px; height: 150px;">
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    }
});