document.addEventListener('DOMContentLoaded', function () {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));

    if (!currentUser) {
        window.location.href = 'index.html';
        return;
    }

    // Fetch user details from the backend
    fetch(`/get_user_profile/${currentUser.id}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                // Display user details
                document.getElementById('profile-username').textContent = data.username;
                document.getElementById('about-text').textContent = data.about || "Here’s who I am & what I do.";

                // Display profile picture
                const profilePictureElement = document.getElementById('profile-picture');
                if (data.profile_picture) {
                    profilePictureElement.src = data.profile_picture;
                } else {
                    profilePictureElement.src = 'default-profile.png'; // Fallback image
                }
            }
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
        });

    // Open Edit Profile Modal
    const editProfileButton = document.getElementById('edit-profile-button');
    editProfileButton.addEventListener('click', function () {
        new WinBox("Edit Profile", {
            width: "400px",
            height: "300px",
            top: 50,
            right: 50,
            bottom: 50,
            left: 50,
            html: "<p>Edit Profile Modal Content</p>",
        });
    });

    function createEditProfileForm(winbox) {
        const container = document.createElement('div');
        container.innerHTML = `
            <form id="edit-profile-form">
                <label for="new-profile-picture">Upload Profile Picture:</label>
                <input type="file" id="new-profile-picture" accept="image/*"><br><br>
                <label for="about-me">About Me:</label>
                <textarea id="about-me" placeholder="Write something about yourself..."></textarea><br><br>
                <button type="submit">Save Changes</button>
            </form>
        `;

        container.querySelector('#edit-profile-form').addEventListener('submit', function (event) {
            event.preventDefault();
            alert('Form submitted!');
            winbox.close();
        });

        return container;
    }

    // Handle profile picture upload
    const uploadInput = document.getElementById('upload-profile-picture');
    const profilePicture = document.getElementById('profile-picture');

    uploadInput.addEventListener('change', function () {
        const file = uploadInput.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('user_id', currentUser.id);

            fetch('/upload_profile_picture', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(`Error: ${data.error}`);
                    } else {
                        alert('Profile picture updated successfully!');
                        profilePicture.src = data.image_path; // Update the profile picture
                    }
                })
                .catch(error => {
                    console.error('Error uploading profile picture:', error);
                });
        }
    });

    // Handle editing the "About Me" section
    const editAboutButton = document.getElementById('edit-about-button');
    editAboutButton.addEventListener('click', function () {
        // Create a textarea for editing
        const aboutTextElement = document.getElementById('about-text');
        const currentAboutText = aboutTextElement.textContent;

        // Replace the "About Me" text with a textarea
        aboutTextElement.innerHTML = `
            <textarea id="about-edit-text" style="width: 100%; height: 100px;">${currentAboutText}</textarea>
            <button id="save-about-button" class="save-button">Save</button>
            <button id="cancel-about-button" class="cancel-button">Cancel</button>
        `;

        // Handle saving the updated "About Me" text
        document.getElementById('save-about-button').addEventListener('click', function () {
            const updatedAboutText = document.getElementById('about-edit-text').value;

            // Send the updated "About Me" text to the backend
            fetch('/edit_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: currentUser.id,
                    about: updatedAboutText,
                }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(`Error: ${data.error}`);
                    } else {
                        alert('About Me updated successfully!');
                        aboutTextElement.textContent = updatedAboutText; // Update the UI
                    }
                })
                .catch(error => {
                    console.error('Error updating About Me:', error);
                });
        });

        // Handle canceling the edit
        document.getElementById('cancel-about-button').addEventListener('click', function () {
            aboutTextElement.textContent = currentAboutText; // Restore the original text
        });
    });

    // Fetch user's prediction history
    fetch(`/user_posts/${currentUser.id}`)
        .then(response => response.json())
        .then(data => {
            const historyContainer = document.getElementById('history-container');
            if (!data.posts || data.posts.length === 0) {
                historyContainer.innerHTML = '<p>No prediction history available.</p>';
                return;
            }

            data.posts.forEach(post => {
                const postElement = document.createElement('div');
                postElement.innerHTML = `
                    <img src="${post.image_path}" alt="Post Image" style="width: 100px; height: 100px;">
                    <p><strong>Prediction:</strong> ${post.prediction}</p>
                    <p><strong>Date:</strong> ${post.timestamp}</p>
                `;
                historyContainer.appendChild(postElement);
            });
        })
        .catch(error => {
            console.error('Error fetching prediction history:', error);
        });

    // Handle Add Post Button Click
    const addPostButton = document.getElementById('add-post-button');
    addPostButton.addEventListener('click', function () {
        // Open a modal or form for adding a new post
        new WinBox("Add New Post", {
            width: "400px",
            height: "300px",
            top: 50,
            right: 50,
            bottom: 50,
            left: 50,
            html: `
                <form id="add-post-form">
                    <label for="post-image">Upload Image:</label>
                    <input type="file" id="post-image" accept="image/*" required><br><br>
                    <label for="post-caption">Caption:</label>
                    <textarea id="post-caption" placeholder="Enter a caption..." required></textarea><br><br>
                    <button type="submit">Add Post</button>
                </form>
            `,
        });

        // Handle the form submission
        document.getElementById('add-post-form').addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData();
            const imageInput = document.getElementById('post-image');
            const captionInput = document.getElementById('post-caption');

            if (!imageInput.files[0] || !captionInput.value) {
                alert('Please provide an image and a caption.');
                return;
            }

            formData.append('image', imageInput.files[0]);
            formData.append('caption', captionInput.value);
            formData.append('user_id', currentUser.id);

            fetch('/add_post', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(`Error: ${data.error}`);
                    } else {
                        alert('Post added successfully!');
                        window.location.reload(); // Reload the page to show the new post
                    }
                })
                .catch(error => {
                    console.error('Error adding post:', error);
                });
        });
    });

    // Logout functionality
    const logoutButton = document.getElementById('logout-button');
    logoutButton.addEventListener('click', function () {
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
    });
});