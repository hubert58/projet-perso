import requests
import re
import json

# URL du script spécifique au Semestre 6 (trouvé dans ton HTML)
URL_JS_S6 = "https://www.fil.univ-lille.fr/~aubert/l3/script/calendarL3S6.js"
BASE_URL_AGENDA = "https://www.fil.univ-lille.fr/~aubert/l3/agenda/"

def trouver_url_agenda():
    print(f"1. Récupération des paramètres dans : {URL_JS_S6}")
    
    try:
        r = requests.get(URL_JS_S6)
        r.raise_for_status()
        content = r.text
        
        # On cherche la variable prefixCalendar avec une regex
        # ex: this.prefixCalendar='2425-S6-'
        match_prefix = re.search(r"this\.prefixCalendar\s*=\s*['\"]([^'\"]+)['\"]", content)
        prefix = match_prefix.group(1) if match_prefix else ""
        
        # On cherche la liste des calendriers
        # ex: this.allCalendarName=['All','G1',...]
        match_cals = re.search(r"this\.allCalendarName\s*=\s*(\[[^\]]+\])", content)
        calendars = []
        if match_cals:
            # On nettoie un peu le JS pour en faire du JSON valide (remplace ' par ")
            raw_list = match_cals.group(1).replace("'", '"')
            try:
                calendars = json.loads(raw_list)
            except:
                # Si le JSON parsing échoue, on extrait bourrin
                calendars = re.findall(r"['\"](\w+)['\"]", raw_list)
        
        print(f"   -> Préfixe trouvé : {prefix}")
        print(f"   -> Calendriers dispos : {calendars}")
        
        print("\n2. Test des URLs JSON...")
        
        valid_urls = []
        
        # On teste le calendrier 'All' (souvent le général) et le premier trouvé
        for cal_name in calendars:
            # Construction de l'URL selon la logique du fichier JS (mode debug)
            full_url = f"{BASE_URL_AGENDA}{prefix}{cal_name}.json"
            
            print(f"   Test de : {full_url} ... ", end="")
            try:
                test = requests.head(full_url)
                if test.status_code == 200:
                    print("✅ VALIDE !")
                    valid_urls.append(full_url)
                else:
                    print(f"❌ (Code {test.status_code})")
            except:
                print("❌ Erreur connexion")

        if valid_urls:
            print("\n" + "="*40)
            print("🚀 VICTOIRE ! Voici les URLs à utiliser dans ton script final :")
            for u in valid_urls:
                print(f"URL_JSON_SOURCE = '{u}'")
            print("="*40)
            return valid_urls[0] # Retourne la première trouvée pour enchainer
        else:
            print("❌ Aucune URL valide trouvée. Vérifier le dossier agenda.")
            return None

    except Exception as e:
        print(f"Erreur globale : {e}")
        return None

# Lancer la recherche
url_trouvee = trouver_url_agenda()