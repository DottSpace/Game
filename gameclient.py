import requests
import json
import os
import time
import random

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
    "bold": "\033[1m",     # Grassetto
    "underline": "\033[4m" # Sottolineato
}

# Funzione per cancellare lo schermo
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Funzione per stampare informazioni utente
def print_user_info(username, saldo, level, exp):
    print(f"{COLORS['bold']}=== INFO GIOCATORE ==={COLORS['reset']}")
    print(f"Utente: {COLORS['green']}{username}{COLORS['reset']}")
    print(f"Livello: {COLORS['cyan']}{level}{COLORS['reset']}")
    print(f"Esperienza: {COLORS['blue']}{exp}{COLORS['reset']}")
    print(f"Saldo: {COLORS['yellow']}{saldo} denaro{COLORS['reset']}")
    print()

# Funzione per stampare le statistiche del personaggio
def print_stats(stats, equipped):
    print(f"{COLORS['bold']}=== STATISTICHE PERSONAGGIO ==={COLORS['reset']}")
    print(f"Salute: {COLORS['red']}{stats['health']}{COLORS['reset']}")
    print(f"Danno: {COLORS['orange']}{stats['damage']}{COLORS['reset']}")
    print(f"Difesa: {COLORS['blue']}{stats['defense']}{COLORS['reset']}")
    print()
    
    print(f"{COLORS['bold']}=== EQUIPAGGIAMENTO ==={COLORS['reset']}")
    if "weapon" in equipped:
        print(f"Arma: {COLORS['orange']}{equipped['weapon']}{COLORS['reset']}")
    else:
        print(f"Arma: {COLORS['gray']}Nessuna{COLORS['reset']}")
    
    if "armor" in equipped:
        print(f"Armatura: {COLORS['blue']}{equipped['armor']}{COLORS['reset']}")
    else:
        print(f"Armatura: {COLORS['gray']}Nessuna{COLORS['reset']}")
    
    if "amulet" in equipped:
        print(f"Amuleto: {COLORS['purple']}{equipped['amulet']}{COLORS['reset']}")
    else:
        print(f"Amuleto: {COLORS['gray']}Nessuno{COLORS['reset']}")
    print()

# Funzione per visualizzare l'inventario dettagliato
def show_inventory(inventory, equipped):
    clear()
    print(f"{COLORS['bold']}=== INVENTARIO ==={COLORS['reset']}")
    
    if not inventory:
        print("Il tuo inventario è vuoto!")
    else:
        # Ordina gli oggetti per tipo e rarità
        items_by_type = {
            "weapon": [],
            "armor": [],
            "amulet": []
        }
        
        for item in inventory:
            item_type = item["type"]
            if item_type in items_by_type:
                items_by_type[item_type].append(item)
        
        # Rarità in ordine decrescente
        rarities_order = {"Mitico": 6, "Leggendario": 5, "Epico": 4, "Raro": 3, "Comune": 2, "Spazzatura": 1}
        
        # Visualizza armi
        if items_by_type["weapon"]:
            print(f"\n{COLORS['bold']}ARMI:{COLORS['reset']}")
            sorted_weapons = sorted(items_by_type["weapon"], key=lambda x: rarities_order.get(x["rarity"], 0), reverse=True)
            for item in sorted_weapons:
                color = get_rarity_color(item["rarity"])
                equipped_marker = f" {COLORS['green']}[EQUIPAGGIATO]{COLORS['reset']}" if "weapon" in equipped and equipped["weapon"] == item["name"] else ""
                print(f"{color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} (Danno: {item['stats']['damage']}{equipped_marker})")
        
        # Visualizza armature
        if items_by_type["armor"]:
            print(f"\n{COLORS['bold']}ARMATURE:{COLORS['reset']}")
            sorted_armors = sorted(items_by_type["armor"], key=lambda x: rarities_order.get(x["rarity"], 0), reverse=True)
            for item in sorted_armors:
                color = get_rarity_color(item["rarity"])
                equipped_marker = f" {COLORS['green']}[EQUIPAGGIATO]{COLORS['reset']}" if "armor" in equipped and equipped["armor"] == item["name"] else ""
                print(f"{color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} (Difesa: {item['stats']['defense']}{equipped_marker})")
        
        # Visualizza amuleti
        if items_by_type["amulet"]:
            print(f"\n{COLORS['bold']}AMULETI:{COLORS['reset']}")
            sorted_amulets = sorted(items_by_type["amulet"], key=lambda x: rarities_order.get(x["rarity"], 0), reverse=True)
            for item in sorted_amulets:
                color = get_rarity_color(item["rarity"])
                equipped_marker = f" {COLORS['green']}[EQUIPAGGIATO]{COLORS['reset']}" if "amulet" in equipped and equipped["amulet"] == item["name"] else ""
                effect_text = get_effect_text(item["stats"]["effect"], item["stats"]["bonus"])
                print(f"{color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} ({effect_text}{equipped_marker})")
    
    print("\n1. Equipaggia oggetto")
    print("2. Rimuovi oggetto equipaggiato")
    print("3. Torna al menu principale")
    
    choice = input("\nScelta: ")
    return choice

