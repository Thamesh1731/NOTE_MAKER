from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
#app.secret_key = 'your_secret_key'  # Replace with your secret key

# MongoDB setup
client = MongoClient("mongodb+srv://admin:iambatman@note.2xzbk.mongodb.net/?retryWrites=true&w=majority&appName=NOTE")
db = client['note_taking_app']
users = db['users']
notes = db['notes']

# Image upload settings
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route
@app.route('/')
def home():
    if 'username' in session:
        user_notes = notes.find({'user': session['username']})
        return render_template('home.html', notes=user_notes)
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.find_one({'username': username}):
            return "User already exists"
        hashed_password = generate_password_hash(password)
        users.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        return "Invalid username or password"
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Add note route
@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        file = request.files['image']
        image_url = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = url_for('uploaded_file', filename=filename)
        notes.insert_one({
            'title': title, 
            'body': body, 
            'image_url': image_url, 
            'user': session['username']
        })
        return redirect(url_for('home'))
    return render_template('note_form.html')

# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Search notes route
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    results = notes.find({'user': session['username'], 'title': {'$regex': query, '$options': 'i'}})
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)

