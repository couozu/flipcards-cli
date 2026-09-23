import sqlite3
DB_FILE = "vocab.db"

ARTICLES = {
    "problema": "el", "hombre": "el", "disparo": "el", "charco": "el",
    "ojo": "el", "atraco": "el", "trabajo": "el", "segurata": "el",
    "ladrón": "el", "asesino": "el", "día": "el", "año": "el",
    "viejecito": "el", "cuerpo": "el", "alma": "el", "tono": "el",
    "tiempo": "el", "teléfono": "el", "niño": "el", "cariño": "el",
    "viaje": "el", "barco": "el", "chino": "el", "cocinero": "el",
    "billete": "el", "cementerio": "el", "mercado": "el", "matadero": "el",
    "ángel": "el", "guarda": "el", "minuto": "el", "plato": "el",
    "momento": "el", "camino": "el", "equipo": "el", "coche": "el",
    "profesor": "el", "culo": "el", "furgón": "el", "campo": "el",
    "diamante": "el", "tiburón": "el", "jefe": "el", "mando": "el",
    "asalto": "el", "tosido": "el", "amor": "el", "negocio": "el",
    "palo": "el", "periódico": "el", "ruido": "el", "mes": "el",
    "golpe": "el", "sueldo": "el", "caso": "el", "nombre": "el",
    "número": "el", "planeta": "el", "rollo": "el", "señor": "el",
    "registro": "el", "DNI": "el", "efecto": "el", "fantasma": "el",
    "dinero": "el", "héroe": "el", "cuidado": "el", "timbre": "el",
    "miedo": "el", "atracador": "el", "zombi": "el", "esqueleto": "el",
    "bigote": "el", "pintor": "el", "cojón": "el", "muñeco": "el",
    "ratón": "el", "guantazo": "el", "lado": "el", "crío": "el",
    "papa": "el", "santo": "el", "frenazo": "el", "zapato": "el",
    "segundo": "el", "artefacto": "el", "arsenal": "el", "camión": "el",
    "edificio": "el", "papel": "el", "fusil": "el", "cuello": "el",
    "valor": "el", "heroísmo": "el", "precio": "el", "uniforme": "el",
    "camionero": "el", "cambio": "el", "caos": "el", "chico": "el",
    "cordero": "el", "culatazo": "el", "error": "el", "favor": "el",
    "macho": "el", "matrimonio": "el", "mensaje": "el", "móvil": "el",
    "museo": "el", "riñón": "el", "vestíbulo": "el", "poquito": "el",
    "llanto": "el", "pin": "el", "ahogo": "el", "crack": "el",
    "lujo": "el", "metal": "el", "monstruo": "el", "paso": "el",
    "salvoconducto": "el", "asado": "el", "papá": "el", "talego": "el",
    "currículum": "el", "sitio": "el", "cerebro": "el", "remedio": "el",
    "don": "el", "sistema": "el", "Oscar": "el", "idioma": "el",
    "limbo": "el", "tío": "el", "compromiso": "el", "anillo": "el",
    "pedruscazo": "el", "principio": "el", "agente": "el", "apoyo": "el",
    "corazón": "el", "fuego": "el", "suelo": "el", "trueno": "el",
    "sonido": "el", "ordenador": "el", "plan": "el", "resto": "el",
    "rey": "el", "chaleco": "el", "cine": "el", "bocajarro": "el",
    "diente": "el", "divorcio": "el", "granito": "el", "grito": "el",
    "mármol": "el", "sollozo": "el", "rehén": "el", "trasero": "el",
    "payo": "el", "Río": "el", "siamés": "el", "soldado": "el",
    "mujer": "la", "historia": "la", "vez": "la", "sangre": "la",
    "profesión": "la", "manera": "la", "foto": "la", "comisaría": "la",
    "cámara": "la", "llamada": "la", "cosa": "la", "realidad": "la",
    "mamá": "la", "noticia": "la", "tortilla": "la", "tontería": "la",
    "calle": "la", "ciencia": "la", "ventaja": "la", "gente": "la",
    "policía": "la", "pistola": "la", "pelota": "la", "relación": "la",
    "casa": "la", "madre": "la", "opinión": "la", "parte": "la",
    "víctima": "la", "fábrica": "la", "moneda": "la", "careta": "la",
    "peli": "la", "muerte": "la", "arma": "la", "mano": "la",
    "oreja": "la", "razón": "la", "punta": "la", "peña": "la",
    "carnicería": "la", "banda": "la", "boda": "la", "décima": "la",
    "tonelada": "la", "bobina": "la", "cocina": "la", "sirena": "la",
    "posibilidad": "la", "radio": "la", "telefonía": "la",
    "cabeza": "la", "puerta": "la", "hija": "la", "marca": "la",
    "agua": "la", "clase": "la", "fachada": "la", "mitad": "la",
    "niña": "la", "noche": "la", "rueda": "la", "tranquilidad": "la",
    "voz": "la", "profesora": "la", "acreditación": "la",
    "visita": "la", "respiración": "la", "izquierda": "la",
    "pareja": "la", "fecundación": "la", "fertilidad": "la",
    "pensión": "la", "prueba": "la", "paternidad": "la",
    "escalera": "la", "idea": "la", "sensación": "la",
    "persona": "la", "forma": "la", "disculpa": "la",
    "cara": "la", "boca": "la", "frente": "la", "pieza": "la",
    "cama": "la", "cárcel": "la", "suerte": "la", "cafetería": "la",
    "interpretación": "la", "comunicación": "la",
    "radiofrecuencia": "la", "paz": "la", "tormenta": "la",
    "corriente": "la", "mañana": "la", "edad": "la",
    "carretilla": "la", "chapa": "la", "pedida": "la",
    "película": "la", "seguridad": "la", "bolsa": "la",
    "cuenta": "la", "emisora": "la", "bala": "la",
    "milésima": "la", "rata": "la", "velocidad": "la",
    "puta": "la", "risa": "la", "oferta": "la", "gracia": "la",
    "bienvenida": "la", "mierda": "la", "pregunta": "la",
    "ciudad": "la", "señorita": "la", "rima": "la",
    "busca": "la", "captura": "la", "joyería": "la",
    "subasta": "la", "piscina": "la", "mina": "la",
    "peletería": "la", "relojería": "la", "caja": "la",
    "lanza": "la", "herramienta": "la", "droga": "la",
    "costilla": "la", "pelea": "la", "discoteca": "la",
    "bomba": "la", "debilidad": "la", "alarma": "la",
    "electrónica": "la", "falta": "la", "calidad": "la",
    "familia": "la", "gota": "la", "semana": "la",
    "vida": "la", "diosa": "la", "central": "la",
}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

updated = 0
for word, article in ARTICLES.items():
    # Force update regardless of current value
    c.execute("UPDATE words SET article = ? WHERE word = ?", (article, word))
    updated += c.rowcount

conn.commit()

c.execute("SELECT word, article FROM words WHERE word = 'problema'")
print("problema check:", c.fetchone())

c.execute("SELECT count(*) FROM words WHERE article != '' AND is_ignored = 0")
print(f"Total words with articles: {c.fetchone()[0]}")

conn.close()
print(f"Done! Updated {updated} rows")
