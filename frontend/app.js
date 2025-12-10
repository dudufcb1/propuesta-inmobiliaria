const API_URL = 'http://localhost:5000';

// Estado global simple
let state = {
    contactos: [],
    agentes: [],
    propiedades: [],
    token: localStorage.getItem('crm_token') || null,
    user: JSON.parse(localStorage.getItem('crm_user') || 'null')
};

// Helper para hacer requests autenticados
function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
    };
}

async function authFetch(url, options = {}) {
    const headers = { ...authHeaders(), ...options.headers };
    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
        handleLogout();
        throw new Error('Sesion expirada');
    }

    return res;
}

// --- AUTH ---

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');

    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            errorDiv.textContent = data.error || 'Error de autenticacion';
            errorDiv.classList.remove('hidden');
            return;
        }

        state.token = data.token;
        state.user = data.user;
        localStorage.setItem('crm_token', data.token);
        localStorage.setItem('crm_user', JSON.stringify(data.user));

        showApp();
    } catch (err) {
        errorDiv.textContent = 'Error de conexion';
        errorDiv.classList.remove('hidden');
    }
}

function handleLogout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('crm_token');
    localStorage.removeItem('crm_user');
    showLogin();
}

function showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-container').classList.add('hidden');
}

function showApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
    init();
}

async function checkAuth() {
    if (!state.token) {
        showLogin();
        return;
    }

    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: authHeaders()
        });

        if (res.ok) {
            showApp();
        } else {
            handleLogout();
        }
    } catch (err) {
        handleLogout();
    }
}

async function init() {
    console.log('Iniciando Mini CRM...');
    await loadData();
    setupEventListeners();

    // Auto refresh cada 10s
    setInterval(loadDashboardData, 10000);

    // Cargar dashboard inicial
    renderDashboard();
}

