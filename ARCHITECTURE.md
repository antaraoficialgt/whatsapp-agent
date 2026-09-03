# Arquitectura del Sistema 🏗️

Documento que explica cómo funciona el sistema WhatsApp Agent API de principio a fin.

## 🌍 Flujo General

```
┌─────────────────────────────────────────────────────────────────┐
│                      USUARIO CLIENTE                            │
│                   (Envía mensaje WhatsApp)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  META WHATSAPP BUSINESS API                     │
│              (Recibe mensaje y lo reenvía)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ POST /webhook
┌─────────────────────────────────────────────────────────────────┐
│                    TU SERVIDOR (FastAPI)                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               webhook.py (WhatsAppWebhookHandler)          │ │
│  │  - Parsea JSON de Meta                                     │ │
│  │  - Extrae teléfono del remitente, texto del mensaje       │ │
│  │  - Guarda en base de datos                                │ │
│  └────────────┬──────────────────────────────────────────────┘ │
│               │                                                  │
│               ▼                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            claude_agent.py (ClaudeAgent)                   │ │
│  │  - Construye contexto de conversación anterior           │ │
│  │  - Llama Claude API con system prompt personalizado       │ │
│  │  - Genera respuesta inteligente                           │ │
│  └────────────┬──────────────────────────────────────────────┘ │
│               │                                                  │
│               ▼                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            database.py (Database)                          │ │
│  │  - Guarda conversación + respuesta                         │ │
│  │  - Registra tiempo de respuesta                           │ │
│  │  - Actualiza analytics                                    │ │
│  └────────────┬──────────────────────────────────────────────┘ │
│               │                                                  │
│               ▼                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         webhook.py (send_message)                          │ │
│  │  - Envía respuesta de vuelta a Meta                        │ │
│  └────────────┬──────────────────────────────────────────────┘ │
│               │                                                  │
└───────────────┼──────────────────────────────────────────────────┘
                │
                ▼ POST request
┌─────────────────────────────────────────────────────────────────┐
│                  META WHATSAPP BUSINESS API                     │
│              (Reenvía respuesta al usuario)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USUARIO CLIENTE                            │
│                   (Recibe respuesta automática)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de Carpetas

```
whatsapp-agent/
│
├── main.py                 # 🌟 FastAPI app principal
│   ├── GET /health        # Verificar que el servidor vive
│   ├── GET /webhook       # Verificar webhook con Meta
│   ├── POST /webhook      # Recibir mensajes entrantes
│   ├── POST /customers    # Crear nuevo cliente
│   ├── GET /customers/me  # Ver info del cliente
│   ├── PUT /customers/me  # Actualizar configuración
│   ├── GET /conversations # Ver conversaciones
│   ├── GET /analytics     # Ver estadísticas
│   └── POST /send-message # Enviar mensaje manual
│
├── webhook.py             # 🔄 Manejo de webhooks
│   ├── WhatsAppWebhookHandler
│   │   ├── handle_webhook()    # Procesa JSON de Meta
│   │   ├── _process_message()  # Procesa un mensaje
│   │   └── send_message()      # Envía respuesta a Meta
│
├── claude_agent.py        # 🤖 Integración con Claude
│   └── ClaudeAgent
│       ├── generate_response()           # Llama Claude API
│       ├── build_conversation_context()  # Obtiene historial
│       └── get_system_prompts_examples() # Prompts de ejemplo
│
├── database.py            # 💾 Base de datos SQLite
│   └── Database
│       ├── create_customer()           # Crear cliente
│       ├── save_conversation()         # Guardar mensajes
│       ├── get_conversation_history()  # Obtener historial
│       └── update_analytics()          # Registrar stats
│
├── requirements.txt       # 📦 Dependencias Python
├── .env.example          # 🔐 Variables de entorno
├── .gitignore            # 🙈 Archivos a ignorar en Git
│
├── README.md             # 📖 Documentación principal
├── TESTING.md            # 🧪 Guía de pruebas
├── DEPLOYMENT.md         # 🚀 Guía de despliegue
├── ARCHITECTURE.md       # 🏗️  Este archivo
└── conversations.db      # 💾 Base de datos (generada)
```

---

## 🔐 Autenticación y Seguridad

### Capas de Autenticación

```
┌──────────────────────────────────────────┐
│  1. API Key Authorization (Bearer Token) │
│  └─ Todos los endpoints protegidos      │
│
│  2. Webhook Verification Token           │
│  └─ Verifica que es Meta quien envía    │
│
│  3. Database Customer Validation         │
│  └─ Valida que cliente existe           │
└──────────────────────────────────────────┘
```

### Flujo de Autenticación

```python
# En cada request a /customers/me, /conversations, etc:

1. Cliente envía: 
   GET /customers/me
   Authorization: Bearer whatsapp_agent_abc123xyz

2. FastAPI ejecuta verify_api_key():
   - Extrae "whatsapp_agent_abc123xyz"
   - Busca en base de datos customers.api_key
   - Retorna customer_id si es válido
   - Retorna 401 si no existe

