import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Carica i dati da un file JSON
def load_data():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Salva i dati nel file JSON
def save_data(data):
    with open('users.json', 'w') as f:
        json.dump(data, f, indent=4)

# Oggetti disponibili con le rispettive rarità
objects = {
    "Spazzatura": {"rarity": "spazzatura", "color": "black"},
    "Comune": {"rarity": "comune", "color": "gray"},
    "Raro": {"rarity": "raro", "color": "blue"},
    "Epico": {"rarity": "epico", "color": "purple"},
    "Leggendario": {"rarity": "leggendario", "color": "yellow"},
    "Mitico": {"rarity": "mitico", "color": "orange"}
}

# Funzione per generare l'oggetto della lootbox
def generate_lootbox(lootbox_type):
    if lootbox_type == "rara":
        chances = [("Spazzatura", 50), ("Comune", 30), ("Raro", 15), ("Epico", 5)]
    elif lootbox_type == "epica":
        chances = [("Comune", 40), ("Raro", 30), ("Epico", 20), ("Leggendario", 10)]
    elif lootbox_type == "leggendaria":
        chances = [("Raro", 40), ("Epico", 30), ("Leggendario", 20), ("Mitico", 10)]
    elif lootbox_type == "mitica":
        chances = [("Epico", 30), ("Leggendario", 30), ("Mitico", 30), ("Raro", 10)]
    else:
        return []  # Gestione errore per tipo di lootbox non valido
    
    total_chances = sum(chance[1] for chance in chances)
    rand = random.randint(1, total_chances)
    current_sum = 0
    
    for item, chance in chances:
        current_sum += chance
        if rand <= current_sum:
            return [item]  # Restituisce una lista con un solo elemento (per mantenere compatibilità)
    
    return []  # Caso improbabile ma gestito

@app.route('/login', methods=['POST'])
def login():
    data = load_data()
    username = request.json.get('username')
    if username not in data:
        data[username] = {"saldo": 100, "inventario": []}  # Imposta saldo iniziale a 100
        save_data(data)
    return jsonify({"status": "success", "saldo": data[username]["saldo"], "inventario": data[username]["inventario"]})

@app.route('/buy_lootbox', methods=['POST'])
def buy_lootbox():
    data = load_data()
    username = request.json.get('username')
    lootbox_type = request.json.get('lootbox_type')
    
    if username not in data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Verifica che il tipo di lootbox sia valido
    cost = {"rara": 10, "epica": 30, "leggendaria": 50, "mitica": 100}  # Prezzi delle lootbox
    if lootbox_type not in cost:
        return jsonify({"status": "error", "message": "Tipo di lootbox non valido!"})
    
    if data[username]["saldo"] < cost[lootbox_type]:
        return jsonify({"status": "error", "message": "Non hai abbastanza denaro!"})
    
    # Dedurre il costo dal saldo dell'utente
    data[username]["saldo"] -= cost[lootbox_type]
    
    # Generare e aggiungere l'oggetto all'inventario dell'utente
    loot = generate_lootbox(lootbox_type)
    data[username]["inventario"].extend(loot)
    
    save_data(data)
    return jsonify({"status": "success", "saldo": data[username]["saldo"], "loot": loot})

if __name__ == '__main__':
    app.run(debug=True)
