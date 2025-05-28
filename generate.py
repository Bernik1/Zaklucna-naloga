from tinydb import TinyDB
from werkzeug.security import generate_password_hash

db = TinyDB('users.json')
users_table = db.table('users')

users_table.truncate()  

for i in range(1, 101):
    username = f"user{i}"
    password_hash = generate_password_hash("test123")
    age = str(16 + i % 10)
    goal = "Izboljšanje moči" if i % 2 == 0 else "Izboljšanje vzdržljivosti"
    bio = f"Sem uporabnik številka {i}. Rad treniram in swipam."
    picture = f"user{i}.jpg"  
    
    users_table.insert({
        "username": username,
        "password": password_hash,
        "age": age,
        "goal": goal,
        "bio": bio,
        "picture": picture,
        "background_image": ""
    })

print("Dodano 100 uporabnikov za testiranje.")