3. Endpoint accede a customer_id autenticado
   - Solo ve sus propios datos
   - No puede acceder a otros clientes
```

---

## 💬 Flujo de Conversación Detallado

### Paso 1: Usuario envía mensaje

```json
{
  "entry": [{
    "changes": [{
      "field": "messages",
      "value": {
        "metadata": {
          "phone_number_id": "1234567890123"
        },
        "messages": [{
          "from": "5512345678",
          "id": "wamid.D1234567890123_ABC123",
          "text": {"body": "¿Cuál es tu horario?"}
        }]
      }
    }]
  }]
}
```

### Paso 2: API recibe y parsea

```python
# webhook.py: handle_webhook()
phone_number_id = "1234567890123"  # ID del número de la empresa
sender_phone = "5512345678"         # Número del cliente
message_text = "¿Cuál es tu horario?"
```

### Paso 3: Buscar cliente en BD

```python
# database.py
customer = db.get_customer_by_phone_number_id("1234567890123")
# Retorna:
# {
#   "id": 1,
#   "name": "Hotel Paradise",
#   "phone_number_id": "1234567890123",
#   "access_token": "EAAxxxxx",
#   "system_prompt": "Eres un asistente de hotel...",
#   ...
# }
```

### Paso 4: Obtener contexto de conversación

```python
# claude_agent.py: build_conversation_context()
# Obtiene últimos 5 intercambios del mismo usuario

history = db.get_conversation_history(
  customer_id=1,
  sender_phone="5512345678",
  limit=5
)

# Convierte a formato OpenAI:
messages = [
  {"role": "user", "content": "¿Qué servicios ofrecen?"},
  {"role": "assistant", "content": "Ofrecemos spa, piscina..."},
  {"role": "user", "content": "¿Cuál es el costo?"},
  {"role": "assistant", "content": "El spa cuesta..."},
  # ... más historial
  {"role": "user", "content": "¿Cuál es tu horario?"}
]
```

### Paso 5: Llamar Claude API

```python
# claude_agent.py: generate_response()

response = client.messages.create(
  model="claude-3-5-sonnet-20241022",
  max_tokens=1024,
  system="""Eres un asistente de hotel profesional. Ayuda con:
- Información de habitaciones
- Reservas
- Servicios: spa, piscina, restaurante
- Preguntas sobre la ciudad
Sé amable y eficiente.""",
  messages=messages,  # Incluye contexto anterior
  temperature=0.7
)

# Respuesta: "Nuestro hotel está abierto de 24 horas..."
```

### Paso 6: Guardar conversación

```python
# database.py: save_conversation() + update_conversation_response()

# Guardar mensaje entrante y respuesta
db.save_conversation(
  customer_id=1,
  sender_phone="5512345678",
  message_text="¿Cuál es tu horario?",
  message_id="wamid.D1234567890123_ABC123",
  response_text="Nuestro hotel está abierto de 24 horas...",
  response_time_ms=1250
)

# Actualizar analytics
db.update_analytics(customer_id=1, response_time_ms=1250)
```

### Paso 7: Enviar respuesta a Meta

```python
# webhook.py: send_message()

POST https://graph.instagram.com/v18.0/1234567890123/messages
Authorization: Bearer EAAxxxxx
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "5512345678",
  "type": "text",
  "text": {
    "preview_url": false,
    "body": "Nuestro hotel está abierto de 24 horas..."
  }
}

# Respuesta de Meta: {"messages": [{"id": "wamid.xxx"}]}
```

### Paso 8: Meta envía respuesta al usuario

Meta reenvía el mensaje a través de WhatsApp. El usuario recibe la respuesta.

---

## 🗄️ Diseño de Base de Datos

### Tabla: customers

```sql
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,                -- ID único
  name TEXT NOT NULL,                    -- Nombre del negocio
  phone_number_id TEXT NOT NULL UNIQUE, -- ID del número en Meta
  access_token TEXT NOT NULL,            -- Token de Meta
  system_prompt TEXT,                    -- Instrucción personalizada
  api_key TEXT NOT NULL UNIQUE,          -- Para autenticar en API
  created_at TIMESTAMP,                  -- Cuándo se registró
  updated_at TIMESTAMP                   -- Última modificación
)
```

**Ejemplo:**
```
1 | Hotel Paradise | 1234567890123 | EAAxxxxx | "Eres un asistente de hotel..." | whatsapp_agent_abc123 | 2024-01-15 10:30 | 2024-01-15 10:30
```

### Tabla: conversations

```sql
CREATE TABLE conversations (
  id INTEGER PRIMARY KEY,              -- ID único
  customer_id INTEGER NOT NULL,        -- Referencia a customer
  sender_phone TEXT NOT NULL,          -- Número del usuario
  message_text TEXT NOT NULL,          -- Mensaje que envió
  response_text TEXT,                  -- Respuesta de Claude
  message_id TEXT UNIQUE,              -- ID en Meta
  timestamp TIMESTAMP,                 -- Cuándo sucedió
  response_time_ms INTEGER             -- Tiempo de respuesta
)
```

**Ejemplo:**
```
1 | 1 | 5512345678 | "¿Qué servicios tienen?" | "Ofrecemos spa, piscina..." | wamid.xxx | 2024-01-15 11:15 | 1250
2 | 1 | 5512345678 | "¿Cuál es el costo?" | "El spa cuesta..." | wamid.yyy | 2024-01-15 11:20 | 980
```

### Tabla: analytics

```sql
CREATE TABLE analytics (
  id INTEGER PRIMARY KEY,              -- ID único
  customer_id INTEGER NOT NULL,        -- Referencia a customer
  messages_count INTEGER,              -- Mensajes del día
  response_time_avg REAL,              -- Tiempo promedio
  date DATE                            -- Fecha
)
```

**Ejemplo:**
```
1 | 1 | 25 | 1150.0 | 2024-01-15
2 | 1 | 18 | 980.0  | 2024-01-14
```

---

## 🔄 Relaciones entre Módulos

```python
main.py (FastAPI)
├── Importa: database, webhook, claude_agent
├── Sirve endpoints HTTP
└── Delega procesamiento a otros módulos

