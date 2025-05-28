from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BACKGROUND_FOLDER'] = 'static/backgrounds'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = TinyDB('users.json')
users_table = db.table('users')
messages_table = db.table('messages')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

GIPHY_API_KEY = "6MUnabIswTdYCrQEbOJXHnJ8yu0NeA5K"

@app.route('/search_gifs')
def search_gifs():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'data': []})

    url = f'https://api.giphy.com/v1/gifs/search'
    params = {
        'api_key': GIPHY_API_KEY,
        'q': query,
        'limit': 10,
        'rating': 'g'
    }
    response = requests.get(url, params=params)
    data = response.json()
    gifs = [{'id': gif['id'], 'url': gif['images']['downsized_medium']['url']} for gif in data.get('data', [])]
    return jsonify({'data': gifs})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        User = Query()
        user = users_table.search(User.username == username)
        if user and check_password_hash(user[0]['password'], password):
            session['user_id'] = user[0]['username']
            flash('Prijava uspešna!', 'success')
            session['swiped_users'] = []
            return redirect(url_for('dashboard'))
        flash('Napačno uporabniško ime ali geslo.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        User = Query()
        if users_table.search(User.username == username):
            flash('Uporabniško ime je že zasedeno.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users_table.insert({
                'username': username,
                'password': hashed_password,
                'age': '',
                'goal': '',
                'bio': '',
                'picture': '',
                'background_image': ''
            })
            flash('Račun ustvarjen!', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Prijava je obvezna.', 'danger')
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
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                update_data['picture'] = filename

        if 'background_image' in request.files:
            file = request.files['background_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                bg_path = os.path.join(app.config['BACKGROUND_FOLDER'], filename)
                file.save(bg_path)
                update_data['background_image'] = filename

        users_table.update(update_data, User.username == user_id)
        flash('Profil posodobljen.', 'success')
        return redirect(url_for('dashboard'))

    profile = user[0] if user else None
    return render_template('settings.html', profile=profile)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Prijava je obvezna.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    User = Query()
    user = users_table.search(User.username == user_id)
    profile = user[0] if user else None

    all_users = [u for u in users_table.all() if u['username'] != user_id]

    if 'swiped_users' not in session:
        session['swiped_users'] = []

    swiped = session['swiped_users']
    remaining_users = [u for u in all_users if u['username'] not in swiped]

    if request.method == 'POST':
        swipe = request.form.get('swipe')
        user_to_swipe = request.form.get('user_to_swipe')
        if swipe and user_to_swipe:
            session['swiped_users'].append(user_to_swipe)
            session.modified = True
            flash(f'Odločitev: {swipe} za uporabnika {user_to_swipe}', 'info')
        remaining_users = [u for u in all_users if u['username'] not in session['swiped_users']]

    next_user = remaining_users[0] if remaining_users else None
    return render_template('dashboard.html', profile=profile, user=next_user)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Prijava je obvezna.', 'danger')
        return redirect(url_for('login'))
    User = Query()
    user = users_table.search(User.username == session['user_id'])
    profile = user[0] if user else None
    return render_template('profile.html', profile=profile)

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = session['user_id']
    User = Query()
    sent_to = set([msg['to_user'] for msg in messages_table.search(User.from_user == current_user)])
    received_from = set([msg['from_user'] for msg in messages_table.search(User.to_user == current_user)])
    chat_users = list(sent_to.union(received_from))

    chats = []
    for u in chat_users:
        user = users_table.search(User.username == u)
        if user:
            chats.append(user[0])

    return render_template('messages.html', chats=chats, selected_user=None)

@app.route('/chat/<username>', methods=['GET', 'POST'])
def chat(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = session['user_id']
    User = Query()

    selected_user_obj = users_table.search(User.username == username)
    if not selected_user_obj:
        flash('Uporabnik ne obstaja.', 'danger')
        return redirect(url_for('messages'))
    selected_user = username

    sent_to = set(msg['to_user'] for msg in messages_table.search(User.from_user == current_user))
    received_from = set(msg['from_user'] for msg in messages_table.search(User.to_user == current_user))
    chat_users = list(sent_to.union(received_from))

    chats = []
    for u in chat_users:
        user = users_table.search(User.username == u)
        if user:
            chats.append(user[0])

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            text = data.get('message_text', '').strip()
        else:
            text = request.form.get('message_text', '').strip()

        if text:
            messages_table.insert({
                'from_user': current_user,
                'to_user': username,
                'text': text,
                'timestamp': datetime.utcnow().isoformat()
            })

        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('chat', username=username))

    messages = messages_table.search(
        ((User.from_user == current_user) & (User.to_user == username)) |
        ((User.from_user == username) & (User.to_user == current_user))
    )
    messages_dicts = [dict(m) for m in messages]
    messages_sorted = sorted(messages_dicts, key=lambda m: m.get('timestamp', ''))

    return render_template('chat.html', chats=chats, selected_user=selected_user, messages=messages_sorted, current_user=current_user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('swiped_users', None)
    flash('Odjava uspešna.', 'info')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True) 