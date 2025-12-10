# Mini CRM Inmobiliario (Demo)

Prototipo de sistema CRM para gestión de contactos inmobiliarios, desarrollado como prueba de concepto (PoC).

## Características

- **Backend Python**: Flask + Pandas para lógica de negocio y persistencia simple en CSV.
- **Frontend Ligero**: HTML5 + Vanilla JS + TailwindCSS.
- **Asignación Inteligente**: Distribuye leads automáticamente basándose en la propiedad de interés o carga de trabajo.
- **Dockerizado**: Listo para ejecutar con un solo comando.

## Estructura del Proyecto

```
/backend
  - api.py          # API REST con Flask
  - asignacion.py   # Lógica de asignación de leads
  - seeder.py       # Generador de datos de prueba
  - Dockerfile
/frontend
  - index.html      # SPA con Dashboard, Captura y Vista Agente
  - app.js          # Lógica frontend
/data
  - *.csv           # Base de datos en archivos planos
docker-compose.yml
demo_script.py      # Script para simular flujo completo
```

## Instrucciones de Ejecución

### Prerrequisitos
- Docker y Docker Compose instalados.

### Pasos

1. **Iniciar el entorno**:
   ```bash
   docker-compose up --build
   ```
   Esto levantará:
   - Backend API en: http://localhost:5000
   - Frontend en: http://localhost:8080

2. **Acceder a la aplicación**:
   Abre tu navegador en [http://localhost:8080](http://localhost:8080).

3. **Ejecutar Demo Automática** (Opcional):
   Para ver el flujo de datos sin interactuar manualmente:
   ```bash
   python3 demo_script.py
   ```
   *Nota: Requiere `requests` instalado localmente (`pip install requests`).*

## Uso del Sistema

1. **Dashboard**: Vista general de métricas (Total contactos, Tasa de conversión, Top agentes).
2. **Captura Lead**: Formulario para registrar nuevos interesados. Al guardar, el sistema asigna un agente automáticamente.
3. **Vista Agente**: Simula la vista de un agente específico para gestionar sus leads asignados (Contactar, Cerrar).

## Notas Técnicas
- La persistencia es volátil si se borra la carpeta `/data` o se reinicia el contenedor sin volúmenes (aunque están configurados en el compose).
- Los datos iniciales se generan automáticamente si no existen archivos CSV.
