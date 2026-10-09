import os
import time
import random
import requests
from datetime import datetime

# ============ CONFIGURACIÓN ============
TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = -1004298823500
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# IDs de los hilos
HILOS = {
    "general": 1,
    "empleos": 4,
    "cultura": 7,
    "deportes": 3,
    "gastronomia": 9
}

# Headers para Wikipedia
WIKI_HEADERS = {
    'User-Agent': 'VeneConexionBot/1.0 (marcosvargas@example.com) Python/3.10'
}

# Temas para buscar en Wikipedia
TEMAS = {
    "cultura": [
        "Cultura de Venezuela",
        "Música de Venezuela",
        "Arte de Venezuela",
        "Historia de Venezuela",
        "Isla de Margarita",
        "Salto Ángel",
        "Los Roques",
        "Mérida",
        "Caracas",
        "Joropo",
        "Gaita zuliana",
        "Diablos Danzantes",
        "Canaima",
        "Morrocoy",
        "Roraima",
        "Gran Sabana",
        "Lago de Maracaibo",
        "Orinoco",
        "Simón Bolívar",
        "Francisco de Miranda",
        "Rómulo Gallegos",
        "Teresa Carreño"
    ],
    "deportes": [
        "Béisbol",
        "Fútbol",
        "Luis Aparicio",
        "Miguel Cabrera",
        "Johan Santana",
        "Félix Hernández",
        "Voleibol",
        "Baloncesto"
    ],
    "gastronomia": [
        "Gastronomía de Venezuela",
        "Arepa",
        "Hallaca",
        "Cachapa",
        "Pabellón criollo",
        "Tequeño",
        "Queso de mano",
        "Casabe",
        "Chicha",
        "Pan de jamón",
        "Papelón",
        "Sancocho",
        "Asado negro"
    ],
    "empleos": [
        "Emprendimiento",
        "Economía",
        "Pequeña y mediana empresa",
        "Comercio electrónico",
        "Turismo",
        "Agricultura",
        "Petróleo"
    ],
    "general": [
        "Venezuela",
        "Bandera de Venezuela",
        "Himno Nacional de Venezuela",
        "Escudo de armas de Venezuela",
        "Geografía de Venezuela",
        "Clima",
        "Demografía"
    ]
}

VISTOS_FILE = 'vistos.txt'

def cargar_vistos():
    if os.path.exists(VISTOS_FILE):
        with open(VISTOS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def guardar_visto(tema):
    with open(VISTOS_FILE, 'a', encoding='utf-8') as f:
        f.write(tema + '\n')

def buscar_wikipedia(tema):
    """Busca en Wikipedia usando la API de búsqueda."""
    # Primero buscar el artículo
    search_url = f"https://es.wikipedia.org/w/api.php"
    search_params = {
        'action': 'query',
        'list': 'search',
        'srsearch': tema,
        'srlimit': 1,
        'format': 'json'
    }
    
    try:
        resp = requests.get(search_url, params=search_params, headers=WIKI_HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('query', {}).get('search', [])
            
            if results:
                titulo = results[0]['title']
                
                # Ahora obtener el resumen
                summary_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{titulo.replace(' ', '_')}"
                summary_resp = requests.get(summary_url, headers=WIKI_HEADERS, timeout=10)
                
                if summary_resp.status_code == 200:
                    summary_data = summary_resp.json()
                    resumen = summary_data.get('extract', '')
                    imagen = summary_data.get('thumbnail', {}).get('source', '')
                    
                    if len(resumen) > 50:
                        return titulo, resumen[:400], imagen
                    else:
                        print(f"   ⚠️ Resumen muy corto para {titulo}")
    except Exception as e:
        print(f"   ❌ Error Wikipedia: {e}")
    
    return None, None, None

def enviar_mensaje(texto, thread_id, imagen_url=''):
    if imagen_url:
        try:
            img = requests.get(imagen_url, headers=WIKI_HEADERS, timeout=10).content
            files = {'photo': ('img.jpg', img, 'image/jpeg')}
            data = {
                'chat_id': CHAT_ID,
                'message_thread_id': thread_id,
                'caption': texto,
                'parse_mode': 'HTML'
            }
            r = requests.post(f"{API_URL}/sendPhoto", files=files, data=data, timeout=20)
            if r.status_code == 200:
                return True
            else:
                print(f"   ⚠️ Error imagen: {r.status_code}")
        except Exception as e:
            print(f"   ⚠️ Error imagen: {e}")
    
    data = {
        'chat_id': CHAT_ID,
        'message_thread_id': thread_id,
        'text': texto,
        'parse_mode': 'HTML'
    }
    r = requests.post(f"{API_URL}/sendMessage", data=data, timeout=10)
    if r.status_code == 200:
        return True
    else:
        print(f"   ❌ Error Telegram: {r.status_code}")
        return False

def publicar_en_categoria(categoria):
    vistos = cargar_vistos()
    temas = TEMAS.get(categoria, [])
    
    if not temas:
        print(f"   ⚠️ No hay temas para {categoria}")
        return False
    
    temas_disponibles = [t for t in temas if t not in vistos]
    
    if not temas_disponibles:
        print(f"   🔄 Reiniciando lista de {categoria}")
        with open(VISTOS_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        temas_disponibles = temas[:]
    
    for intento in range(min(3, len(temas_disponibles))):
        tema = random.choice(temas_disponibles)
        print(f"   🔍 Buscando: {tema}")
        
        titulo, resumen, imagen = buscar_wikipedia(tema)
        
        if titulo and resumen:
            emojis = {
                'cultura': '',
                'deportes': '⚽',
                'gastronomia': '🍲',
                'empleos': '💼',
                'general': '🇻'
            }
            emoji = emojis.get(categoria, '📌')
            texto = f"{emoji} <b>{titulo}</b>\n\n{resumen}\n\n📚 Fuente: Wikipedia"
            thread_id = HILOS.get(categoria, 1)
            
            if enviar_mensaje(texto, thread_id, imagen):
                guardar_visto(tema)
                print(f"   ✅ Publicado: {titulo}")
                return True
            else:
                print(f"   ❌ Falló envío: {titulo}")
                temas_disponibles.remove(tema)
        else:
            print(f"   ⚠️ Sin info: {tema}")
            temas_disponibles.remove(tema)
    
    return False

def main():
    print("=" * 50)
    print(" Bot Curador VeneConexión")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    categorias = ['cultura', 'deportes', 'gastronomia', 'empleos', 'general']
    
    for categoria in categorias:
        print(f"\n📂 Categoría: {categoria}")
        try:
            publicar_en_categoria(categoria)
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ Error en {categoria}: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Ciclo completado")
    print("=" * 50)

if __name__ == '__main__':
    main()
