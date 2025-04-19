import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Carica i dati dal file JSON
def load_user_data():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Carica i dati di gioco
def load_game_data():
    try:
        with open('data.dat', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Salva i dati nel file JSON
def save_user_data(data):
    with open('users.json', 'w') as f:
        json.dump(data, f, indent=4)

# Funzione per generare item dalla lootbox
def generate_lootbox_item(lootbox_type):
    game_data = load_game_data()
    chances = game_data["lootbox_chances"][lootbox_type]
    
    # Calcola la somma totale delle probabilità
    total_chance = sum(item["chance"] for item in chances)
    
    # Genera un numero casuale
    rand = random.randint(1, total_chance)
    
    # Seleziona l'elemento in base alla probabilità
    current_sum = 0
    selected_item_info = None
    
    for item_chance in chances:
        current_sum += item_chance["chance"]
        if rand <= current_sum:
            selected_item_info = item_chance
            break
    
    if not selected_item_info:
        return None
    
    # Ottieni tutti gli oggetti della categoria e rarità selezionata
    items_in_category = game_data["items"][selected_item_info["item_type"]]
    matching_items = [item_name for item_name, item_data in items_in_category.items() 
                     if item_data["rarity"] == selected_item_info["rarity"]]
    
    if not matching_items:
        return None
    
    # Seleziona casualmente un oggetto dalla lista
    selected_item = random.choice(matching_items)
    
    return {
        "name": selected_item,
        "type": items_in_category[selected_item]["type"],
        "rarity": items_in_category[selected_item]["rarity"],
        "stats": items_in_category[selected_item]
    }

# Calcola il livello in base all'esperienza
def calculate_level(exp):
    game_data = load_game_data()
    level_data = game_data["levels"]["exp_requirements"]
    
    current_level = 1
    for level, required_exp in sorted(level_data.items(), key=lambda x: int(x[0])):
        if exp >= required_exp:
            current_level = int(level)
        else:
            break
    
    return current_level

# Calcola le statistiche del personaggio in base al livello e all'equipaggiamento
def calculate_stats(user_data):
    game_data = load_game_data()
    level = calculate_level(user_data.get("exp", 0))
    base_stats = game_data["levels"]["stats"]
    
    # Calcola statistiche base per livello
    stats = {
        "health": base_stats["base_health"] + (level - 1) * base_stats["health_per_level"],
        "damage": base_stats["base_damage"] + (level - 1) * base_stats["damage_per_level"],
        "defense": base_stats["base_defense"] + (level - 1) * base_stats["defense_per_level"]
    }
    
    # Aggiungi bonus dall'equipaggiamento
    equipped = user_data.get("equipped", {})
    if "weapon" in equipped:
        item = next((i for i in user_data["inventory"] if i["name"] == equipped["weapon"]), None)
        if item:
            stats["damage"] += item["stats"].get("damage", 0)
    
    if "armor" in equipped:
        item = next((i for i in user_data["inventory"] if i["name"] == equipped["armor"]), None)
        if item:
            stats["defense"] += item["stats"].get("defense", 0)
    
    if "amulet" in equipped:
        item = next((i for i in user_data["inventory"] if i["name"] == equipped["amulet"]), None)
        if item:
            effect = item["stats"].get("effect", "")
            bonus = item["stats"].get("bonus", 0)
            
            if effect == "health":
                stats["health"] += bonus
            elif effect == "damage":
                stats["damage"] += bonus
            elif effect == "defense":
                stats["defense"] += bonus
            elif effect == "all":
                stats["health"] += bonus
                stats["damage"] += bonus
                stats["defense"] += bonus
    
    return stats

# Seleziona un nemico in base alla posizione e al livello del giocatore
def select_enemy(location, player_level):
    game_data = load_game_data()
    location_data = game_data["locations"].get(location)
    
    if not location_data:
        return None
    
    # Filtra i nemici che sono appropriati per il livello del giocatore
    possible_enemies = []
    for enemy_name in location_data["enemies"]:
        enemy_data = game_data["enemies"].get(enemy_name)
        if enemy_data and player_level >= enemy_data["level_range"][0] and player_level <= enemy_data["level_range"][1]:
            possible_enemies.append((enemy_name, enemy_data))
    
    if not possible_enemies:
        return None
    
    # Seleziona casualmente un nemico dalla lista
    enemy_name, enemy_data = random.choice(possible_enemies)
    
    return {
        "name": enemy_name,
        "health": enemy_data["health"],
        "damage": enemy_data["damage"],
        "defense": enemy_data["defense"],
        "exp": enemy_data["exp"],
        "gold": enemy_data["gold"],
        "drop_chance": enemy_data["drop_chance"],
        "drops": enemy_data["drops"]
    }

@app.route('/login', methods=['POST'])
def login():
    user_data = load_user_data()
    username = request.json.get('username')
    
    if username not in user_data:
        # Crea un nuovo utente con valori predefiniti
        user_data[username] = {
            "saldo": 100,
            "exp": 0,
            "inventory": [],
            "equipped": {}
        }
        save_user_data(user_data)
    
    # Calcola il livello attuale
    level = calculate_level(user_data[username].get("exp", 0))
    
    # Calcola le statistiche del personaggio
    stats = calculate_stats(user_data[username])
    
    return jsonify({
        "status": "success", 
        "saldo": user_data[username]["saldo"], 
        "inventory": user_data[username]["inventory"],
        "level": level,
        "exp": user_data[username].get("exp", 0),
        "stats": stats,
        "equipped": user_data[username].get("equipped", {})
    })

@app.route('/buy_lootbox', methods=['POST'])
def buy_lootbox():
    user_data = load_user_data()
    game_data = load_game_data()
    username = request.json.get('username')
    lootbox_type = request.json.get('lootbox_type')
    
    if username not in user_data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Verifica che il tipo di lootbox sia valido
    cost = {"rara": 10, "epica": 30, "leggendaria": 50, "mitica": 100}  # Prezzi delle lootbox
    if lootbox_type not in cost:
        return jsonify({"status": "error", "message": "Tipo di lootbox non valido!"})
    
    if user_data[username]["saldo"] < cost[lootbox_type]:
        return jsonify({"status": "error", "message": "Non hai abbastanza denaro!"})
    
    # Dedurre il costo dal saldo dell'utente
    user_data[username]["saldo"] -= cost[lootbox_type]
    
    # Generare e aggiungere l'oggetto all'inventario dell'utente
    item = generate_lootbox_item(lootbox_type)
    if item:
        user_data[username]["inventory"].append(item)
        loot = [item]
    else:
        loot = []
    
    save_user_data(user_data)
    return jsonify({
        "status": "success", 
        "saldo": user_data[username]["saldo"], 
        "loot": loot
    })

@app.route('/equip_item', methods=['POST'])
def equip_item():
    user_data = load_user_data()
    username = request.json.get('username')
    item_name = request.json.get('item_name')
    
    if username not in user_data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Trova l'oggetto nell'inventario
    item = next((i for i in user_data[username]["inventory"] if i["name"] == item_name), None)
    
    if not item:
        return jsonify({"status": "error", "message": "Oggetto non trovato nell'inventario!"})
    
    # Inizializza equipped se non esiste
    if "equipped" not in user_data[username]:
        user_data[username]["equipped"] = {}
    
    # Equipaggia l'oggetto in base al suo tipo
    item_type = item["type"]
    if item_type == "weapon":
        user_data[username]["equipped"]["weapon"] = item_name
    elif item_type == "armor":
        user_data[username]["equipped"]["armor"] = item_name
    elif item_type == "amulet":
        user_data[username]["equipped"]["amulet"] = item_name
    
    # Salva i dati
    save_user_data(user_data)
    
    # Calcola le statistiche aggiornate
    stats = calculate_stats(user_data[username])
    
    return jsonify({
        "status": "success", 
        "message": f"{item_name} equipaggiato con successo!", 
        "equipped": user_data[username]["equipped"],
        "stats": stats
    })

@app.route('/unequip_item', methods=['POST'])
def unequip_item():
    user_data = load_user_data()
    username = request.json.get('username')
    slot = request.json.get('slot')  # weapon, armor, amulet
    
    if username not in user_data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Inizializza equipped se non esiste
    if "equipped" not in user_data[username]:
        user_data[username]["equipped"] = {}
    
    # Verifica che lo slot sia valido
    if slot not in ["weapon", "armor", "amulet"]:
        return jsonify({"status": "error", "message": "Slot non valido!"})
    
    # Verifica che ci sia un oggetto equipaggiato nello slot
    if slot not in user_data[username]["equipped"]:
        return jsonify({"status": "error", "message": f"Nessun oggetto equipaggiato nello slot {slot}!"})
    
    # Rimuovi l'oggetto equipaggiato
    item_name = user_data[username]["equipped"][slot]
    del user_data[username]["equipped"][slot]
    
    # Salva i dati
    save_user_data(user_data)
    
    # Calcola le statistiche aggiornate
    stats = calculate_stats(user_data[username])
    
    return jsonify({
        "status": "success", 
        "message": f"{item_name} rimosso con successo!", 
        "equipped": user_data[username]["equipped"],
        "stats": stats
    })

@app.route('/get_locations', methods=['POST'])
def get_locations():
    game_data = load_game_data()
    username = request.json.get('username')
    user_data = load_user_data()
    
    if username not in user_data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Calcola il livello del giocatore
    level = calculate_level(user_data[username].get("exp", 0))
    
    # Filtra le location in base al livello del giocatore
    available_locations = {}
    for loc_name, loc_data in game_data["locations"].items():
        if level >= loc_data["level_range"][0]:
            available_locations[loc_name] = {
                "description": loc_data["description"],
                "level_range": loc_data["level_range"]
            }
    
    return jsonify({
        "status": "success", 
        "locations": available_locations
    })

@app.route('/pve_battle', methods=['POST'])
def pve_battle():
    user_data = load_user_data()
    game_data = load_game_data()
    username = request.json.get('username')
    location = request.json.get('location')
    
    if username not in user_data:
        return jsonify({"status": "error", "message": "Utente non trovato!"})
    
    # Verifica che la location esista
    if location not in game_data["locations"]:
        return jsonify({"status": "error", "message": "Location non valida!"})
    
    # Calcola il livello del giocatore
    level = calculate_level(user_data[username].get("exp", 0))
    
    # Verifica che il giocatore abbia il livello minimo richiesto
    if level < game_data["locations"][location]["level_range"][0]:
        return jsonify({
            "status": "error", 
            "message": f"Livello minimo richiesto: {game_data['locations'][location]['level_range'][0]}"
        })
    
    # Seleziona un nemico
    enemy = select_enemy(location, level)
    if not enemy:
        return jsonify({"status": "error", "message": "Nessun nemico disponibile!"})
    
    # Calcola le statistiche del giocatore
    player_stats = calculate_stats(user_data[username])
    
    # Simulazione della battaglia
    battle_log = []
    player_current_hp = player_stats["health"]
    enemy_current_hp = enemy["health"]
    round_num = 1
    
    # Log dell'inizio battaglia
    battle_log.append(f"Inizio battaglia contro {enemy['name']}!")
    battle_log.append(f"Statistiche giocatore: HP {player_stats['health']}, ATK {player_stats['damage']}, DEF {player_stats['defense']}")
    battle_log.append(f"Statistiche nemico: HP {enemy['health']}, ATK {enemy['damage']}, DEF {enemy['defense']}")
    
    player_won = False
    
    while player_current_hp > 0 and enemy_current_hp > 0:
        battle_log.append(f"\nRound {round_num}:")
        
        # Attacco del giocatore
        player_damage = max(1, player_stats["damage"] - enemy["defense"] // 2)
        enemy_current_hp -= player_damage
        battle_log.append(f"Hai inflitto {player_damage} danni a {enemy['name']}. HP rimanente: {max(0, enemy_current_hp)}")
        
        # Verifica se il nemico è stato sconfitto
        if enemy_current_hp <= 0:
            player_won = True
            break
        
        # Attacco del nemico
        enemy_damage = max(1, enemy["damage"] - player_stats["defense"] // 2)
        player_current_hp -= enemy_damage
        battle_log.append(f"{enemy['name']} ti ha inflitto {enemy_damage} danni. HP rimanente: {max(0, player_current_hp)}")
        
        round_num += 1
    
    # Risultato della battaglia
    if player_won:
        battle_log.append(f"\nHai sconfitto {enemy['name']}!")
        
        # Calcola ricompense
        exp_reward = enemy["exp"]
        gold_range = enemy["gold"].split("-")
        gold_min, gold_max = int(gold_range[0]), int(gold_range[1])
        gold_reward = random.randint(gold_min, gold_max)
        
        # Aggiungi exp e oro al giocatore
        user_data[username]["exp"] = user_data[username].get("exp", 0) + exp_reward
        user_data[username]["saldo"] += gold_reward
        
        battle_log.append(f"Hai guadagnato {exp_reward} EXP e {gold_reward} denaro!")
        
        # Calcola nuovo livello
        old_level = calculate_level(user_data[username].get("exp", 0) - exp_reward)
        new_level = calculate_level(user_data[username].get("exp", 0))
        
        if new_level > old_level:
            battle_log.append(f"Sei salito di livello! Nuovo livello: {new_level}")
        
        # Verifica se il nemico ha lasciato cadere un oggetto
        if random.random() < enemy["drop_chance"]:
            # Seleziona casualmente un oggetto dalla lista dei drop
            if enemy["drops"]:
                dropped_item_name = random.choice(enemy["drops"])
                
                # Trova l'oggetto nei dati di gioco
                item_found = False
                for item_category in game_data["items"]:
                    if dropped_item_name in game_data["items"][item_category]:
                        item_data = game_data["items"][item_category][dropped_item_name]
                        new_item = {
                            "name": dropped_item_name,
                            "type": item_data["type"],
                            "rarity": item_data["rarity"],
                            "stats": item_data
                        }
                        user_data[username]["inventory"].append(new_item)
                        battle_log.append(f"Hai trovato: {dropped_item_name} ({item_data['rarity']})")
                        item_found = True
                        break
                
                if not item_found:
                    battle_log.append("Errore: oggetto non trovato nei dati di gioco!")
    else:
        battle_log.append(f"\nSei stato sconfitto da {enemy['name']}!")
        battle_log.append("Hai perso la battaglia ma hai guadagnato esperienza dal combattimento.")
        
        # Guadagna una piccola quantità di exp anche quando perdi
        exp_reward = enemy["exp"] // 4
        user_data[username]["exp"] = user_data[username].get("exp", 0) + exp_reward
        battle_log.append(f"Hai guadagnato {exp_reward} EXP!")
    
    # Salva i dati dell'utente
    save_user_data(user_data)
    
    # Aggiorna le statistiche e il livello del giocatore
    stats = calculate_stats(user_data[username])
    level = calculate_level(user_data[username].get("exp", 0))
    
    return jsonify({
        "status": "success",
        "battle_log": battle_log,
        "player_won": player_won,
        "new_stats": stats,
        "new_level": level,
        "new_exp": user_data[username].get("exp", 0),
        "new_saldo": user_data[username]["saldo"]
    })

if __name__ == '__main__':
    app.run(debug=True)