async function loadData() {
    try {
        const [resContactos, resAgentes, resPropiedades] = await Promise.all([
            authFetch(`${API_URL}/contactos`),
            authFetch(`${API_URL}/agentes`),
            authFetch(`${API_URL}/propiedades`)
        ]);

        state.contactos = await resContactos.json();
        state.agentes = await resAgentes.json();
        state.propiedades = await resPropiedades.json();

        // Actualizar dropdowns
        updateDropdowns();
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}

async function loadDashboardData() {
    // Recarga ligera para dashboard
    try {
        const res = await authFetch(`${API_URL}/dashboard`);
        const data = await res.json();
        updateDashboardMetrics(data);

        // Recargar tabla completa tambien
        const resCont = await authFetch(`${API_URL}/contactos`);
        state.contactos = await resCont.json();
        renderContactsTable();
    } catch (e) {
        console.error("Error refreshing dashboard", e);
    }
}

function updateDropdowns() {
    // Propiedades en Captura
    const propSelect = document.getElementById('propiedad');
    propSelect.innerHTML = '<option value="">-- Sin propiedad especifica --</option>';
    state.propiedades.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.tipo} - ${p.direccion} ($${p.precio})`;
        propSelect.appendChild(opt);
    });

    // Agentes en Vista Agente
    const agentSelect = document.getElementById('select-agente-simulacion');
    agentSelect.innerHTML = '';
    state.agentes.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.nombre;
        agentSelect.appendChild(opt);
    });

    // Agentes en selector manual de Captura
    const agentManualSelect = document.getElementById('agente-manual');
    agentManualSelect.innerHTML = '<option value="">-- Seleccionar Agente --</option>';
    state.agentes.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.nombre;
        agentManualSelect.appendChild(opt);
    });
}

function toggleAsignacionManual() {
    const propSelect = document.getElementById('propiedad');
    const asignacionContainer = document.getElementById('asignacion-container');

    if (propSelect.value) {
        // Si hay propiedad seleccionada, ocultar opciones de asignacion
        asignacionContainer.classList.add('hidden');
    } else {
        // Sin propiedad, mostrar opciones
        asignacionContainer.classList.remove('hidden');
    }
}

function toggleAgenteSelect() {
    const modoManual = document.querySelector('input[name="modo_asignacion"][value="manual"]').checked;
    const agentManualSelect = document.getElementById('agente-manual');

    if (modoManual) {
        agentManualSelect.classList.remove('hidden');
    } else {
        agentManualSelect.classList.add('hidden');
    }
}

function showSection(sectionId) {
    // Ocultar todas
    document.querySelectorAll('.section-content').forEach(el => el.classList.add('hidden'));
    // Mostrar seleccionada
    document.getElementById(`${sectionId}-section`).classList.remove('hidden');

    if (sectionId === 'dashboard') {
        loadDashboardData();
    } else if (sectionId === 'agente') {
        cargarVistaAgente();
    }
}

// --- DASHBOARD ---

function renderDashboard() {
    loadDashboardData();
}

function updateDashboardMetrics(data) {
    document.getElementById('kpi-total').textContent = data.total_contactos;

    // Calcular "Nuevos hoy" (simple filtro local o usar backend)
    // Usaremos datos del backend 'por_estado' para simplificar por ahora
    const nuevos = data.por_estado['Nuevo'] || 0;
    document.getElementById('kpi-nuevos').textContent = novos_hoy_simulado(); // Simulamos "hoy" vs total

    document.getElementById('kpi-pendientes').textContent = nuevos;

    // Listas simples para graficas
    const listEstado = document.getElementById('list-estado');
    listEstado.innerHTML = '';
    for (const [k, v] of Object.entries(data.por_estado)) {
        listEstado.innerHTML += `<li class="flex justify-between py-1 border-b border-gray-100"><span>${k}</span> <span class="font-bold">${v}</span></li>`;
    }

    const listAgentes = document.getElementById('list-agentes');
    listAgentes.innerHTML = '';
    for (const [k, v] of Object.entries(data.top_agentes)) {
        listAgentes.innerHTML += `<li class="flex justify-between py-1 border-b border-gray-100"><span>${k}</span> <span class="font-bold">${v}</span></li>`;
    }
}

function novos_hoy_simulado() {
    // Retorna un número aleatorio para simular actividad diaria
    return state.contactos.filter(c => c.estado === 'Nuevo').length;
}

function renderContactsTable() {
    const tbody = document.getElementById('table-contacts');
    tbody.innerHTML = '';

    // Mostrar ultimos 10
    const ultimos = [...state.contactos].reverse().slice(0, 10);

    ultimos.forEach(c => {
        const agente = state.agentes.find(a => a.id === c.agente_asignado_id);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">${c.nombre}</td>
            <td class="px-6 py-4 whitespace-nowrap">${c.telefono}</td>
            <td class="px-6 py-4 whitespace-nowrap"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">${c.estado}</span></td>
            <td class="px-6 py-4 whitespace-nowrap">${agente ? agente.nombre : 'Sin asignar'}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(c.fecha).toLocaleDateString()}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- CAPTURA ---

async function registrarContacto(e) {
    e.preventDefault();
    const nombre = document.getElementById('nombre').value;
    const telefono = document.getElementById('telefono').value;
    const propiedadId = document.getElementById('propiedad').value;

    const data = {
        nombre,
        telefono,
        propiedad_id: propiedadId ? parseInt(propiedadId) : null
    };

    // Si no hay propiedad, agregar modo de asignacion
    if (!propiedadId) {
        const modoAsignacion = document.querySelector('input[name="modo_asignacion"]:checked').value;
        data.modo_asignacion = modoAsignacion;

        if (modoAsignacion === 'manual') {
            const agenteManualId = document.getElementById('agente-manual').value;
            if (!agenteManualId) {
                alert('Selecciona un agente para asignacion manual');
                return;
            }
            data.agente_manual_id = parseInt(agenteManualId);
        }
    }

    try {
        const res = await authFetch(`${API_URL}/contactos`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        if (res.ok) {
            showNotification('Contacto registrado y asignado exitosamente');
            document.getElementById('form-captura').reset();
            // Resetear visibilidad de campos
            document.getElementById('asignacion-container').classList.remove('hidden');
            document.getElementById('agente-manual').classList.add('hidden');
            loadData();
        } else {
            alert('Error al registrar');
        }
    } catch (err) {
        console.error(err);
        alert('Error de conexion');
    }
}

// --- AGENTE ---

async function cargarVistaAgente() {
    const agenteId = parseInt(document.getElementById('select-agente-simulacion').value);
    if (!agenteId) return;

    // Cargar mensajes de WhatsApp
    await cargarMensajesWhatsApp(agenteId);

    // Cargar lista de leads
    cargarLeadsAgente(agenteId);
}

async function cargarMensajesWhatsApp(agenteId) {
    try {
        const res = await authFetch(`${API_URL}/mensajes/agente/${agenteId}`);
        const mensajes = await res.json();

        const chatContainer = document.getElementById('whatsapp-chat');
        chatContainer.innerHTML = '';

        if (mensajes.length === 0) {
            chatContainer.innerHTML = `
                <div class="text-center text-gray-500 mt-10">
                    <i class="fas fa-inbox text-4xl mb-2"></i>
                    <p>No hay mensajes</p>
                </div>
            `;
            return;
        }

        mensajes.forEach(msg => {
            const msgEl = crearMensajeWhatsApp(msg);
            chatContainer.appendChild(msgEl);
        });

        // Scroll al final
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (err) {
        console.error('Error cargando mensajes:', err);
    }
}

function crearMensajeWhatsApp(msg) {
    const div = document.createElement('div');
    div.className = 'mb-3';

    const hora = new Date(msg.fecha).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });

    // Burbuja del mensaje
    const burbuja = document.createElement('div');
    burbuja.className = 'bg-white rounded-lg p-3 shadow max-w-xs ml-0';

    // Contenido
    burbuja.innerHTML = `
        <p class="text-sm text-gray-800">${msg.contenido}</p>
        <p class="text-xs text-gray-400 text-right mt-1">${hora}</p>
    `;

    div.appendChild(burbuja);

    // Si tiene botones y no fue respondido, mostrarlos
    if (msg.botones && msg.botones.length > 0 && !msg.respondido) {
        const botonesContainer = document.createElement('div');
        botonesContainer.className = 'mt-2 space-y-1';

        msg.botones.forEach(btn => {
            const boton = document.createElement('button');
            boton.className = 'w-full bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-4 rounded';
            boton.textContent = btn.label;
            boton.onclick = () => ejecutarAccionWhatsApp(msg.id, btn.accion, msg.contacto_id);
            botonesContainer.appendChild(boton);
        });

        div.appendChild(botonesContainer);
    }

    // Si fue respondido, mostrar la respuesta
    if (msg.respondido && msg.respuesta) {
        const respuestaDiv = document.createElement('div');
        respuestaDiv.className = 'bg-green-100 rounded-lg p-2 shadow max-w-xs ml-auto mt-1';
        respuestaDiv.innerHTML = `
            <p class="text-sm text-green-800 text-right">${formatearRespuesta(msg.respuesta)}</p>
        `;
        div.appendChild(respuestaDiv);
    }

    return div;
}

function formatearRespuesta(accion) {
    const mapeo = {
        'confirmar_recepcion': 'Recibido',
        'rechazar_lead': 'Rechazado',
        'marcar_contactado': 'Si, contacte',
        'no_pudo_contactar': 'No pude',
        'cliente_no_contesta': 'No contesta',
        'marcar_negociacion': 'En negociacion',
        'marcar_cerrado': 'Cerrado',
        'marcar_perdido': 'Perdido'
    };
    return mapeo[accion] || accion;
}

async function ejecutarAccionWhatsApp(mensajeId, accion, contactoId) {
    try {
        const res = await authFetch(`${API_URL}/mensajes/accion`, {
            method: 'POST',
            body: JSON.stringify({
                mensaje_id: mensajeId,
                accion: accion,
                contacto_id: contactoId
            })
        });

        if (res.ok) {
            const data = await res.json();
            showNotification(data.mensaje || `Accion ejecutada: ${accion}`);

            // Recargar vista
            await loadData();
            cargarVistaAgente();
        }
    } catch (err) {
        console.error('Error ejecutando accion:', err);
    }
}

function cargarLeadsAgente(agenteId) {
    const leads = state.contactos.filter(c =>
        c.agente_asignado_id === agenteId &&
        c.estado !== 'Cerrado' &&
        c.estado !== 'Perdido'
    );

    const lista = document.getElementById('list-agente-leads');
    lista.innerHTML = '';

    if (leads.length === 0) {
        lista.innerHTML = '<li class="p-4 text-center text-gray-500">No tienes leads pendientes.</li>';
        return;
    }

    leads.forEach(lead => {
        const propiedad = state.propiedades.find(p => p.id === lead.propiedad_id);
        const li = document.createElement('li');
        li.className = 'px-4 py-3 hover:bg-gray-50';
        li.innerHTML = `
            <div class="flex justify-between items-start">
                <div>
                    <p class="font-medium text-gray-900">${lead.nombre}</p>
                    <p class="text-sm text-gray-500">${lead.telefono}</p>
                    ${propiedad ? `<p class="text-xs text-gray-400">${propiedad.tipo} - ${propiedad.direccion}</p>` : ''}
                </div>
                <span class="px-2 py-1 text-xs rounded-full ${getEstadoColor(lead.estado)}">${lead.estado}</span>
            </div>
        `;
        lista.appendChild(li);
    });
}

function getEstadoColor(estado) {
    const colores = {
        'Nuevo': 'bg-blue-100 text-blue-800',
        'Asignado': 'bg-yellow-100 text-yellow-800',
        'Confirmado': 'bg-orange-100 text-orange-800',
        'Contactado': 'bg-purple-100 text-purple-800',
        'En Negociacion': 'bg-indigo-100 text-indigo-800',
        'Cerrado': 'bg-green-100 text-green-800',
        'Perdido': 'bg-red-100 text-red-800'
    };
    return colores[estado] || 'bg-gray-100 text-gray-800';
}

async function cambiarEstado(id, nuevoEstado) {
    try {
        const res = await authFetch(`${API_URL}/contactos/${id}`, {
            method: 'PATCH',
            body: JSON.stringify({ estado: nuevoEstado })
        });

        if (res.ok) {
            showNotification(`Estado actualizado a: ${nuevoEstado}`);
            await loadData();
            cargarVistaAgente(); // Refrescar vista actual
        }
    } catch (err) {
        console.error(err);
    }
}

// --- UTILIDADES ---

function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

function showNotification(msg) {
    const notif = document.getElementById('notification');
    notif.textContent = msg;
    notif.classList.remove('hidden');
    setTimeout(() => {
        notif.classList.add('hidden');
    }, 3000);
}

function setupEventListeners() {
    // Listeners adicionales si fueran necesarios
}


// --- LLAMADAS PERDIDAS ---

let ultimoNumeroSimulado = '';

async function simularLlamada() {
    try {
        const res = await authFetch(`${API_URL}/llamadas/simular`);
        const data = await res.json();

        ultimoNumeroSimulado = data.telefono;
        document.getElementById('numero-simulado').textContent = data.telefono;
        document.getElementById('llamada-simulada').classList.remove('hidden');

        // Copiar automaticamente al input de busqueda
        document.getElementById('telefono-buscar').value = data.telefono;

    } catch (err) {
        console.error('Error simulando llamada:', err);
    }
}

function copiarNumero() {
    navigator.clipboard.writeText(ultimoNumeroSimulado);
    showNotification('Numero copiado');
}

async function buscarCliente() {
    const telefono = document.getElementById('telefono-buscar').value.trim();
    if (!telefono) {
        alert('Ingresa un numero para buscar');
        return;
    }

    try {
        const res = await authFetch(`${API_URL}/llamadas/buscar`, {
            method: 'POST',
            body: JSON.stringify({ telefono })
        });

        const data = await res.json();
        const contenedor = document.getElementById('resultado-busqueda');
        contenedor.classList.remove('hidden');

        if (!data.encontrado) {
            contenedor.innerHTML = `
                <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p class="text-yellow-700 font-medium">Cliente no encontrado</p>
                    <p class="text-sm text-yellow-600">Este numero no esta registrado en el sistema.</p>
                    <button onclick="showSection('captura')" class="mt-2 text-sm text-blue-600 hover:text-blue-800">
                        Registrar como nuevo lead
                    </button>
                </div>
            `;
            return;
        }

        // Mostrar resultados
        let html = '';
        data.resultados.forEach(r => {
            const c = r.contacto;
            const a = r.agente;
            const p = r.propiedad;

            html += `
                <div class="p-4 bg-green-50 border border-green-200 rounded-lg mb-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="font-bold text-gray-800">${c.nombre}</p>
                            <p class="text-sm text-gray-600">${c.telefono}</p>
                            ${p ? `<p class="text-xs text-gray-500">${p.tipo} - ${p.direccion}</p>` : ''}
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${getEstadoColor(c.estado)}">${c.estado}</span>
                    </div>

                    <div class="mt-3 pt-3 border-t border-green-200">
                        <p class="text-sm text-gray-600">
                            <i class="fas fa-user-tie mr-1"></i> Agente: <strong>${a ? a.nombre : 'Sin asignar'}</strong>
                        </p>
                        ${a ? `<p class="text-xs text-gray-500">${a.whatsapp}</p>` : ''}
                    </div>

                    <div class="mt-3 flex space-x-2">
                        <button onclick="enviarSeguimiento(${c.id})" class="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded">
                            <i class="fab fa-whatsapp mr-1"></i> Notificar Agente
                        </button>
                    </div>
                </div>
            `;
        });

        contenedor.innerHTML = html;

    } catch (err) {
        console.error('Error buscando cliente:', err);
    }
}

async function enviarSeguimiento(contactoId) {
    try {
        const res = await authFetch(`${API_URL}/llamadas/seguimiento`, {
            method: 'POST',
            body: JSON.stringify({
                contacto_id: contactoId,
                tipo: 'llamada_perdida'
            })
        });

        const data = await res.json();
        if (data.success) {
            showNotification(data.mensaje);
            // Limpiar busqueda
            document.getElementById('resultado-busqueda').classList.add('hidden');
            document.getElementById('telefono-buscar').value = '';
            document.getElementById('llamada-simulada').classList.add('hidden');
        }
    } catch (err) {
        console.error('Error enviando seguimiento:', err);
    }
}


// Iniciar app
document.addEventListener('DOMContentLoaded', checkAuth);
