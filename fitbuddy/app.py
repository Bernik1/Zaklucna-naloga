from flask import Flask, render_template, request, redirect, url_for, flash, session
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'FB_secret_key'  

db = TinyDB('db.json')
users_table = db.table('users')
matches_table = db.table('matches')

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

    profile = user_data.get('profile', {})  
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

    profile = user.get('profile', {})
    return render_template('settings.html', profile=profile)


@app.route('/logout')
def logout():
    session.clear()
    flash('Uspešno si se odjavil.', 'info')
    return redirect(url_for('login'))


@app.route('/swipe', methods=['GET', 'POST'])
def swipe():
    if 'username' not in session:
        flash('Najprej se prijavi.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    User = Query()
    user_data = users_table.get(User.username == username)

    all_users = users_table.all()
    all_users = [user for user in all_users if user['username'] != username] 

    if request.method == 'POST':
        swipe_action = request.form['swipe_action']
        target_user = request.form['target_user']
        
        if swipe_action == 'right':  
            match = {
                'user1': username,
                'user2': target_user
            }
            matches_table.insert(match)
            flash(f'Povezan z {target_user}!', 'success')
        
        return redirect(url_for('swipe'))

    return render_template('swipe.html', users=all_users)


@app.route('/messages')
def messages():
    if 'username' not in session:
        flash('Najprej se prijavi.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    User = Query()
    matches = matches_table.search((Query().user1 == username) | (Query().user2 == username))
    
    matched_users = set()
    for match in matches:
        matched_users.add(match['user1'] if match['user1'] != username else match['user2'])
    
    return render_template('messages.html', matches=matched_users)


@app.route('/chat/<target_user>', methods=['GET', 'POST'])
def chat(target_user):
    if 'username' not in session:
        flash('Najprej se prijavi.', 'warning')
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        message = request.form['message']
        flash(f'Poslano sporočilo {target_user}: {message}', 'success')

    return render_template('chat.html', target_user=target_user)


if __name__ == '__main__':
    app.run(debug=True, port=5001)