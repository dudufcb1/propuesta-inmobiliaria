from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import database as db

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Usuario demo hardcodeado
DEMO_USER = {
    'email': 'converging@demo.com',
    'password': 'demo2025',
    'name': 'Demo User'
}

# Token simple (en produccion usar JWT)
DEMO_TOKEN = 'demo_token_minicrm_2024'


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requerido'}), 401

        token = auth_header.split(' ')[1]
        if token != DEMO_TOKEN:
            return jsonify({'error': 'Token invalido'}), 401

        return f(*args, **kwargs)
    return decorated


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if email == DEMO_USER['email'] and password == DEMO_USER['password']:
        return jsonify({
            'token': DEMO_TOKEN,
            'user': {
                'email': DEMO_USER['email'],
                'name': DEMO_USER['name']
            }
        })

    return jsonify({'error': 'Credenciales invalidas'}), 401


@app.route('/auth/me', methods=['GET'])
@require_auth
def auth_me():
    return jsonify({
        'email': DEMO_USER['email'],
        'name': DEMO_USER['name']
    })

# Inicializar DB y migrar datos si es necesario
db.init_db()
db.migrate_from_csv()

# Botones por tipo de mensaje
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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/contactos', methods=['GET'])
@require_auth
def get_contactos():
    contactos = db.get_contactos()
    return jsonify(contactos)


@app.route('/contactos', methods=['POST'])
@require_auth
def create_contacto():
    data = request.json
    if not data or 'nombre' not in data or 'telefono' not in data:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400

    nombre = data['nombre']
    telefono = data['telefono']
    propiedad_id = data.get('propiedad_id')
    modo = data.get('modo_asignacion', 'auto')

    # Determinar agente
    agente_id = None

    if modo == 'manual':
        agente_id = data.get('agente_manual_id')
    elif modo == 'round_robin':
        agente_id = db.get_agente_menos_carga()
    else:
        # Auto: si hay propiedad, usar su agente; sino round robin
        if propiedad_id:
            propiedad = db.get_propiedad(propiedad_id)
            if propiedad:
                agente_id = propiedad['agente_id']
        if not agente_id:
            agente_id = db.get_agente_menos_carga()

    # Crear contacto
    nuevo_contacto = db.crear_contacto(nombre, telefono, propiedad_id, agente_id)

    # Generar mensaje inicial para el agente
    agente = db.get_agente(agente_id)
    propiedad = db.get_propiedad(propiedad_id) if propiedad_id else None

    prop_info = ""
    if propiedad:
        prop_info = f"\nInteresado en: {propiedad['tipo']} - {propiedad['direccion']}"

    contenido = f"Nuevo lead asignado: {nombre} ({telefono}){prop_info}"
    botones = str(BOTONES_POR_MENSAJE['nuevo_lead'])

    db.crear_mensaje(nuevo_contacto['id'], agente_id, 'nuevo_lead', contenido, botones)

    print(f"--> NOTIFICACION: Lead {nombre} asignado a {agente['nombre']}")

    return jsonify(nuevo_contacto), 201


@app.route('/contactos/<int:id>', methods=['PATCH'])
@require_auth
def update_contacto(id):
    data = request.json
    nuevo_estado = data.get('estado')

    if not nuevo_estado:
        return jsonify({'error': 'Falta el nuevo estado'}), 400

    exito = db.actualizar_estado_contacto(id, nuevo_estado)
    if exito:
        return jsonify({'message': 'Estado actualizado'}), 200
    else:
        return jsonify({'error': 'Contacto no encontrado'}), 404


@app.route('/agentes', methods=['GET'])
@require_auth
def get_agentes():
    agentes = db.get_agentes()
    return jsonify(agentes)


@app.route('/propiedades', methods=['GET'])
@require_auth
def get_propiedades():
    propiedades = db.get_propiedades()
    return jsonify(propiedades)


@app.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    metricas = db.get_metricas()
    return jsonify(metricas)


# --- ENDPOINTS DE MENSAJES ---

@app.route('/mensajes/agente/<int:agente_id>', methods=['GET'])
@require_auth
def get_mensajes_agente(agente_id):
    mensajes = db.get_mensajes_agente(agente_id)
    # Parsear botones de string a lista
    for msg in mensajes:
        try:
            msg['botones'] = eval(msg['botones']) if msg['botones'] else []
        except:
            msg['botones'] = []
        msg['respondido'] = bool(msg['respondido'])
    return jsonify(mensajes)


