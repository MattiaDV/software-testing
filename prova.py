import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import csv
from selenium.webdriver.common.keys import Keys

# Configura il driver
def configure_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")  # Nascondi automazione
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")  # Opzionale: usa una porta diversa per il debug remoto
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    return driver

# Funzione per accettare i cookie
def accept_cookies(driver):
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'))
        )
        cookie_button.click()
        print("Cookie accettati.")
    except:
        print("Nessun banner dei cookie trovato.")

# Funzione per raccogliere i link delle esperienze
def collect_experience_links(driver):
    try:
        # Trova le card delle esperienze
        cards = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.vertical-activity-card__content-wrapper'))
        )
        links = [card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') for card in cards]
        print(f"Link delle esperienze trovati: {links}")
        return links
    except Exception as e:
        print(f"Errore nel trovare le card: {e}")
        return []

# Funzione per raccogliere le informazioni legali (ragione sociale, indirizzo e partita IVA)
# tore
def find_supplier_link(driver):
    try:
        supplier_selector = [
            'a.supplier-name__link.adp__link',  # Selettore originale
            'a[href*="supplier"]',             # Alternativo basato su href
        ]
        supplier_link = None
        for selector in supplier_selector:
            try:
                supplier_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                supplier_link = supplier_element.get_attribute('href')
                if supplier_link:
                    break
            except:
                pass

        return supplier_link
    except Exception as e:
        print(f"Errore nel trovare il link del fornitore: {e}")
        return None

# Funzione per raccogliere il titolo e i dettagli
def collect_supplier_info(driver):
    dati = {
        'titolo': 'Non disponibile',  # Campo per il titolo
        'info': ''                    # Campo unico per i dettagli concatenati
    }
    try:
        # Trova il titolo nella pagina del fornitore
        try:
            titolo_element = driver.find_element(By.CSS_SELECTOR, 'h1.supplier__header-title')
            dati['titolo'] = titolo_element.text.strip()
        except:
            print("Titolo non trovato.")
        
        # Trova i dettagli generici (elementi <li>)
        try:
            legal_items = driver.find_elements(By.CSS_SELECTOR, 'ul.legal-notice__items > li')
            dettagli = [item.text.strip() for item in legal_items if item.text.strip()]
            dati['info'] = ' | '.join(dettagli)  # Concatena i dettagli separati da '|'
        except Exception as e:
            print(f"Errore nel raccogliere i dettagli: {e}")
    
    except Exception as e:
        print(f"Errore nel raccogliere le informazioni del fornitore: {e}")
    
    return dati

# Scrivere i dati nel file CSV (Titolo + Info)
def write_data_to_csv(nazione, dati):
    try:
        with open('provider_data.csv', 'r', encoding='utf-8') as file:
            file_contents = file.readlines()
    except FileNotFoundError:
        file_contents = []

    with open('provider_data.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_contents or not any(f"Nazione: {nazione}" in line for line in file_contents):
            writer.writerow([f"Nazione: {nazione}"])
            writer.writerow([])

        # Scrive il titolo e le info in un'unica riga
        writer.writerow([f"Titolo: {dati.get('titolo', 'Non disponibile')}"])
        writer.writerow([f"Info: {dati.get('info', 'Non disponibile')}"])
        writer.writerow([])  # Linea vuota per separare i provider

# Modifica principale nel loop per raccogliere Titolo + Info
driver = configure_driver()

try:
    # Apri la pagina principale
    url = "https://www.getyourguide.com/"
    driver.get(url)
    time.sleep(random.uniform(2, 4))  # Attendi caricamento
    accept_cookies(driver)

    # Nazioni da ricercare
    nazioni = ["Italia", "Finlandia", "Francia"]

    # Per ogni nazione, cerca i dati
    for nazione in nazioni:
        try:
            # Ricerca la nazione
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input.c-input__field'))
            )
            search_box.clear()  # Pulisce la barra di ricerca
            search_box.send_keys(nazione)  # Inserisci il nome della nazione
            search_box.send_keys(Keys.RETURN)  # Premere INVIO per avviare la ricerca

            time.sleep(3)  # Attendere che la pagina si carichi

            # Raccogli i link delle esperienze per la nazione
            links = collect_experience_links(driver)

            # Visita ogni link delle esperienze
            for link in links:
                try:
                    driver.get(link)
                    accept_cookies(driver)

                    # Trova il link del fornitore
                    supplier_link = find_supplier_link(driver)

                    if supplier_link:
                        print(f"Link del fornitore trovato: {supplier_link}")

                        # Visita la pagina del fornitore
                        driver.get(supplier_link)

                        # Raccogli le informazioni aziendali
                        dati = collect_supplier_info(driver)

                        # Scrivi i dati nel file CSV
                        write_data_to_csv(nazione, dati)

                    else:
                        print("Nessun link del fornitore trovato.")
                except Exception as e:
                    print(f"Errore con il link {link}: {e}")

        except Exception as e:
            print(f"Errore nella ricerca per {nazione}: {e}")

except Exception as e:
    print(f"Errore nello script principale: {e}")

finally:
    driver.quit()
