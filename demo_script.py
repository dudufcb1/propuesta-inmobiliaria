import requests
import time
import random

API_URL = "http://localhost:5000"

def demo():
    print("==================================================")
    print("INICIANDO DEMO AUTOMÁTICA MINI CRM")
    print("==================================================")

    # 1. Verificar salud
    try:
        requests.get(f"{API_URL}/health")
        print("✅ Backend online")
    except:
        print("❌ Error: Backend no responde. Asegúrate de ejecutar 'docker-compose up'")
        return

    # 2. Simular entrada de nuevo lead (Gisel)
    print("\n[Paso 1] Gisel registra un nuevo lead interesado...")
    nuevo_lead = {
        "nombre": f"Cliente Interesado {random.randint(100, 999)}",
        "telefono": "555-000-1234",
        "propiedad_id": random.randint(1, 10),
        "notas": "Interesado en visitar el fin de semana"
    }

    res = requests.post(f"{API_URL}/contactos", json=nuevo_lead)
    if res.status_code == 201:
        data = res.json()
        print(f"✅ Lead creado: {data['nombre']}")
        print(f"✅ Asignado automáticamente al Agente ID: {data['agente_asignado_id']}")
        lead_id = data['id']
        agente_id = data['agente_asignado_id']
    else:
        print("❌ Fallo al crear lead")
        return

    time.sleep(2)

    # 3. Simular Agente viendo su dashboard y contactando
    print(f"\n[Paso 2] Agente {agente_id} ve el lead y lo contacta...")
    res = requests.patch(f"{API_URL}/contactos/{lead_id}", json={"estado": "Contactado"})
    if res.status_code == 200:
        print(f"✅ Estado actualizado a: Contactado")

    time.sleep(2)

    # 4. Simular cierre de venta
    print(f"\n[Paso 3] El cliente confirma compra. Agente cierra el trato.")
    res = requests.patch(f"{API_URL}/contactos/{lead_id}", json={"estado": "Cerrado"})
    if res.status_code == 200:
        print(f"✅ Estado actualizado a: Cerrado")

    print("\n==================================================")
    print("DEMO FINALIZADA EXITOSAMENTE")
    print("Revisa el dashboard en http://localhost:8080")
    print("==================================================")

if __name__ == "__main__":
    demo()
