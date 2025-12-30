import requests
import re
import hashlib
from ics import Calendar, Event
import arrow

# ==========================================
# 1. CONFIGURATION
# ==========================================

# ==========================================
# MAPPING DES ADRESSES (Pour Google Maps)
# ==========================================
ADRESSES_BATIMENTS = {
    "M3": "Bâtiment M3, Avenue Carl Gauss, 59655 Villeneuve-d'Ascq",
    "M5": "Bâtiment M5, Université de Lille, 59655 Villeneuve-d'Ascq",
    "M1": "Bâtiment M1, Université de Lille, 59655 Villeneuve-d'Ascq",
    "M2": "Bâtiment M2, Université de Lille, 59655 Villeneuve-d'Ascq",
    "TP": "Bâtiment M3, Avenue Carl Gauss, 59655 Villeneuve-d'Ascq",
    "P1": "Bâtiment P1, Avenue Paul Langevin, 59655 Villeneuve-d'Ascq",
    "P2": "Bâtiment P2, Avenue Paul Langevin, 59655 Villeneuve-d'Ascq",
    "P3": "Bâtiment P3, Avenue Paul Langevin, 59655 Villeneuve-d'Ascq",
    "P4": "Bâtiment P4, Avenue Paul Langevin, 59655 Villeneuve-d'Ascq",
    "P5": "Bâtiment P5, Avenue Paul Langevin, 59655 Villeneuve-d'Ascq",
    "Amphi": "Université de Lille, 59655 Villeneuve-d'Ascq",
    "Halle": "Halle Vallin, 59655 Villeneuve-d'Ascq"
}

def enrichir_localisation(raw_location, title):
    """
    Cherche le bâtiment dans le lieu OU dans le titre.
    """
    # 1. Recherche dans le TITRE (car souvent la salle est là : ".../M5-A12")
    for batiment, adresse in ADRESSES_BATIMENTS.items():
        if batiment in title:
            return adresse

    # 2. Recherche dans le lieu (au cas où)
    if raw_location:
        for batiment, adresse in ADRESSES_BATIMENTS.items():
            if batiment in raw_location:
                return f"{raw_location}, {adresse}"
    
    # 3. Fallback (Si on a rien trouvé)
    if raw_location:
         return f"{raw_location}, Université de Lille, 59655 Villeneuve-d'Ascq"
    return "Université de Lille, 59655 Villeneuve-d'Ascq"

URL_AGENDA = "https://www.fil.univ-lille.fr/~aubert/l3/agenda/2526-S6-All.json"
OUTPUT_FILE = "data_export.ics"

# Dictionnaire de tes groupes : 'MATIERE': Numéro_Groupe
# Note : Pour les CM (Cours Magistraux), le script les prendra automatiquement.
MES_CHOIX = {
    'TEC': 6,
    'Projet': 4,
    'RSX2': 2,
    'GL': 5,
    'JSFS': 4,
    'LAAS': 2,
    'PDS': 4,
    'II2D': 1,  # Ton option découverte
    'ARCHI': 0, # Mettre 0 si tu ne fais pas cette matière (pour être sûr)
    'Logique': 0,
    'BIOINFO': 0,
    'PP': 0,
    'META': 0,
    'MAL': 0,
    'PDM': 0
}

# ==========================================
# 2. LE MOTEUR DE TRAITEMENT
# ==========================================

def parse_event_info(title):
    """
    Réplique la logique Regex du fichier JS CalendarL3S6.js
    Retourne: nature (CM/TD/TP), matiere, groupe
    """
    # Regex du JS: const reCourse = evt.title.match('^(..) (\\w+)/');
    match_course = re.search(r'^(..) (\w+)/', title)
    
    # Regex du JS: const reGroup = evt.title.match('\(G(\\d)\)');
    match_group = re.search(r'\(G(\d)\)', title)

    nature = "special"
    matiere = "special"
    groupe = None

    if match_course:
        nature = match_course.group(1)  # ex: CM, TD, TP
        matiere = match_course.group(2) # ex: RSX2, GL
        
        # Validation comme dans le JS
        if nature not in ['CM', 'TD', 'TP']:
            nature = 'special'
            matiere = 'special'

    if match_group:
        groupe = int(match_group.group(1))

    return nature, matiere, groupe

