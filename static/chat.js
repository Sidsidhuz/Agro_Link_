const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const userList = document.getElementById('user-list');

const user1Id = 1; // Replace with the logged-in user's ID
let selectedUserId = null;

function fetchUsers() {
    fetch(`/get_chat_users/${user1Id}`)
        .then(response => response.json())
        .then(data => {
            userList.innerHTML = '';
            data.users.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.classList.add('user');
                userDiv.textContent = user.username;
                userDiv.addEventListener('click', () => {
                    selectedUserId = user.id;
                    userList.querySelectorAll('.user').forEach(u => u.classList.remove('active'));
                    userDiv.classList.add('active');
                    fetchMessages();
                });
                userList.appendChild(userDiv);
            });
        })
        .catch(err => console.error('Error fetching users:', err));
}

function fetchMessages() {
    if (!selectedUserId) return;

    fetch(`/get_messages/${user1Id}/${selectedUserId}`)
        .then(response => response.json())
        .then(data => {
            chatMessages.innerHTML = '';
            data.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(msg.sender_id === user1Id ? 'sent' : 'received');
                messageDiv.innerHTML = `
                    <div class="message-bubble">
                        <p><strong>${msg.sender_id === user1Id ? 'You' : msg.sender_name}</strong></p>
                        <p>${msg.text}</p>
                        <span class="timestamp">${new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                `;
                chatMessages.appendChild(messageDiv);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(err => console.error('Error fetching messages:', err));
}

sendButton.addEventListener('click', () => {
    const text = messageInput.value.trim();
    if (!text || !selectedUserId) return;

    fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender_id: user1Id, receiver_id: selectedUserId, text })
    })
        .then(response => response.json())
        .then(() => {
            messageInput.value = '';
            fetchMessages();
        })
        .catch(err => console.error('Error sending message:', err));
});

// Fetch users on page load
fetchUsers();