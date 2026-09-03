# WhatsApp Business Agent API 🤖

Sistema completo de atención al cliente 24/7 para WhatsApp Business usando Claude API. Permite que empresas integren agentes IA automáticos a sus números de WhatsApp Business.

## 🎯 Características

- ✅ Recibe mensajes automáticamente desde WhatsApp Business
- ✅ Genera respuestas inteligentes usando Claude API
- ✅ Mantiene contexto de conversaciones por usuario
- ✅ Sistema de prompts personalizados por cliente
- ✅ Base de datos SQLite para historial completo
- ✅ Analytics en tiempo real (mensajes, tiempo de respuesta)
- ✅ API segura con autenticación por API Key
- ✅ Soporte multi-cliente (múltiples empresas)

## 📋 Requisitos Previos

### Antes de Comenzar

1. **Cuenta Anthropic API** - Obtén tu API key en [console.anthropic.com](https://console.anthropic.com)
   - Necesitarás una tarjeta de crédito vinculada
   - Modelo recomendado: Claude 3.5 Sonnet (más económico y rápido)

2. **Meta Business Account** con:
   - WhatsApp Business API acceso
   - App ID y Token de acceso
   - Número de teléfono verificado
   - Número de ID de teléfono

3. **Servidor/Hosting** para ejecutar el backend
   - Render.com (recomendado - $7/mes)
   - Railway.app
   - AWS EC2
   - VPS propio

4. **Python 3.11+**

## 🚀 Instalación Local

### 1. Clonar/Descargar el proyecto

```bash
cd whatsapp-agent
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
# Obtén en https://console.anthropic.com
CLAUDE_API_KEY=sk-ant-v0-xxxxxxxxxxxxx

# Token para verificar webhook (puedes crear uno)
WEBHOOK_VERIFY_TOKEN=tu-token-secreto-aqui-1234567890

# Para seguridad de API
SECRET_KEY=tu-clave-secreta-super-fuerte-1234567890

# Base de datos
DATABASE_URL=sqlite:///./conversations.db

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

### 5. Inicializar base de datos

```bash
python -c "from database import db; print('Database initialized')"
```

### 6. Ejecutar servidor localmente

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Verificar que funciona

```bash
curl http://localhost:8000/health
```

Deberías recibir:
```json
{"status": "healthy", "service": "WhatsApp Business Agent API"}
```

---

## 📱 Configuración de Meta WhatsApp Business API

### Paso 1: Obtener Credenciales de Meta

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Crea una aplicación (o usa una existente)
3. En **Configuración > General**, obtén:
   - **App ID**
   - **App Secret**

4. En **WhatsApp > Primeros pasos**, obtén:
   - **Phone Number ID** (identificador de tu número de WhatsApp)
   - **Access Token** (token de acceso de la app)

### Paso 2: Crear Cliente en tu API

Llama a este endpoint para registrar tu negocio:

```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Negocio",
    "phone_number_id": "1234567890123",
    "access_token": "EAAxxxxxxxxxxxxxx",
    "system_prompt": "Eres un asistente de hotel. Ayuda a los clientes con reservas, preguntas sobre habitaciones y servicios..."
  }'
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Mi Negocio",
  "phone_number_id": "1234567890123",
  "api_key": "whatsapp_agent_abc123xyz...",
  "message": "Guarda tu API key en un lugar seguro. No podrá ser recuperada."
}
```

⚠️ **GUARDA EL API_KEY EN UN LUGAR SEGURO** - Lo necesitarás para acceder a tu información.

### Paso 3: Configurar Webhook en Meta

1. Ve a tu app en developers.facebook.com
2. En **Configuración > Webhooks**
3. Haz clic en **Suscribirse a webhooks**
4. Configura:
   - **URL de devolución de llamada**: `https://tu-dominio.com/webhook`
   - **Token de verificación**: El mismo que en tu `.env` (`WEBHOOK_VERIFY_TOKEN`)
