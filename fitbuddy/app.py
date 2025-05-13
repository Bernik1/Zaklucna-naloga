from flask import Flask, render_template, redirect, url_for, flash, request, session
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Poti do upload map
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BACKGROUND_FOLDER'] = 'static/backgrounds'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Inicializacija baze
db = TinyDB('users.json')  
users_table = db.table('users')


# Funkcija za preverjanje dovoljene datoteke
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
            flash('Prijava uspešna!', 'success')
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

        # profilna
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                update_data['picture'] = filename

        # ozadje
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

    # Pridobivanje drugih uporabnikov, ki niso trenutni uporabnik
    users = [u for u in users_table.all() if u['username'] != user_id]

    # Obdelava swipe odločitve uporabnika
    if request.method == 'POST':
        swipe = request.form.get('swipe')  # 'left' ali 'right'
        user_to_swipe = request.form.get('user_to_swipe')

        # Shrani odločitev (lahko kasneje dodaš še shranjevanje v bazo ali session)
        if swipe and user_to_swipe:
            flash(f'Odločitev: {swipe} za uporabnika {user_to_swipe}', 'info')

        # Pomik naprej na naslednjega uporabnika (preprosto)
        if len(users) > 1:
            users.pop(0)

    return render_template('dashboard.html', profile=profile, users=users)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Odjava uspešna.', 'info')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
