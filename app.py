from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import os
import requests
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
import sqlite3
import uuid  # Import for generating unique IDs




app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)
app.secret_key = 'your_secret_key'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

def init_db():
    db_path = 'database.db'  # Define database path
    try:
        if not os.path.exists(db_path):  # Check if the database file already exists
            print("Initializing database...")  # Debug log
        else:
            print("Database file already exists. Validating tables...")  # Debug log

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Ensure 'users' table exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL,
                                phone TEXT NOT NULL UNIQUE,
                                password TEXT NOT NULL,
                                plants TEXT,
                                country TEXT,
                                state TEXT,
                                place TEXT,
                                profile_picture TEXT,
                                about TEXT)''')  # Added about column
            print("Verified 'users' table.")  # Debug log

            # Ensure 'posts' table exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                image_path TEXT NOT NULL,
                                prediction TEXT NOT NULL,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users (id))''')
            print("Verified 'posts' table.")  # Debug log

            # Ensure 'messages' table exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                sender_id INTEGER NOT NULL,
                                receiver_id INTEGER NOT NULL,
                                text TEXT NOT NULL,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (sender_id) REFERENCES users (id),
                                FOREIGN KEY (receiver_id) REFERENCES users (id))''')
            print("Verified 'messages' table.")  # Debug log

            # Add missing columns if they don't exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'profile_picture' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
                print("Added 'profile_picture' column to 'users' table.")  # Debug log
            if 'about' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN about TEXT")
                print("Added 'about' column to 'users' table.")  # Debug log

            conn.commit()
        print("Database initialized and tables verified successfully.")  # Debug log

    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")  # Log error for debugging

@app.before_request
def ensure_db_initialized():
    try:
        conn = get_db_connection()
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error detected: {e}. Reinitializing database...")
        init_db()

@app.before_request
def ensure_db_initialized():
    try:
        conn = get_db_connection()
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error detected: {e}. Reinitializing database...")
        init_db()



def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

class CNN_Model(nn.Module):
    def __init__(self, num_classes=4):
        super(CNN_Model, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(128 * 18 * 18, 256)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = self.pool(torch.relu(self.conv3(x)))
        x = self.flatten(x)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

MODEL_PATHS = {
    "Corn": "Corn_disease.pth",
    "Banana": "Banana_disease.pth",
    "Grapes": "Grapes_disease.pth"
}

CLASS_LABELS = {
    "Corn": ["Corn___Common_Rust", "Corn___Gray_Leaf_Spot", "Corn___Healthy", "Corn___Northern_Leaf_Blight"],
    "Banana": ["cordana", "Banana_Healthy", "pestalotiopsis", "sigatoka"],
    "Grapes": ["Black_Root", "Grapes_Esca", "Leaf_Blight", "Grapes_Healthy"]
}

transform = transforms.Compose([
    transforms.Resize((150, 150)),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

def get_weather(location):
    try:
        url = f"https://wttr.in/{location}?format=%C+%t"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and "+" in response.text:
            return response.text.strip()
        return "Weather data unavailable"
    except requests.RequestException:
        return "Weather service error"

def save_image(image, folder='static', prefix='z'):
    """
    Save an image with a unique filename using uuid and return the filename.
    """
    os.makedirs(folder, exist_ok=True)  # Ensure the folder exists
    unique_id = uuid.uuid4().hex  # Generate a unique identifier
    image_filename = f"{prefix}_{unique_id}_{secure_filename(image.filename)}"
    image_path = os.path.join(folder, image_filename)
    image.save(image_path)
    return image_filename

loaded_models = {}
for crop, path in MODEL_PATHS.items():
    if os.path.exists(path):
        model = CNN_Model(num_classes=len(CLASS_LABELS[crop]))
        model.load_state_dict(torch.load(path, map_location=torch.device("cpu")))
        model.eval()
        loaded_models[crop] = model

@app.route('/')
def serve_home():
    return send_from_directory("static", "index.html")

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Store the password as plain text (not recommended for production)
            cursor.execute("INSERT INTO users (username, phone, password, plants, country, state, place) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (data["username"], data["phone"], data["password"], ','.join(data.get("plants", [])), data["country"], data["state"], data["place"]))
            conn.commit()
            return jsonify({"message": "Registration successful"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Phone number already registered!"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, country, state, place FROM users WHERE phone=?",
                       (data["phone"],))
        user = cursor.fetchone()

    if user and user[2] == data["password"]:  # Direct comparison of plain text password
        user_data = {
            "id": user[0],
            "username": user[1],
            "phone": data["phone"],
            "country": user[3],
            "state": user[4],
            "place": user[5]
        }
        return jsonify({"message": "Login successful!", "user": user_data}), 200

    return jsonify({"error": "Invalid phone number or password"}), 400


@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files or 'crop' not in request.form:
        return jsonify({'error': 'Image or crop not provided'}), 400

    crop = request.form['crop']
    if crop not in loaded_models:
        return jsonify({'error': 'Invalid crop selection'}), 400

    image = request.files['image']

    try:
        # Save the image with a unique filename
        image_filename = save_image(image)

        # Load the image for prediction
        image_path = os.path.join('static', image_filename)
        image = Image.open(image_path).convert("RGB")
        image = transform(image).unsqueeze(0)

        # Perform prediction
        model = loaded_models[crop]
        with torch.no_grad():
            output = model(image)
            predicted_class = torch.argmax(output, dim=1).item()

        # Return the prediction result with the filename only
        return jsonify({'crop': crop, 'prediction': CLASS_LABELS[crop][predicted_class], 'image_path': image_filename})
    except Exception as e:
        return jsonify({'error': f'Failed to process image: {e}'}), 500

@app.route('/weather', methods=['POST'])
def get_weather_data():
    data = request.json
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT place FROM users WHERE phone=?", (data["phone"],))
        user = cursor.fetchone()
    if user:
        return jsonify({"location": user[0], "weather": get_weather(user[0])})
    return jsonify({"error": "User not found"}), 404


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    username_query = data.get('username')

    if not username_query:
        return jsonify({"error": "Username is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Use a wildcard search to find similar usernames
    cursor.execute(
        "SELECT id, username, profile_picture FROM users WHERE username LIKE ?",
        (f"%{username_query}%",)
    )
    users = cursor.fetchall()
    conn.close()

    if users:
        return jsonify({"users": [{"id": user[0], "username": user[1], "profile_picture": user[2]} for user in users]}), 200
    else:
        return jsonify({"error": "No users found"}), 404

@app.route('/submit_post', methods=['POST'])
def submit_post():
    if 'image' not in request.files or 'prediction' not in request.form or 'user_id' not in request.form:
        print("Missing required fields")  # Debug log
        return jsonify({'error': 'Missing required fields'}), 400

    image = request.files['image']
    prediction = request.form['prediction']
    user_id = request.form['user_id']

    print(f"Received post data: user_id={user_id}, prediction={prediction}, image={image.filename}")  # Debug log

    # Save the image to the static folder
    try:
        image_filename = save_image(image)
        print(f"Image saved with filename {image_filename}")  # Debug log

    except Exception as e:
        print(f"Error saving image: {e}")  # Debug log
        return jsonify({'error': 'Failed to save image'}), 500

    # Save the post to the database
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            print(f"Inserting into posts table: user_id={user_id}, image_path={image_filename}, prediction={prediction}")  # Debug log
            cursor.execute("INSERT INTO posts (user_id, image_path, prediction) VALUES (?, ?, ?)",
                           (user_id, image_filename, prediction))
            conn.commit()
            print("Post saved to database")  # Debug log
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")  # Debug log
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    except Exception as e:
        print(f"Error saving post to database: {e}")  # Debug log
        return jsonify({'error': 'Failed to save post to database'}), 500

    return jsonify({'message': 'Post submitted successfully!'}), 201

@app.route('/user_posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_path, prediction, timestamp FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        posts = cursor.fetchall()

    return jsonify({'posts': [{'image_path': post[0], 'prediction': post[1], 'timestamp': post[2]} for post in posts]}), 200

@app.route('/all_posts', methods=['GET'])
def get_all_posts():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT posts.image_path, posts.prediction, posts.timestamp, users.username
                          FROM posts
                          JOIN users ON posts.user_id = users.id
                          ORDER BY posts.timestamp DESC''')
        posts = cursor.fetchall()

    # Return the filename directly
    return jsonify({'posts': [{'image_path': post[0], 'prediction': post[1], 'timestamp': post[2], 'username': post[3]} for post in posts]}), 200