@app.route('/mensajes/accion', methods=['POST'])
@require_auth
def ejecutar_accion():
    data = request.json
    mensaje_id = data.get('mensaje_id')
    accion = data.get('accion')
    contacto_id = data.get('contacto_id')

    if not all([mensaje_id, accion, contacto_id]):
        return jsonify({'error': 'Faltan datos'}), 400

    contacto = db.get_contacto(contacto_id)
    if not contacto:
        return jsonify({'error': 'Contacto no encontrado'}), 404

    agente_id = contacto['agente_asignado_id']
    agente = db.get_agente(agente_id)

    # Marcar mensaje como respondido
    db.responder_mensaje(mensaje_id, accion)

    # Ejecutar accion
    nuevo_estado = None
    mensaje_respuesta = None

    if accion == 'confirmar_recepcion':
        nuevo_estado = 'Confirmado'
        contenido = f"¿Pudiste contactar a {contacto['nombre']}?"
        botones = str(BOTONES_POR_MENSAJE['pedir_contacto'])
        db.crear_mensaje(contacto_id, agente_id, 'pedir_contacto', contenido, botones)

    elif accion == 'rechazar_lead':
        nuevo_estado = 'Nuevo'
        # TODO: reasignar

    elif accion == 'marcar_contactado':
        nuevo_estado = 'Contactado'
        contenido = f"¿Como va la gestion con {contacto['nombre']}?"
        botones = str(BOTONES_POR_MENSAJE['seguimiento'])
        db.crear_mensaje(contacto_id, agente_id, 'seguimiento', contenido, botones)

    elif accion == 'no_pudo_contactar':
        mensaje_respuesta = "Entendido. Intenta nuevamente pronto."
        contenido = f"Recordatorio: Intenta contactar a {contacto['nombre']} ({contacto['telefono']})"
        botones = str(BOTONES_POR_MENSAJE['pedir_contacto'])
        db.crear_mensaje(contacto_id, agente_id, 'pedir_contacto', contenido, botones)

    elif accion == 'cliente_no_contesta':
        mensaje_respuesta = "OK. Te recordaremos en unas horas."
        contenido = f"¿Pudiste contactar a {contacto['nombre']}? (intento anterior: no contesta)"
        botones = str(BOTONES_POR_MENSAJE['pedir_contacto'])
        db.crear_mensaje(contacto_id, agente_id, 'pedir_contacto', contenido, botones)

    elif accion == 'marcar_negociacion':
        nuevo_estado = 'En Negociacion'
        contenido = f"¿Como va la gestion con {contacto['nombre']}?"
        botones = str(BOTONES_POR_MENSAJE['seguimiento'])
        db.crear_mensaje(contacto_id, agente_id, 'seguimiento', contenido, botones)

    elif accion == 'marcar_cerrado':
        nuevo_estado = 'Cerrado'
        contenido = f"Felicitaciones! Lead {contacto['nombre']} marcado como cerrado."
        db.crear_mensaje(contacto_id, agente_id, 'felicitacion', contenido, None)

    elif accion == 'marcar_perdido':
        nuevo_estado = 'Perdido'
        contenido = f"Lead {contacto['nombre']} marcado como perdido. Sigue adelante!"
        db.crear_mensaje(contacto_id, agente_id, 'felicitacion', contenido, None)

    if nuevo_estado:
        db.actualizar_estado_contacto(contacto_id, nuevo_estado)

    return jsonify({
        'success': True,
        'nuevo_estado': nuevo_estado,
        'mensaje': mensaje_respuesta
    })


@app.route('/mensajes/pendientes/<int:agente_id>', methods=['GET'])
@require_auth
def get_mensajes_pendientes(agente_id):
    mensajes = db.get_mensajes_agente(agente_id)
    pendientes = [m for m in mensajes if not m['respondido']]
    return jsonify(pendientes)


# --- LLAMADAS PERDIDAS ---

@app.route('/llamadas/simular', methods=['GET'])
@require_auth
def simular_llamada():
    """Simula una llamada perdida con un numero aleatorio de cliente existente."""
    import random
    contactos = db.get_contactos()
    if not contactos:
        return jsonify({'error': 'No hay contactos'}), 404

    contacto = random.choice(contactos)
    return jsonify({
        'telefono': contacto['telefono'],
        'mensaje': 'Llamada perdida simulada'
    })


