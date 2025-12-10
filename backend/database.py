import sqlite3
import os
import pandas as pd

DB_PATH = 'data/crm.db'
DATA_DIR = 'data'


def get_connection():
    """Obtiene conexion a SQLite."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT,
            whatsapp TEXT,
            carga_trabajo INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direccion TEXT NOT NULL,
            tipo TEXT,
            precio INTEGER,
            agente_id INTEGER,
            FOREIGN KEY (agente_id) REFERENCES agentes(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            propiedad_id INTEGER,
            estado TEXT DEFAULT 'Asignado',
            agente_asignado_id INTEGER,
            FOREIGN KEY (propiedad_id) REFERENCES propiedades(id),
            FOREIGN KEY (agente_asignado_id) REFERENCES agentes(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contacto_id INTEGER NOT NULL,
            agente_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            botones TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            respondido INTEGER DEFAULT 0,
            respuesta TEXT,
            FOREIGN KEY (contacto_id) REFERENCES contactos(id),
            FOREIGN KEY (agente_id) REFERENCES agentes(id)
        )
    ''')

    conn.commit()
    conn.close()


def migrate_from_csv():
    """Migra datos existentes de CSV a SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si ya hay datos
    cursor.execute('SELECT COUNT(*) FROM agentes')
    if cursor.fetchone()[0] > 0:
        print("Base de datos ya tiene datos, saltando migracion")
        conn.close()
        return

    # Migrar agentes
    agentes_csv = os.path.join(DATA_DIR, 'agentes.csv')
    if os.path.exists(agentes_csv):
        df = pd.read_csv(agentes_csv)
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO agentes (id, nombre, email, whatsapp, carga_trabajo)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['id'], row['nombre'], row['email'], row['whatsapp'], row.get('carga_trabajo', 0)))
        print(f"Migrados {len(df)} agentes")

    # Migrar propiedades
    propiedades_csv = os.path.join(DATA_DIR, 'propiedades.csv')
    if os.path.exists(propiedades_csv):
        df = pd.read_csv(propiedades_csv)
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO propiedades (id, direccion, tipo, precio, agente_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['id'], row['direccion'], row['tipo'], row['precio'], row['agente_id']))
        print(f"Migradas {len(df)} propiedades")

    # Migrar contactos
    contactos_csv = os.path.join(DATA_DIR, 'contactos.csv')
    if os.path.exists(contactos_csv):
        df = pd.read_csv(contactos_csv)
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO contactos (id, nombre, telefono, fecha, propiedad_id, estado, agente_asignado_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['id'], row['nombre'], row['telefono'], row['fecha'],
                  row.get('propiedad_id'), row['estado'], row.get('agente_asignado_id')))
        print(f"Migrados {len(df)} contactos")

    # Migrar mensajes si existen
    mensajes_csv = os.path.join(DATA_DIR, 'mensajes.csv')
    if os.path.exists(mensajes_csv):
        df = pd.read_csv(mensajes_csv)
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO mensajes (id, contacto_id, agente_id, tipo, contenido, botones, fecha, respondido, respuesta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row['id'], row['contacto_id'], row['agente_id'], row['tipo'],
                  row['contenido'], row.get('botones'), row['fecha'],
                  1 if row.get('respondido') else 0, row.get('respuesta')))
        print(f"Migrados {len(df)} mensajes")

    conn.commit()
    conn.close()
    print("Migracion completada")


# Funciones de acceso a datos

def get_agentes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agentes')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_agente(agente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agentes WHERE id = ?', (agente_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_propiedades():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM propiedades')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_propiedad(propiedad_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM propiedades WHERE id = ?', (propiedad_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_contactos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contactos ORDER BY fecha DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_contacto(contacto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contactos WHERE id = ?', (contacto_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def crear_contacto(nombre, telefono, propiedad_id, agente_id, estado='Asignado'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contactos (nombre, telefono, propiedad_id, agente_asignado_id, estado)
        VALUES (?, ?, ?, ?, ?)
    ''', (nombre, telefono, propiedad_id, agente_id, estado))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_contacto(nuevo_id)


def actualizar_estado_contacto(contacto_id, nuevo_estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE contactos SET estado = ? WHERE id = ?', (nuevo_estado, contacto_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_mensajes_agente(agente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mensajes WHERE agente_id = ? ORDER BY fecha ASC', (agente_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def crear_mensaje(contacto_id, agente_id, tipo, contenido, botones=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mensajes (contacto_id, agente_id, tipo, contenido, botones)
        VALUES (?, ?, ?, ?, ?)
    ''', (contacto_id, agente_id, tipo, contenido, botones))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return nuevo_id


def responder_mensaje(mensaje_id, respuesta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE mensajes SET respondido = 1, respuesta = ? WHERE id = ?', (respuesta, mensaje_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_metricas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM contactos')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT estado, COUNT(*) FROM contactos GROUP BY estado')
    por_estado = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute('''
        SELECT a.nombre, COUNT(c.id) as count
        FROM agentes a
        LEFT JOIN contactos c ON a.id = c.agente_asignado_id
        GROUP BY a.id
        ORDER BY count DESC
        LIMIT 5
    ''')
    top_agentes = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        'total_contactos': total,
        'por_estado': por_estado,
        'top_agentes': top_agentes
    }


def contar_contactos_agente(agente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM contactos WHERE agente_asignado_id = ?', (agente_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_agente_menos_carga():
    """Retorna el agente con menos contactos asignados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, COUNT(c.id) as carga
        FROM agentes a
        LEFT JOIN contactos c ON a.id = c.agente_asignado_id
        GROUP BY a.id
        ORDER BY carga ASC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


if __name__ == '__main__':
    init_db()
    migrate_from_csv()
