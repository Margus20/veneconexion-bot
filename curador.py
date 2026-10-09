import os
import time
import random
import requests
from datetime import datetime

# ============ CONFIGURACIÓN ============
TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = -1004298823500
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# IDs de los hilos (message_thread_id)
HILOS = {
    "general": 1,
    "empleos": 4,
    "cultura": 7,
    "deportes": 3,
    "gastronomia": 9
}

# Palabras clave para clasificar contenido
PALABRAS_CLAVE = {
    "cultura": [
        "música", "arte", "cultura", "historia", "tradición", "folclore",
        "gaita", "joropo", "tamunangue", "pintura", "escultura", "literatura",
        "poesía", "cine", "teatro", "danza", "geografía", "paisaje", "ciudad",
        "pueblo", "turismo", "monumento", "patrimonio", "leyenda", "mito"
    ],
    "deportes": [
        "béisbol", "fútbol", "deporte", "atleta", "juego", "pelota", "LVBP",
        "MLB", "equipos", "campeonato", "medalla", "olímpico", "natación",
        "ciclismo", "boxeo", "voleibol", "baloncesto"
    ],
    "gastronomia": [
        "receta", "comida", "arepa", "hallaca", "cachapa", "cocina", "sabor",
        "plato", "gastronomía", "culinaria", "ingredientes", "sopa", "asado",
        "pescado", "dulce", "postre", "bebida", "café", "cacao"
    ],
    "empleos": [
        "trabajo", "empleo", "contratación", "vacante", "emprendimiento",
        "negocio", "oportunidad", "profesión", "oficio", "empresa", "economía",
        "comercio", "industria"
    ]
}

# Temas para buscar en Wikipedia (organizados por categoría)
TEMAS = {
    "cultura": [
        "Cultura de Venezuela", "Música de Venezuela", "Arte de Venezuela",
        "Historia de Venezuela", "Geografía de Venezuela", "Isla de Margarita",
        "Salto Ángel", "Los Roques", "Mérida (Venezuela)", "Caracas",
        "Joropo", "Gaita zuliana", "Tamunangue", "Diablos Danzantes de Yare",
        "Parque Nacional Canaima", "Parque Nacional Morrocoy",
        "Parque Nacional Henri Pittier", "Roraima", "Gran Sabana",
        "Lago de Maracaibo", "Orinoco", "Ángel Falls",
        "Simón Bolívar", "Francisco de Miranda", "José Antonio Páez",
        "Literatura venezolana", "Rómulo Gallegos", "Teresa Carreño"
    ],
    "deportes": [
        "Béisbol en Venezuela", "Fútbol en Venezuela",
        "Selección de béisbol de Venezuela", "Luis Aparicio",
        "Miguel Cabrera", "Johan Santana", "Félix Hernández",
        "Deporte en Venezuela", "Juegos Bolivarianos",
        "Voleibol en Venezuela", "Baloncesto en Venezuela"
    ],
    "gastronomia": [
        "Gastronomía de Venezuela", "Arepa", "Hallaca", "Cachapa",
        "Pabellón criollo", "Tequeño", "Queso de mano", "Casabe",
        "Chicha venezolana", "Pan de jamón", "Cachito",
        "Dulce de leche", "Papelón con limón", "Mandoca",
        "Sancocho", "Asado negro", "Pescado frito"
    ],
    "empleos": [
        "Emprendimiento en Venezuela", "Economía de Venezuela",
        "Pequeña y mediana empresa", "Comercio electrónico",
        "Turismo en Venezuela", "Agricultura en Venezuela",
        "Industria petrolera en Venezuela"
    ]
}

# Archivo de memoria
VISTOS_FILE = 'vistos.txt'

def cargar_vistos():
    """Carga los temas ya publicados desde el archivo."""
    if os.path.exists(VISTOS_FILE):
        with open(VISTOS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def guardar_visto(tema):
    """Guarda un tema como ya publicado."""
    with open(VISTOS_FILE, 'a', encoding='utf-8') as f:
        f.write(tema + '\n')

def buscar_wikipedia(tema):
    """Busca un artículo en Wikipedia y devuelve título, resumen e imagen."""
    url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get('title', tema)
            resumen = data.get('extract', '')
            imagen = data.get('thumbnail', {}).get('source', '')
            if len(resumen) > 100:
                return titulo, resumen[:300], imagen
    except Exception as e:
        print(f"Error Wikipedia: {e}")
    return None, None, None

def clasificar_tema(tema):
    """Clasifica un tema según palabras clave."""
    tema_lower = tema.lower()
    for categoria, palabras in PALABRAS_CLAVE.items():
        for palabra in palabras:
            if palabra in tema_lower:
                return categoria
    return 'general'

def enviar_mensaje(texto, thread_id, imagen_url=''):
    """Envía un mensaje (con o sin imagen) a un hilo específico."""
    if imagen_url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            img = requests.get(imagen_url, headers=headers, timeout=10).content
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
        except Exception as e:
            print(f"Error al enviar imagen: {e}")
    
    # Si no hay imagen o falló, enviar solo texto
    data = {
        'chat_id': CHAT_ID,
        'message_thread_id': thread_id,
        'text': texto,
        'parse_mode': 'HTML'
    }
    r = requests.post(f"{API_URL}/sendMessage", data=data, timeout=10)
    return r.status_code == 200

def publicar_en_categoria(categoria):
    """Busca y publica contenido de una categoría."""
    vistos = cargar_vistos()
    temas = TEMAS.get(categoria, [])
    
    # Filtrar temas no publicados
    temas_disponibles = [t for t in temas if t not in vistos]
    
    if not temas_disponibles:
        print(f"🔄 Reiniciando lista de {categoria} (todos publicados)")
        # Reiniciar solo esta categoría en el archivo
        with open(VISTOS_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        temas_disponibles = temas
    
    tema = random.choice(temas_disponibles)
    titulo, resumen, imagen = buscar_wikipedia(tema)
    
    if titulo and resumen:
        emojis = {
            'cultura': '',
            'deportes': '⚽',
            'gastronomia': '🍲',
            'empleos': '💼',
            'general': ''
        }
        emoji = emojis.get(categoria, '📌')
        
        texto = f"{emoji} <b>{titulo}</b>\n\n{resumen}\n\n📚 Fuente: Wikipedia"
        thread_id = HILOS.get(categoria, 1)
        
        if enviar_mensaje(texto, thread_id, imagen):
            guardar_visto(tema)
            print(f"✅ [{categoria}] Publicado: {titulo}")
            return True
        else:
            print(f"❌ [{categoria}] Falló al publicar: {titulo}")
            return False
    else:
        print(f"⚠️ [{categoria}] No se encontró info para: {tema}")
        return False

def main():
    print("=" * 50)
    print(" Bot Curador VeneConexión")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    categorias = ['cultura', 'deportes', 'gastronomia', 'empleos', 'general']
    
    for categoria in categorias:
        try:
            publicar_en_categoria(categoria)
            time.sleep(3)  # Pausa para no saturar la API
        except Exception as e:
            print(f"❌ Error en {categoria}: {e}")
    
    print("=" * 50)
    print("✅ Ciclo completado")
    print("=" * 50)

if __name__ == '__main__':
    main()
