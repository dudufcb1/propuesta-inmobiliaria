import pandas as pd
import os
import mensajes as msg_module

DATA_DIR = 'data'

def cargar_datos():
    agentes = pd.read_csv(os.path.join(DATA_DIR, 'agentes.csv'))
    propiedades = pd.read_csv(os.path.join(DATA_DIR, 'propiedades.csv'))

    # Cargar contactos si existe, si no crear dataframe vacio
    contactos_path = os.path.join(DATA_DIR, 'contactos.csv')
    if os.path.exists(contactos_path):
        contactos = pd.read_csv(contactos_path)
    else:
        contactos = pd.DataFrame(columns=['id', 'nombre', 'telefono', 'fecha', 'propiedad_id', 'estado', 'agente_asignado_id'])

    return agentes, propiedades, contactos

def guardar_contactos(df_contactos):
    df_contactos.to_csv(os.path.join(DATA_DIR, 'contactos.csv'), index=False)

def asignar_agente_round_robin(agentes, contactos):
    """
    Asigna al agente con menos carga de contactos.
    """
    conteo = contactos['agente_asignado_id'].value_counts()
    todos_agentes_ids = agentes['id'].tolist()

    for ag_id in todos_agentes_ids:
        if ag_id not in conteo.index:
            return ag_id

    return int(conteo.idxmin())


def asignar_agente(nuevo_contacto_dict):
    """
    Asigna un agente a un nuevo contacto.

    Modos de asignacion (campo 'modo_asignacion'):
    - 'propiedad': Asigna al agente de la propiedad (default si hay propiedad)
    - 'round_robin': Asigna al agente con menos carga
    - 'manual': Usa el agente_id especificado en el campo 'agente_manual_id'

    Si no hay propiedad y no se especifica modo, usa round_robin.
    """
    agentes, propiedades, contactos = cargar_datos()

    agente_asignado_id = None
    modo = nuevo_contacto_dict.get('modo_asignacion', 'auto')

    # Modo manual: asignar a agente especifico
    if modo == 'manual':
        agente_manual_id = nuevo_contacto_dict.get('agente_manual_id')
        if agente_manual_id and agente_manual_id in agentes['id'].values:
            agente_asignado_id = int(agente_manual_id)

    # Modo round_robin forzado
    elif modo == 'round_robin':
        agente_asignado_id = asignar_agente_round_robin(agentes, contactos)

    # Modo auto o propiedad: primero intenta por propiedad, sino round_robin
    else:
        propiedad_id = nuevo_contacto_dict.get('propiedad_id')
        if propiedad_id:
            propiedad = propiedades[propiedades['id'] == int(propiedad_id)]
            if not propiedad.empty:
                agente_asignado_id = propiedad.iloc[0]['agente_id']

        # Fallback a round_robin si no hay propiedad
        if agente_asignado_id is None:
            agente_asignado_id = asignar_agente_round_robin(agentes, contactos)

    # Notificar agente (Simulacion)
    agente_info = agentes[agentes['id'] == agente_asignado_id].iloc[0]
    print(f"--> NOTIFICACION SIMULADA: Enviando WhatsApp a {agente_info['nombre']} ({agente_info['whatsapp']}) - Nuevo lead: {nuevo_contacto_dict['nombre']}")

    return int(agente_asignado_id)

def crear_contacto(datos):
    """
    Recibe diccionario con datos del contacto (nombre, telefono, propiedad_id, etc)
    """
    agentes, propiedades, contactos = cargar_datos()

    nuevo_id = 1
    if not contactos.empty:
        nuevo_id = int(contactos['id'].max()) + 1

    agente_id = asignar_agente(datos)

    nuevo_contacto = {
        'id': nuevo_id,
        'nombre': datos['nombre'],
        'telefono': datos['telefono'],
        'fecha': pd.Timestamp.now(),
        'propiedad_id': datos.get('propiedad_id'),
        'estado': 'Asignado',
        'agente_asignado_id': agente_id
    }

    # Usar pd.concat en lugar de append (deprecated)
    contactos = pd.concat([contactos, pd.DataFrame([nuevo_contacto])], ignore_index=True)
    guardar_contactos(contactos)

    # Generar mensaje inicial para el agente
    agente = agentes[agentes['id'] == agente_id].iloc[0].to_dict()
    propiedad = None
    if datos.get('propiedad_id'):
        prop_row = propiedades[propiedades['id'] == int(datos['propiedad_id'])]
        if not prop_row.empty:
            propiedad = prop_row.iloc[0].to_dict()

    msg_module.generar_mensaje_nuevo_lead(nuevo_contacto, agente, propiedad)

    return nuevo_contacto

def actualizar_estado_contacto(contacto_id, nuevo_estado):
    agentes, propiedades, contactos = cargar_datos()

    if contacto_id in contactos['id'].values:
        idx = contactos[contactos['id'] == contacto_id].index[0]
        contactos.at[idx, 'estado'] = nuevo_estado
        guardar_contactos(contactos)
        return True
    return False

def obtener_metricas():
    agentes, propiedades, contactos = cargar_datos()

    total_contactos = len(contactos)
    por_estado = contactos['estado'].value_counts().to_dict()

    # Top agentes
    top_agentes = contacts_per_agent = contactos['agente_asignado_id'].value_counts().head(5).to_dict()

    # Mapear IDs a nombres para el frontend
    top_agentes_nombres = {}
    for ag_id, count in top_agentes.items():
        nombre = agentes[agentes['id'] == ag_id].iloc[0]['nombre']
        top_agentes_nombres[nombre] = count

    return {
        'total_contactos': total_contactos,
        'por_estado': por_estado,
        'top_agentes': top_agentes_nombres
    }
