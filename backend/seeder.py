import pandas as pd
from faker import Faker
import random
import os

fake = Faker('es_MX')

DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def generate_data():
    print("Generando datos...")

    # 1. Agentes
    print("Creando agentes...")
    agentes = []
    for i in range(1, 11):
        agentes.append({
            'id': i,
            'nombre': fake.name(),
            'email': fake.email(),
            'whatsapp': fake.phone_number(),
            'carga_trabajo': 0
        })
    df_agentes = pd.DataFrame(agentes)
    df_agentes.to_csv(os.path.join(DATA_DIR, 'agentes.csv'), index=False)

    # 2. Propiedades
    print("Creando propiedades...")
    propiedades = []
    tipos = ['Casa', 'Departamento', 'Terreno', 'Local Comercial']
    for i in range(1, 51):
        propiedades.append({
            'id': i,
            'direccion': fake.address(),
            'tipo': random.choice(tipos),
            'precio': random.randint(1000000, 15000000),
            'agente_id': random.randint(1, 10) # Agente responsable de la captación
        })
    df_propiedades = pd.DataFrame(propiedades)
    df_propiedades.to_csv(os.path.join(DATA_DIR, 'propiedades.csv'), index=False)

    # 3. Contactos (Simulados inicialmente)
    print("Creando contactos simulados...")
    contactos = []
    estados = ['Nuevo', 'Contactado', 'En Proceso', 'Cerrado', 'Perdido']
    for i in range(1, 101):
        contactos.append({
            'id': i,
            'nombre': fake.name(),
            'telefono': fake.phone_number(),
            'fecha': fake.date_time_between(start_date='-30d', end_date='now'),
            'propiedad_id': random.randint(1, 50),
            'estado': random.choice(estados),
            'agente_asignado_id': random.randint(1, 10)
        })
    df_contactos = pd.DataFrame(contactos)
    df_contactos.to_csv(os.path.join(DATA_DIR, 'contactos.csv'), index=False)

    print("Datos generados exitosamente en /data")

if __name__ == "__main__":
    generate_data()