webhook.py (WhatsAppWebhookHandler)
├── Importa: database, claude_agent
├── Recibe JSON de Meta
├── Procesa con Claude
└── Guarda en base de datos

claude_agent.py (ClaudeAgent)
├── Importa: database
├── Lee historial de conversaciones
├── Llama Anthropic API
└── Retorna respuesta generada

database.py (Database)
├── No importa otros módulos (independiente)
├── Maneja SQLite directamente
└── CRUD operations
```

---

## 📊 Estados de Mensajes

```
┌─────────────────────────────────────────────┐
│                   INCOMING                  │
│              Usuario → Meta → API           │
│                                             │
│  1. RECEIVED                                │
│     - Llegó a la API                        │
│     - Guardado en conversations.message_text│
│                                             │
│  2. PROCESSING                              │
│     - Claude está generando respuesta       │
│     - En memoria, no almacenado             │
│                                             │
│  3. RESPONDED                               │
│     - Claude respondió                      │
│     - Guardado en conversations.response_text
│                                             │
│  4. SENT                                    │
│     - Enviado a Meta                        │
│     - Meta lo reenviará al usuario          │
│                                             │
│  5. DELIVERED                               │
│     - Meta confirma entrega (opcional)      │
└─────────────────────────────────────────────┘
```

---

## 🎯 Puntos Clave de Arquitectura

### 1. **Multi-tenancy**
Cada cliente (empresa) es completamente independiente:
- Su propia `api_key` para acceder
- Su propio `system_prompt` para personalizar
- Su propio historial de conversaciones
- Sus propias estadísticas

### 2. **Escalabilidad**
- SQLite es suficiente para pequeños/medianos volúmenes
- PostgreSQL para escala empresarial
- Sin cambios de código necesarios

### 3. **Bajo Acoplamiento**
- Cada módulo es responsable de su tarea
- Cambios en uno no afectan a otros
- Fácil de testing

### 4. **Resiliencia**
- Los mensajes se guardan ANTES de procesar
- Si Claude falla, el mensaje sigue en la BD
- Puedes reintentar procesar

### 5. **Seguridad**
- API keys únicas por cliente
- Verification token para webhook
- HTTPS en producción
- Sin exponer datos sensibles

---

## 💰 Optimización de Costos

### Claude API
- **Entrada**: 10,000 tokens ~$0.003
- **Salida**: 2,000 tokens ~$0.03
- **Por mensaje**: ~$0.05 en promedio

### Optimizaciones
```python
1. Limitar historial a últimos 5 intercambios
   → Reduce tokens enviados a Claude
   
2. Usar Claude 3.5 Sonnet en lugar de Opus
   → 10x más barato, 95% igual de bueno
   
3. Cachear system prompts
   → No re-computar para cada mensaje
   
4. Limitar max_tokens a 1024
   → Respuestas más breves = menos tokens
```

---

## 🚀 Flujo de Despliegue

```
Tu máquina local
│
├─ Editar código
├─ Commit a GitHub
└─ Push a main
     │
     ▼
  GitHub
     │
     ├─ Webhook trigger
     └─ Notifica a Render
          │
          ▼
       Render.com
     │
     ├─ Pull código
     ├─ pip install requirements.txt
     ├─ uvicorn main:app
     └─ Deploy en vivo
          │
          ▼
       https://whatsapp-agent-xxx.onrender.com
     │
     └─ Meta envía webhooks aquí
```

---

## 🔍 Monitoreo

```
Logs disponibles:
├─ main.py: Todos los requests HTTP
├─ webhook.py: Procesamiento de mensajes
├─ claude_agent.py: Llamadas a Claude
└─ database.py: Operaciones de base de datos

Métricas importantes:
├─ response_time_ms: Cuánto tarda Claude
├─ messages_count: Volumen de mensajes
├─ API errors: Fallos en la integración
└─ Status codes: 200 OK, 401 Unauthorized, 500 Error
```

---

Esta arquitectura es **simple, escalable y producción-lista**. Cada componente puede ser mejorado independientemente sin afectar el resto del sistema. 🎯
