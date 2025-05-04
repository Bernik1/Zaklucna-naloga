from flask import Flask, render_template, request, redirect, url_for, flash, session
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'fb_secret_key'  

db = TinyDB('db.json')
users_table = db.table('users')

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        User = Query()
        existing_user = users_table.get(User.username == username)

        if existing_user:
            flash('Uporabniško ime že obstaja.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users_table.insert({'username': username, 'password': hashed_password})
            flash('Račun uspešno ustvarjen!', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        User = Query()
        user = users_table.get(User.username == username)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Prijava uspešna!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Napačno uporabniško ime ali geslo.', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Najprej se prijavi.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    User = Query()
    user_data = users_table.get(User.username == username)

    profile = user_data.get('profile', {})  # Če profil še ne obstaja
    return render_template('dashboard.html', username=username, profile=profile)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        flash('Najprej se prijavi.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    User = Query()
    user = users_table.get(User.username == username)

    if request.method == 'POST':
        age = request.form['age']
        goal = request.form['goal']
        bio = request.form['bio']

        users_table.update({'profile': {'age': age, 'goal': goal, 'bio': bio}}, User.username == username)
        flash('Profil shranjen.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('settings.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Uspešno si se odjavil.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)