def est_pour_cedric(item):
    """Filtre les cours selon tes groupes"""
    title = item.get('title', '')
    nature, matiere, groupe_event = parse_event_info(title)

    # 1. On garde toujours les événements spéciaux (Rentrée, Examens, Conférences...)
    if matiere == 'special':
        return True

    # 2. Si la matière n'est pas dans ta liste (ex: Logique, BioInfo...), on jette
    if matiere not in MES_CHOIX:
        return False
    
    mon_groupe = MES_CHOIX[matiere]

    # 3. Si tu as mis 0 ou None dans la config, tu ne suis pas ce cours
    if not mon_groupe:
        return False

    # 4. Logique principale :
    # - Si c'est un CM : ON GARDE (tout le monde va en CM)
    # - Si c'est TD/TP : On compare le numéro de groupe
    if nature == 'CM':
        return True
    
    # Si l'événement a un numéro de groupe, il doit correspondre au tien
    if groupe_event is not None:
        return groupe_event == mon_groupe
    
    # Si c'est un TD/TP mais qu'il n'y a PAS de numéro de groupe dans le titre,
    # on suppose que c'est pour toute la promo de cette matière -> On garde
    return True

def main():
    print(f"📥 Récupération des données depuis {URL_AGENDA}...")
    
    try:
        response = requests.get(URL_AGENDA)
        response.raise_for_status()
        data = response.json()
        
        cal = Calendar()
        count = 0
        ignored = 0

        for item in data:
            if est_pour_cedric(item):
                e = Event()
                e.name = item.get('title', 'Cours')

                # --- AJOUT OPTIMISATION UID ---
                # On crée une signature unique pour ce cours (ex: "2025-01-12T08:00:00_CM_JAVA")
                # Comme ça, si le cours ne bouge pas, l'UID reste le même et Google ne recharge rien.
                id_string = f"{item['start']}_{e.name}"
                # On transforme ça en code unique propre
                e.uid = hashlib.md5(id_string.encode('utf-8')).hexdigest() + "@cedric-agenda"
                # ------------------------------
                e.description = item.get('description', '')
                
                raw_loc = item.get('location', '')
                # ON AJOUTE e.name ICI vvv
                e.location = enrichir_localisation(raw_loc, e.name)
                
                # Gestion Date & Heure (Fuseau Paris)
                try:
                    start = arrow.get(item['start'])
                    end = arrow.get(item['end']) if item.get('end') else start.shift(minutes=90)
                    
                    # Force le fuseau horaire si absent
                    if start.tzinfo is None: start = start.replace(tzinfo='Europe/Paris')
                    if end.tzinfo is None: end = end.replace(tzinfo='Europe/Paris')
                    
                    e.begin = start
                    e.end = end
                    
                    # ====================================================
                    # AJOUT CEDRIC : Forcer "Toute la journée"
                    # ====================================================
                    # Si le titre contient "Interruption", on active le mode All Day
                    if "Interruption" in e.name:
                        e.make_all_day()
                    # ====================================================
                    
                    cal.events.add(e)
                    count += 1
                except Exception as err:
                    print(f"⚠️ Erreur date sur {e.name}: {err}")
            else:
                ignored += 1

        # ====================================================
        # AMÉLIORATION : TRIER PAR DATE
        # ====================================================
        # On trie les événements pour qu'ils soient toujours dans le même ordre dans le fichier.
        # Cela évite que GitHub croie que tout le fichier a changé juste parce que l'ordre a bougé.
        cal.events = sorted(cal.events, key=lambda x: x.begin)
        # ====================================================

        # Sauvegarde
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(cal)
            
        print("="*40)
        print(f"✅ Agenda généré pour CÉDRIC")
        print(f"📅 Cours ajoutés : {count}")
        print(f"🗑️ Cours ignorés : {ignored}")
        print(f"👉 Fichier : {OUTPUT_FILE}")
        print("="*40)

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    main()