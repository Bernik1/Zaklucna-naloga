from flask import Flask, render_template, request, redirect, url_for, flash
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key' 


db = TinyDB('db.json')
users_table = db.table('users')

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
        
        if user:
            if check_password_hash(user[0]['password'], password):
                flash('Login successful!', 'success')
                return redirect(url_for('home'))  
            else:
                flash('Invalid password. Please try again.', 'danger')  
        else:
            flash('Username not found. Please try again.', 'danger')  

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        User = Query()
        existing_user = users_table.search(User.username == username)

        if existing_user:
            flash('Username already taken, please choose another.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users_table.insert({'username': username, 'password': hashed_password})
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

if __name__ == "__main__":
    app.run(debug=True)