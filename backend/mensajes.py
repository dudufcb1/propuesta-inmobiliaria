import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = 'data'

# Estados del lead en el flujo de seguimiento
ESTADOS_LEAD = {
    'nuevo': 'Nuevo',
    'asignado': 'Asignado',
    'confirmado': 'Confirmado',
    'contactado': 'Contactado',
    'en_negociacion': 'En Negociacion',
    'cerrado': 'Cerrado',
    'perdido': 'Perdido'
}

# Tipos de mensaje del sistema
TIPO_MENSAJE = {
    'nuevo_lead': 'nuevo_lead',
    'recordatorio_confirmacion': 'recordatorio_confirmacion',
    'pedir_contacto': 'pedir_contacto',
    'seguimiento': 'seguimiento',
    'felicitacion': 'felicitacion',
    'alerta_sin_respuesta': 'alerta_sin_respuesta'
}

# Botones disponibles segun el tipo de mensaje
BOTONES_POR_MENSAJE = {
    'nuevo_lead': [
        {'id': 'recibido', 'label': 'Recibido', 'accion': 'confirmar_recepcion'},
        {'id': 'rechazar', 'label': 'Rechazar', 'accion': 'rechazar_lead'}
    ],
    'recordatorio_confirmacion': [
        {'id': 'recibido', 'label': 'Recibido', 'accion': 'confirmar_recepcion'},
        {'id': 'rechazar', 'label': 'Rechazar', 'accion': 'rechazar_lead'}
    ],
    'pedir_contacto': [
        {'id': 'si_contacte', 'label': 'Si, contacte', 'accion': 'marcar_contactado'},
        {'id': 'no_pude', 'label': 'No pude', 'accion': 'no_pudo_contactar'},
        {'id': 'no_contesta', 'label': 'No contesta', 'accion': 'cliente_no_contesta'}
    ],
    'seguimiento': [
        {'id': 'en_negociacion', 'label': 'En negociacion', 'accion': 'marcar_negociacion'},
        {'id': 'cerrado', 'label': 'Cerrado', 'accion': 'marcar_cerrado'},
        {'id': 'perdido', 'label': 'Perdido', 'accion': 'marcar_perdido'}
    ],
    'felicitacion': [],
    'alerta_sin_respuesta': [
        {'id': 'recibido', 'label': 'Recibido', 'accion': 'confirmar_recepcion'}
    ]
}

# Tiempos de espera (en minutos para demo, en produccion serian horas/dias)
TIEMPOS = {
    'espera_confirmacion': 5,      # 5 min para demo (produccion: 30 min)
    'espera_contacto': 10,         # 10 min para demo (produccion: 24 horas)
    'seguimiento_negociacion': 15  # 15 min para demo (produccion: 3 dias)
}


def cargar_mensajes():
    path = os.path.join(DATA_DIR, 'mensajes.csv')
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=[
        'id', 'contacto_id', 'agente_id', 'tipo', 'contenido',
        'botones', 'fecha', 'respondido', 'respuesta'
    ])


def guardar_mensajes(df):
    df.to_csv(os.path.join(DATA_DIR, 'mensajes.csv'), index=False)


def crear_mensaje(contacto_id, agente_id, tipo, contenido):
    """Crea un nuevo mensaje del sistema para un agente."""
    mensajes = cargar_mensajes()

    nuevo_id = 1
    if not mensajes.empty:
        nuevo_id = int(mensajes['id'].max()) + 1

    botones = BOTONES_POR_MENSAJE.get(tipo, [])

    nuevo_msg = {
        'id': nuevo_id,
        'contacto_id': contacto_id,
        'agente_id': agente_id,
        'tipo': tipo,
        'contenido': contenido,
        'botones': str(botones),
        'fecha': datetime.now().isoformat(),
        'respondido': False,
        'respuesta': None
    }

    mensajes = pd.concat([mensajes, pd.DataFrame([nuevo_msg])], ignore_index=True)
    guardar_mensajes(mensajes)
    return nuevo_msg


def obtener_mensajes_agente(agente_id):
    """Obtiene todos los mensajes de un agente ordenados por fecha."""
    mensajes = cargar_mensajes()
    if mensajes.empty:
        return []

    msgs_agente = mensajes[mensajes['agente_id'] == agente_id].copy()
    msgs_agente = msgs_agente.sort_values('fecha', ascending=True)

    resultado = []
    for _, row in msgs_agente.iterrows():
        msg = row.to_dict()
        # Convertir string de botones a lista
        try:
            msg['botones'] = eval(row['botones']) if row['botones'] else []
        except:
            msg['botones'] = []
        resultado.append(msg)

    return resultado


def responder_mensaje(mensaje_id, respuesta):
    """Marca un mensaje como respondido."""
    mensajes = cargar_mensajes()
    idx = mensajes[mensajes['id'] == mensaje_id].index
    if len(idx) > 0:
        mensajes.at[idx[0], 'respondido'] = True
        mensajes.at[idx[0], 'respuesta'] = respuesta
        guardar_mensajes(mensajes)
        return True
    return False


def generar_mensaje_nuevo_lead(contacto, agente, propiedad=None):
    """Genera el mensaje inicial cuando se asigna un lead."""
    prop_info = ""
    if propiedad is not None:
        prop_info = f"\nInteresado en: {propiedad['tipo']} - {propiedad['direccion']}"

    contenido = f"Nuevo lead asignado: {contacto['nombre']} ({contacto['telefono']}){prop_info}"

    return crear_mensaje(
        contacto_id=contacto['id'],
        agente_id=agente['id'],
        tipo='nuevo_lead',
        contenido=contenido
    )


def generar_recordatorio_confirmacion(contacto, agente):
    """Genera recordatorio si el agente no confirmo recepcion."""
    contenido = f"Recordatorio: Tienes un lead pendiente de confirmar: {contacto['nombre']} ({contacto['telefono']})"

    return crear_mensaje(
        contacto_id=contacto['id'],
        agente_id=agente['id'],
        tipo='recordatorio_confirmacion',
        contenido=contenido
    )


def generar_pedir_contacto(contacto, agente):
    """Pregunta al agente si ya contacto al cliente."""
    contenido = f"¿Pudiste contactar a {contacto['nombre']}?"

    return crear_mensaje(
        contacto_id=contacto['id'],
        agente_id=agente['id'],
        tipo='pedir_contacto',
        contenido=contenido
    )


def generar_seguimiento(contacto, agente):
    """Pide actualizacion del estado de la negociacion."""
    contenido = f"¿Como va la gestion con {contacto['nombre']}?"

    return crear_mensaje(
        contacto_id=contacto['id'],
        agente_id=agente['id'],
        tipo='seguimiento',
        contenido=contenido
    )


def generar_felicitacion(contacto, agente):
    """Felicita al agente por cerrar un lead."""
    contenido = f"Felicitaciones! Lead {contacto['nombre']} marcado como cerrado."

    return crear_mensaje(
        contacto_id=contacto['id'],
        agente_id=agente['id'],
        tipo='felicitacion',
        contenido=contenido
    )
