import requests
import json
import os
import time

# Definizione dei colori ANSI
COLORS = {
    "reset": "\033[0m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "gray": "\033[90m",
    "orange": "\033[33m",  # Usiamo giallo per simulare arancione
}

# Funzione per cancellare lo schermo
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Funzione per stampare il saldo
def print_balance(balance):
    print(f"Saldo attuale: {balance} denaro")

# Funzione per visualizzare l'inventario
def show_inventory(inventory):
    clear()
    print("=== INVENTARIO ===")
    if not inventory:
        print("Il tuo inventario è vuoto!")
    else:
        # Conteggio degli oggetti per tipo
        item_counts = {}
        for item in inventory:
            if item in item_counts:
                item_counts[item] += 1
            else:
                item_counts[item] = 1
                
        # Visualizzazione ordinata per rarità
        rarities_order = ["Mitico", "Leggendario", "Epico", "Raro", "Comune", "Spazzatura"]
        
        for rarity in rarities_order:
            if rarity in item_counts:
                color = COLORS["green"]  # Default color
                if rarity == "Spazzatura":
                    color = COLORS["black"]
                elif rarity == "Comune":
                    color = COLORS["gray"]
                elif rarity == "Raro":
                    color = COLORS["blue"]
                elif rarity == "Epico":
                    color = COLORS["purple"]
                elif rarity == "Leggendario":
                    color = COLORS["yellow"]
                elif rarity == "Mitico":
                    color = COLORS["orange"]
                
                print(f"{color}{rarity} - {item_counts[rarity]}x{COLORS['reset']}")
    
    print("\nPremi invio per tornare.")
    input()

# Funzione per aprire la lootbox
def open_lootbox():
    clear()
    print("Scegli una lootbox:")
    print(f"1. Lootbox Rara - 10 denaro ({COLORS['black']}Spazzatura 50%{COLORS['reset']}, {COLORS['gray']}Comune 30%{COLORS['reset']}, {COLORS['blue']}Raro 15%{COLORS['reset']}, {COLORS['purple']}Epico 5%{COLORS['reset']})")
    print(f"2. Lootbox Epica - 30 denaro ({COLORS['gray']}Comune 40%{COLORS['reset']}, {COLORS['blue']}Raro 30%{COLORS['reset']}, {COLORS['purple']}Epico 20%{COLORS['reset']}, {COLORS['yellow']}Leggendario 10%{COLORS['reset']})")
    print(f"3. Lootbox Leggendaria - 50 denaro ({COLORS['blue']}Raro 40%{COLORS['reset']}, {COLORS['purple']}Epico 30%{COLORS['reset']}, {COLORS['yellow']}Leggendario 20%{COLORS['reset']}, {COLORS['orange']}Mitico 10%{COLORS['reset']})")
    print(f"4. Lootbox Mitica - 100 denaro ({COLORS['purple']}Epico 30%{COLORS['reset']}, {COLORS['yellow']}Leggendario 30%{COLORS['reset']}, {COLORS['orange']}Mitico 30%{COLORS['reset']}, {COLORS['blue']}Raro 10%{COLORS['reset']})")
    print("b. Torna indietro")
    
    choice = input("Scegli un numero: ")
    if choice == 'b':
        return None
    
    lootbox_types = {"1": "rara", "2": "epica", "3": "leggendaria", "4": "mitica"}
    return lootbox_types.get(choice)

# Funzione per il login dell'utente
def login():
    clear()
    username = input("Inserisci il tuo username: ")
    try:
        response = requests.post('http://127.0.0.1:5000/login', json={"username": username})
        data = response.json()

        if data['status'] == 'success':
            print(f"Benvenuto {username}! Il tuo saldo è: {data['saldo']}")
            time.sleep(1)
            return username, data['saldo'], data['inventario']
        else:
            print("Errore nel login.")
            time.sleep(1)
            return None, 0, []
    except requests.exceptions.ConnectionError:
        print("Errore di connessione al server. Assicurati che il server sia in esecuzione.")
        time.sleep(2)
        return None, 0, []

# Funzione per mostrare i risultati della lootbox
def show_lootbox_results(loot):
    clear()
    print("=== HAI TROVATO ===")
    if not loot:
        print("Nessun oggetto trovato!")
    else:
        for item in loot:
            color = COLORS["green"]  # Default color
            if item == "Spazzatura":
                color = COLORS["black"]
            elif item == "Comune":
                color = COLORS["gray"]
            elif item == "Raro":
                color = COLORS["blue"]
            elif item == "Epico":
                color = COLORS["purple"]
            elif item == "Leggendario":
                color = COLORS["yellow"]
            elif item == "Mitico":
                color = COLORS["orange"]
            
            print(f"{color}{item}{COLORS['reset']}")
    
    print("\nPremi invio per continuare...")
    input()

# Funzione principale per il gioco
def main():
    username, saldo, inventory = login()

    if not username:
        return

    while True:
        clear()
        print(f"=== LOOTBOX GAME ===")
        print(f"Utente: {username}")
        print_balance(saldo)
        print("\nCosa vuoi fare?")
        print("1. Apri Lootbox")
        print("2. Vedi Inventario")
        print("q. Esci")

        choice = input("Scegli un'opzione: ")

        if choice == '1':
            lootbox_type = open_lootbox()
            if lootbox_type:
                try:
                    response = requests.post('http://127.0.0.1:5000/buy_lootbox', 
                                           json={'username': username, 'lootbox_type': lootbox_type})
                    data = response.json()
                    if data['status'] == 'success':
                        saldo = data['saldo']
                        inventory.extend(data['loot'])  # Aggiorna l'inventario locale
                        show_lootbox_results(data['loot'])
                    else:
                        print(data['message'])
                        input("\nPremi invio per continuare...")
                except requests.exceptions.ConnectionError:
                    print("Errore di connessione al server.")
                    input("\nPremi invio per continuare...")
        elif choice == '2':
            show_inventory(inventory)
        elif choice == 'q':
            clear()
            print("Grazie per aver giocato! Arrivederci.")
            time.sleep(1)
            break
        else:
            print("Opzione non valida. Riprova.")
            time.sleep(1)

if __name__ == '__main__':
    main()