5. Suscribirse a: `messages`, `message_status`

Meta hará una solicitud GET a `/webhook` para verificar. Tu API debe responder correctamente.

---

## 🚀 Despliegue en Render.com (Recomendado)

### Opción Más Fácil: Conectar GitHub

1. Sube tu proyecto a GitHub
2. Ve a [render.com](https://render.com) y crea una cuenta
3. Haz clic en **New +** > **Web Service**
4. Conecta tu repositorio de GitHub
5. Configura:
   - **Name**: `whatsapp-agent`
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. En **Environment**, añade:
   ```
   CLAUDE_API_KEY=sk-ant-v0-xxx...
   WEBHOOK_VERIFY_TOKEN=tu-token-secreto
   SECRET_KEY=tu-clave-fuerte
   ```
7. Haz clic en **Deploy**

Tu URL será algo como: `https://whatsapp-agent-xxxx.onrender.com`

### Opción Manual: Deploy Docker

```bash
# Crear Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# En Render: New > Web Service > Deploy from Docker
```

---

## 🧪 Pruebas con cURL

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Enviar Mensaje Manual

```bash
curl -X POST http://localhost:8000/send-message \
  -H "Authorization: Bearer whatsapp_agent_abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_phone": "5512345678",
    "message_text": "Hola! Este es un mensaje de prueba"
  }'
```

### 3. Ver Conversaciones

```bash
curl http://localhost:8000/conversations \
  -H "Authorization: Bearer whatsapp_agent_abc123xyz..."
```

### 4. Ver Historial con Contacto

```bash
curl http://localhost:8000/conversations/5512345678 \
  -H "Authorization: Bearer whatsapp_agent_abc123xyz..."
```

### 5. Ver Analytics

```bash
curl http://localhost:8000/analytics?days=7 \
  -H "Authorization: Bearer whatsapp_agent_abc123xyz..."
```

### 6. Obtener Prompts de Ejemplo

```bash
curl http://localhost:8000/system-prompts/examples
```

### 7. Simular Webhook de Meta (Test)

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "metadata": {
            "phone_number_id": "1234567890123"
          },
          "messages": [{
            "from": "5512345678",
            "id": "wamid.xxx",
            "timestamp": "1234567890",
            "text": {
              "body": "Hola, necesito ayuda"
            }
          }]
        }
      }]
    }]
  }'
```

---

## 💰 Costos Estimados

### Claude API (Anthropic)
- **Claude 3.5 Sonnet**: 
  - Input: $3 por 1M tokens
  - Output: $15 por 1M tokens
- **Estimación**: $0.001 - $0.005 por mensaje

### Hosting
- **Render.com**: $7/mes (starter)
- **Railway**: $5/mes
- **AWS**: Variable, típicamente $10-20/mes

### Meta WhatsApp
- Primeros 1,000 mensajes: Gratis
- Después: $0.0079 - $0.0177 por mensaje según región

**Total estimado para negocio pequeño**: $20-30/mes

---

## 🔒 Seguridad

### Best Practices

1. **Nunca compartas tu API Key** - Se puede regenerar pero es incómodo
2. **Usa HTTPS** en producción - Render.com lo proporciona automáticamente
3. **Guarda credenciales en variables de entorno** - Nunca en código
4. **Limpia logs sensibles** - No guardes números de teléfono en logs
5. **Backup regular** - Descarga tu base de datos `conversations.db` regularmente

### Regenerar API Key

Si tu API key se compromete, contacta a tu admin para regenerarla.

---

## 📊 Estructura de Base de Datos

### Tabla: customers
```sql
- id: ID único del cliente
- name: Nombre del negocio
- phone_number_id: ID del número de WhatsApp
- access_token: Token de acceso Meta
- system_prompt: Instrucción personalizada para Claude
- api_key: Clave para acceder a la API
- created_at: Fecha de creación
```

### Tabla: conversations
```sql
- id: ID único de conversación
- customer_id: ID del cliente
- sender_phone: Teléfono del usuario
- message_text: Mensaje recibido
- response_text: Respuesta de Claude
- message_id: ID del mensaje en Meta
- timestamp: Fecha/hora
- response_time_ms: Tiempo de respuesta
```

### Tabla: analytics
```sql
- id: ID único
- customer_id: ID del cliente
- messages_count: Mensajes del día
- response_time_avg: Tiempo promedio de respuesta
- date: Fecha
```

---

## 🛠️ Solución de Problemas

### "CLAUDE_API_KEY not set"
```bash
# Verifica que tu .env existe y tiene la clave
cat .env | grep CLAUDE_API_KEY