@app.route('/add_post', methods=['POST'])
def add_post():
    if 'image' not in request.files or 'caption' not in request.form or 'user_id' not in request.form:
        return jsonify({'error': 'Missing required fields'}), 400

    image = request.files['image']
    caption = request.form['caption']
    user_id = request.form['user_id']

    try:
        # Save the image with a unique filename
        image_filename = save_image(image)

        # Store only the filename in the database
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts (user_id, image_path, prediction) VALUES (?, ?, ?)",
                           (user_id, image_filename, caption))
            conn.commit()

        return jsonify({'message': 'Post added successfully!'}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to add post: {e}'}), 500

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'image' not in request.files or 'user_id' not in request.form:
        return jsonify({'error': 'Missing required fields'}), 400

    image = request.files['image']
    user_id = request.form['user_id']

    try:
        image_filename = save_image(image, prefix='z_profile')

        # Update the user's profile picture in the database
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET profile_picture = ? WHERE id = ?", (image_filename, user_id))
            conn.commit()

        return jsonify({'message': 'Profile picture updated successfully!', 'image_path': image_filename}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to upload profile picture: {e}'}), 500

@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'error': 'Missing user ID'}), 400

    user_id = data['user_id']
    about = data.get('about', None)

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            if about is not None:
                cursor.execute("UPDATE users SET about = ? WHERE id = ?", (about, user_id))
            conn.commit()

        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {e}'}), 500