# Funzione per ottenere il colore di una rarità
def get_rarity_color(rarity):
    if rarity == "Spazzatura":
        return COLORS["black"]
    elif rarity == "Comune":
        return COLORS["gray"]
    elif rarity == "Raro":
        return COLORS["blue"]
    elif rarity == "Epico":
        return COLORS["purple"]
    elif rarity == "Leggendario":
        return COLORS["yellow"]
    elif rarity == "Mitico":
        return COLORS["orange"]
    return COLORS["reset"]

# Funzione per ottenere la descrizione testuale dell'effetto di un amuleto
def get_effect_text(effect, bonus):
    if effect == "health":
        return f"Salute +{bonus}"
    elif effect == "damage":
        return f"Danno +{bonus}"
    elif effect == "defense":
        return f"Difesa +{bonus}"
    elif effect == "all":
        return f"Tutte le statistiche +{bonus}"
    return ""

# Funzione per equipaggiare un oggetto
def equip_item(username, inventory, equipped):
    clear()
    print(f"{COLORS['bold']}=== EQUIPAGGIA OGGETTO ==={COLORS['reset']}")
    
    # Organizza gli oggetti per tipo
    items_by_type = {
        "weapon": [],
        "armor": [],
        "amulet": []
    }
    
    for i, item in enumerate(inventory):
        item_type = item["type"]
        if item_type in items_by_type:
            items_by_type[item_type].append((i, item))
    
    # Mostra lista di oggetti numerati
    print("\nArmi:")
    if not items_by_type["weapon"]:
        print("Nessuna arma disponibile.")
    else:
        for i, (index, item) in enumerate(items_by_type["weapon"]):
            color = get_rarity_color(item["rarity"])
            equipped_marker = " [EQUIPAGGIATO]" if "weapon" in equipped and equipped["weapon"] == item["name"] else ""
            print(f"{i+1}. {color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} (Danno: {item['stats']['damage']}){equipped_marker}")
    
    print("\nArmature:")
    if not items_by_type["armor"]:
        print("Nessuna armatura disponibile.")
    else:
        for i, (index, item) in enumerate(items_by_type["armor"]):
            color = get_rarity_color(item["rarity"])
            equipped_marker = " [EQUIPAGGIATO]" if "armor" in equipped and equipped["armor"] == item["name"] else ""
            print(f"{len(items_by_type['weapon'])+i+1}. {color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} (Difesa: {item['stats']['defense']}){equipped_marker}")
    
    print("\nAmuleti:")
    if not items_by_type["amulet"]:
        print("Nessun amuleto disponibile.")
    else:
        for i, (index, item) in enumerate(items_by_type["amulet"]):
            color = get_rarity_color(item["rarity"])
            equipped_marker = " [EQUIPAGGIATO]" if "amulet" in equipped and equipped["amulet"] == item["name"] else ""
            effect_text = get_effect_text(item["stats"]["effect"], item["stats"]["bonus"])
            print(f"{len(items_by_type['weapon'])+len(items_by_type['armor'])+i+1}. {color}{item['name']}{COLORS['reset']} - {color}{item['rarity']}{COLORS['reset']} ({effect_text}){equipped_marker}")
    
    print("\n0. Torna indietro")
    
    try:
        choice = int(input("\nScegli un oggetto da equipaggiare: "))
        if choice == 