@app.route('/llamadas/buscar', methods=['POST'])
@require_auth
def buscar_por_telefono():
    """Busca un cliente por numero de telefono."""
    data = request.json
    telefono = data.get('telefono', '').strip()

    if not telefono:
        return jsonify({'error': 'Telefono requerido'}), 400

    contactos = db.get_contactos()

    # Buscar coincidencia (parcial o exacta)
    encontrados = []
    for c in contactos:
        if telefono in c['telefono'] or c['telefono'] in telefono:
            agente = db.get_agente(c['agente_asignado_id'])
            propiedad = db.get_propiedad(c['propiedad_id']) if c['propiedad_id'] else None
            encontrados.append({
                'contacto': c,
                'agente': agente,
                'propiedad': propiedad
            })

    if not encontrados:
        return jsonify({'encontrado': False, 'mensaje': 'Cliente no encontrado'})

    return jsonify({'encontrado': True, 'resultados': encontrados})


@app.route('/llamadas/seguimiento', methods=['POST'])
@require_auth
def enviar_seguimiento():
    """Envia mensaje de seguimiento al agente segun el estado del contacto."""
    data = request.json
    contacto_id = data.get('contacto_id')
    tipo_seguimiento = data.get('tipo')  # llamada_perdida, sin_respuesta, postventa, etc.

    if not contacto_id:
        return jsonify({'error': 'contacto_id requerido'}), 400

    contacto = db.get_contacto(contacto_id)
    if not contacto:
        return jsonify({'error': 'Contacto no encontrado'}), 404

    agente_id = contacto['agente_asignado_id']
    agente = db.get_agente(agente_id)
    estado_actual = contacto['estado']

    # Generar mensaje segun el contexto
    if tipo_seguimiento == 'llamada_perdida':
        if estado_actual == 'Cerrado':
            contenido = f"Postventa: {contacto['nombre']} ({contacto['telefono']}) intento comunicarse. Ya es cliente cerrado."
            botones = str([
                {'id': 'atendido', 'label': 'Ya lo atendi', 'accion': 'marcar_atendido_postventa'},
                {'id': 'llamar', 'label': 'Voy a llamar', 'accion': 'confirmar_llamada'}
            ])
        elif estado_actual == 'Perdido':
            contenido = f"Reactivacion: {contacto['nombre']} ({contacto['telefono']}) llamo nuevamente. Estaba marcado como perdido."
            botones = str([
                {'id': 'reactivar', 'label': 'Reactivar lead', 'accion': 'reactivar_lead'},
                {'id': 'ignorar', 'label': 'No interesa', 'accion': 'mantener_perdido'}
            ])
        elif estado_actual in ['Asignado', 'Confirmado']:
            contenido = f"Llamada perdida: {contacto['nombre']} ({contacto['telefono']}) intento comunicarse. Aun no lo has contactado."
            botones = str([
                {'id': 'contactado', 'label': 'Ya lo contacte', 'accion': 'marcar_contactado'},
                {'id': 'llamar', 'label': 'Voy a llamar', 'accion': 'confirmar_llamada'}
            ])
        elif estado_actual == 'Contactado':
            contenido = f"Seguimiento: {contacto['nombre']} ({contacto['telefono']}) llamo. Ya lo habias contactado antes."
            botones = str([
                {'id': 'en_negociacion', 'label': 'En negociacion', 'accion': 'marcar_negociacion'},
                {'id': 'cerrado', 'label': 'Cerrado', 'accion': 'marcar_cerrado'},
                {'id': 'perdido', 'label': 'Perdido', 'accion': 'marcar_perdido'}
            ])
        elif estado_actual == 'En Negociacion':
            contenido = f"Cliente activo: {contacto['nombre']} ({contacto['telefono']}) llamo. Esta en negociacion."
            botones = str([
                {'id': 'cerrado', 'label': 'Cerrado', 'accion': 'marcar_cerrado'},
                {'id': 'seguir', 'label': 'Sigo en contacto', 'accion': 'confirmar_seguimiento'},
                {'id': 'perdido', 'label': 'Perdido', 'accion': 'marcar_perdido'}
            ])
        else:
            contenido = f"Llamada de: {contacto['nombre']} ({contacto['telefono']}). Estado actual: {estado_actual}"
            botones = str([
                {'id': 'atendido', 'label': 'Atendido', 'accion': 'marcar_atendido'}
            ])
    else:
        contenido = f"Seguimiento requerido: {contacto['nombre']} ({contacto['telefono']})"
        botones = str([
            {'id': 'atendido', 'label': 'Atendido', 'accion': 'marcar_atendido'}
        ])

    db.crear_mensaje(contacto_id, agente_id, 'seguimiento_llamada', contenido, botones)

    return jsonify({
        'success': True,
        'mensaje': f'Notificacion enviada a {agente["nombre"]}',
        'estado_contacto': estado_actual
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