@app.route('/get_user_profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, about, profile_picture FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

        if user:
            return jsonify({
                'username': user[0],
                'about': user[1],
                'profile_picture': user[2] or 'default-profile.png'
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return jsonify({'error': 'An error occurred while fetching the profile.'}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    text = data.get('text')

    if not sender_id or not receiver_id or not text:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (sender_id, receiver_id, text) VALUES (?, ?, ?)",
                           (sender_id, receiver_id, text))
            conn.commit()
        return jsonify({'message': 'Message sent successfully!'}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to send message: {e}'}), 500


@app.route('/get_messages/<int:user1_id>/<int:user2_id>', methods=['GET'])
def get_messages(user1_id, user2_id):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.sender_id, m.receiver_id, m.text, m.timestamp, 
                       (SELECT username FROM users WHERE id = m.sender_id) AS sender_name,
                       (SELECT username FROM users WHERE id = m.receiver_id) AS receiver_name
                FROM messages m
                WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
                ORDER BY m.timestamp ASC
            ''', (user1_id, user2_id, user2_id, user1_id))
            messages = cursor.fetchall()

        return jsonify({'messages': [
            {
                'sender_id': msg[0],
                'receiver_id': msg[1],
                'text': msg[2],
                'timestamp': msg[3],
                'sender_name': msg[4],
                'receiver_name': msg[5]
            } for msg in messages
        ]}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch messages: {e}'}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, profile_picture FROM users")
            users = cursor.fetchall()

        return jsonify({'users': [{'id': user[0], 'username': user[1], 'profile_picture': user[2]} for user in users]}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch users: {e}'}), 500

@app.route('/get_chat_users/<int:user_id>', methods=['GET'])
def get_chat_users(user_id):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Fetch users who have had a conversation with the logged-in user
            cursor.execute('''
                SELECT DISTINCT u.id, u.username, u.profile_picture
                FROM users u
                JOIN messages m ON u.id = m.sender_id OR u.id = m.receiver_id
                WHERE u.id != ? AND (m.sender_id = ? OR m.receiver_id = ?)
            ''', (user_id, user_id, user_id))
            users = cursor.fetchall()

        return jsonify({'users': [{'id': user[0], 'username': user[1], 'profile_picture': user[2]} for user in users]}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch chat users: {e}'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