# O establécela directamente
export CLAUDE_API_KEY=sk-ant-v0-xxx...
```

### "Webhook verification failed"
1. Verifica que `WEBHOOK_VERIFY_TOKEN` es idéntico en `.env` y Meta
2. Asegúrate que tu servidor es accesible públicamente (no localhost)
3. Intenta verificar de nuevo en Meta

### "Customer not found for phone_number_id"
1. Verifica que registraste el cliente con `/customers`
2. Confirma que `phone_number_id` es correcto en Meta
3. Verifica que el token de acceso sigue siendo válido

### "Failed to send message"
1. Verifica el `access_token` en tu cliente
2. Asegúrate que el número de teléfono está en formato internacional (ej: 5512345678)
3. Revisa logs en `/customers/me` para ver la configuración

### Logs detallados
```bash
# En .env, cambia a:
LOG_LEVEL=DEBUG

# Luego reinicia el servidor
```

---

## 📝 Ejemplos de System Prompts

### Hotel
```
Eres un asistente de hotel profesional. Ayuda con:
- Información de habitaciones y disponibilidad
- Reservas y cambios de booking
- Check-in/check-out
- Servicios: spa, piscina, restaurante, tours
- Preguntas sobre la ciudad
Sé amable, eficiente y ofrece soluciones siempre.
```

### Restaurante
```
Eres un mesero virtual del restaurante XYZ. Ayuda con:
- Información del menú y recomendaciones
- Recibir reservas y pedidos a domicilio
- Ingredientes y alergias
- Promociones especiales
- Cambios y cancelaciones
Sé entusiasta y siempre cortés.
```

### E-commerce
```
Eres un vendedor experto de tienda online. Ayuda con:
- Búsqueda de productos
- Disponibilidad, precios y envíos
- Proceso de compra
- Rastreo de pedidos
- Devoluciones y cambios
Sé persuasivo pero honesto. Prioriza satisfacción del cliente.
```

---

## 🔄 API Endpoints Reference

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Verificar estado del servicio |
| GET | `/webhook` | Verificar webhook con Meta |
| POST | `/webhook` | Recibir mensajes de WhatsApp |
| POST | `/customers` | Crear nuevo cliente |
| GET | `/customers/me` | Ver información del cliente |
| PUT | `/customers/me` | Actualizar configuración |
| GET | `/conversations` | Ver conversaciones recientes |
| GET | `/conversations/{phone}` | Ver historial con contacto |
| GET | `/analytics` | Ver estadísticas |
| GET | `/system-prompts/examples` | Ver prompts de ejemplo |
| POST | `/send-message` | Enviar mensaje manual |

---

## 📚 Recursos Útiles

- [Documentación de Claude API](https://docs.anthropic.com)
- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Render.com Deploy Guide](https://render.com/docs)

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs del servidor
2. Verifica que todas las variables de entorno están correctas
3. Prueba los endpoints con cURL
4. Revisa la documentación de Meta sobre API changes

---

## 📄 Licencia

Este proyecto es de código abierto. Úsalo libremente para tu negocio.

---

**¡Listo! Tu sistema de atención al cliente 24/7 está configurado.** 🎉
