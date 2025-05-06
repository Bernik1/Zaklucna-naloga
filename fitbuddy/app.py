from flask import Flask, render_template, redirect, url_for, flash, request, session
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = TinyDB('db.json')
users_table = db.table('users')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        User = Query()
        user = users_table.search(User.username == username)
        if user and check_password_hash(user[0]['password'], password):
            session['user_id'] = user[0]['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        User = Query()
        if users_table.search(User.username == username):
            flash('Username already taken.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users_table.insert({'username': username, 'password': hashed_password})
            flash('Account created!', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

# Settings (UPLOAD LOGIC HERE)
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Login required.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    User = Query()
    user = users_table.search(User.username == user_id)

    if request.method == 'POST':
        age = request.form['age']
        goal = request.form['goal']
        bio = request.form['bio']

        update_data = {'age': age, 'goal': goal, 'bio': bio}

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure folder exists
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                update_data['picture'] = filename

        users_table.update(update_data, User.username == user_id)
        flash('Profile updated.', 'success')
        return redirect(url_for('dashboard'))

    profile = user[0] if user else None
    return render_template('settings.html', profile=profile)

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Login required.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    User = Query()
    user = users_table.search(User.username == user_id)
    profile = user[0] if user else None
    return render_template('dashboard.html', profile=profile)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('home'))

# Run app
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)