from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

# Configura aquí tu búsqueda
SEARCH_URL = "https://www.idealista.com/areas/alquiler-habitacion/con-precio-hasta_450,sexo_chico/?shape=%28%28qaegGjrbQq%40oc%40%60m%40g%7BAfp%40ucAzBc%5E%60f%40en%40vc%40vdAyFbhBqr%40iCuUn%60AkzAtf%40%29%29"  # cambia a tu búsqueda
DATA_FILE = "anuncios_guardados.json"

# Configura el correo
EMAIL_SENDER = "iraitzmate@gmail.com"
EMAIL_PASSWORD = os.environ.get("MY_SECRET_PASSWORD")
EMAIL_RECEIVER = "iraitzazka@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def extraer_anuncios(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")  # Reduce el ruido en la consola
    options.add_argument("--headless")  # quitar esto si quieres ver el navegador
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)

    try:
        # Espera hasta que aparezca el botón de cookies (máx 10 segundos)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceptar')]"))
        ).click()
        print("✅ Cookies aceptadas.")
    except Exception:
        print("⚠️ No se encontró el banner de cookies o ya estaba aceptado.")

    time.sleep(5)  # deja que cargue JS

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    anuncios = []
    for item in soup.select("article.item"):
        titulo_elem = item.select_one("a.item-link")
        precio_elem = item.select_one("span.item-price")
        if titulo_elem and precio_elem:
            link = "https://www.idealista.com" + titulo_elem.get("href")

        if titulo_elem and precio_elem and link:
            anuncios.append({
                "titulo": titulo_elem.get_text(strip=True),
                "precio": precio_elem.get_text(strip=True),
                "link": link
            })

    return anuncios

def cargar_anuncios_guardados():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_anuncios(anuncios):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(anuncios, f, ensure_ascii=False, indent=2)

def detectar_nuevos_anuncios(nuevos, antiguos):
    antiguos_titulos = {a["titulo"] for a in antiguos}
    return [a for a in nuevos if a["titulo"] not in antiguos_titulos]

def enviar_email(anuncios_nuevos):
    cuerpo = "Nuevos anuncios en Idealista:\n\n"
    for a in anuncios_nuevos:
        cuerpo += f"{a['titulo']} - {a['precio']}\n{a['link']}\n\n"

    msg = MIMEText(cuerpo)
    msg["Subject"] = "Nuevas ofertas de alquiler en Idealista"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Correo enviado con nuevas ofertas.")
    except Exception as e:
        print(f"Error al enviar email: {e}")

def main():
    anuncios_actuales = extraer_anuncios(SEARCH_URL)
    print(f"Anuncios extraídos: {len(anuncios_actuales)}")
    anuncios_anteriores = cargar_anuncios_guardados()
    print(f"Anuncios guardados previamente: {len(anuncios_anteriores)}")
    nuevos = detectar_nuevos_anuncios(anuncios_actuales, anuncios_anteriores)
    print(f"Nuevos anuncios detectados: {len(nuevos)}")
    if nuevos:
        enviar_email(nuevos)
        guardar_anuncios(anuncios_actuales)
    else:
        print("Sin novedades.")
        # mensaje = [{'titulo': 'No hay novedades', 'precio': '', 'link': ''}]
        # enviar_email(mensaje)

if __name__ == "__main__":
    main()
