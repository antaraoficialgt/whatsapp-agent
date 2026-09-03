# Guía de Pruebas - WhatsApp Agent API

Esta guía te muestra cómo probar todos los endpoints de tu API.

## ⚙️ Configuración Inicial

### 1. Crear un Cliente de Prueba

```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hotel Paradise",
    "phone_number_id": "1234567890123",
    "access_token": "EAAxxxxxxxxxxxxx",
    "system_prompt": "Eres un asistente de hotel. Ayuda a los huéspedes con reservas, información de habitaciones, servicios y actividades. Sé amable y eficiente."
  }'
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "name": "Hotel Paradise",
  "phone_number_id": "1234567890123",
  "api_key": "whatsapp_agent_abcdef123456",
  "message": "Guarda tu API key en un lugar seguro. No podrá ser recuperada."
}
```

⚠️ **Guarda el `api_key`** - Lo necesitarás para todas las pruebas siguientes.

---

## 🧪 Pruebas de Endpoints

### Variables para reutilizar

```bash
# Después de crear el cliente, establece estas variables
API_KEY="whatsapp_agent_abcdef123456"  # Tu API key
BASE_URL="http://localhost:8000"
AUTH_HEADER="Authorization: Bearer $API_KEY"
```

### 1. Health Check

```bash
curl $BASE_URL/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "WhatsApp Business Agent API"
}
```

### 2. Ver Información del Cliente

```bash
curl $BASE_URL/customers/me \
  -H "$AUTH_HEADER"
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Hotel Paradise",
  "phone_number_id": "1234567890123",
  "created_at": "2024-01-15 10:30:45",
  "updated_at": "2024-01-15 10:30:45"
}
```

### 3. Actualizar System Prompt

```bash
curl -X PUT $BASE_URL/customers/me \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Eres un asistente de restaurante. Ayuda con reservas, menú y información de platillos. Sé entusiasta y recomendador de nuestras especialidades."
  }'
```

**Respuesta:**
```json
{
  "status": "updated"
}
```

### 4. Ver Prompts de Ejemplo

```bash
curl $BASE_URL/system-prompts/examples
```

**Respuesta:**
```json
{
  "hotel": "Eres un asistente de hotel profesional...",
  "restaurant": "Eres un asistente de restaurante...",
  "ecommerce": "Eres un asistente de e-commerce..."
}
```

### 5. Ver Conversaciones (Vacío al inicio)

```bash
curl $BASE_URL/conversations \
  -H "$AUTH_HEADER"
```

**Respuesta inicial:**
```json
{
  "total": 0,
  "conversations": []
}
```

---

## 📨 Simular Webhooks de Meta

### 6. Simular Mensaje Entrante

Meta enviará un JSON como este. Para pruebas locales, puedes simularlo:

```bash
curl -X POST $BASE_URL/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [
      {
        "changes": [
          {
            "field": "messages",
            "value": {
              "metadata": {
                "phone_number_id": "1234567890123"
              },
              "messages": [
                {
                  "from": "5512345678",
                  "id": "wamid.D1234567890123_ABC123",
                  "timestamp": "1705326645",
                  "text": {
                    "body": "Hola, ¿cuál es el precio de la habitación doble?"
                  }
                }
              ]
            }
          }
        ]
      }
    ]
  }'
```

**Respuesta esperada:**
```json
{
  "status": "received"
}
```

⚠️ **Nota**: Este mensaje será procesado por Claude y respondido automáticamente (si usas credenciales reales de Meta).

### 7. Ver la Conversación Guardada

Después de simular el mensaje anterior:

```bash
curl $BASE_URL/conversations \
  -H "$AUTH_HEADER"
```

**Respuesta (ejemplo):**
```json
{
  "total": 1,
  "conversations": [
    {
      "id": 1,
      "customer_id": 1,
      "sender_phone": "5512345678",
      "message_text": "Hola, ¿cuál es el precio de la habitación doble?",
      "response_text": "Contamos con habitaciones dobles a partir de $150 USD por noche. Incluye desayuno buffet y acceso a la piscina. ¿Deseas conocer más detalles?",
      "message_id": "wamid.D1234567890123_ABC123",
      "timestamp": "2024-01-15 11:15:30",
      "response_time_ms": 1250
    }
  ]
}
```

### 8. Ver Historial con Contacto Específico

```bash
curl $BASE_URL/conversations/5512345678 \
  -H "$AUTH_HEADER"
```

**Respuesta:**
```json
{
  "sender_phone": "5512345678",
  "total": 1,
  "messages": [
    {
      "message_text": "Hola, ¿cuál es el precio de la habitación doble?",
      "response_text": "Contamos con habitaciones dobles a partir de $150 USD...",
      "timestamp": "2024-01-15 11:15:30"
    }
  ]
}
```

---

## 📊 Analytics

### 9. Ver Analytics

```bash
curl "$BASE_URL/analytics?days=30" \
  -H "$AUTH_HEADER"
```

**Respuesta (ejemplo):**
```json
{
  "period_days": 30,
  "total_records": 1,
  "analytics": [
    {
      "id": 1,
      "customer_id": 1,
      "messages_count": 1,
      "response_time_avg": 1250.0,
      "date": "2024-01-15"
    }
  ]
}
```

### 10. Analytics últimos 7 días

```bash
curl "$BASE_URL/analytics?days=7" \
  -H "$AUTH_HEADER"
```

---

## ✉️ Enviar Mensajes Manuales

### 11. Enviar Mensaje Manual (Admin)

Útil para notificaciones, promociones o respuestas manuales:

```bash
curl -X POST $BASE_URL/send-message \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_phone": "5512345678",
    "message_text": "¡Hola! Queremos ofrecerte un 20% de descuento en tu próxima reserva. ¿Interesado?"
  }'
```

**Respuesta (si credenciales Meta son válidas):**
```json
{
  "status": "sent"
}
```

**Si falla:**
```json
{
  "error": "Failed to send message"
}
```

---

## 🔐 Pruebas de Autenticación

### 12. Acceso sin API Key

```bash
curl $BASE_URL/customers/me
```

**Respuesta:**
```json
{
  "error": "Missing Authorization header"
}
```

### 13. API Key inválida

```bash
curl $BASE_URL/customers/me \
  -H "Authorization: Bearer invalid_key_12345"
```

**Respuesta:**
```json
{
  "error": "Invalid API key"
}
```

### 14. Formato incorrecto

```bash
curl $BASE_URL/customers/me \
  -H "Authorization: invalidtoken"
```

**Respuesta:**
```json
{
  "error": "Invalid authorization format"
}
```

---

## 🌐 Verificación de Webhook con Meta

### 15. Verificar Webhook (GET)

Meta hace un GET a `/webhook` con estos parámetros:

```bash
curl "$BASE_URL/webhook?hub_mode=subscribe&hub_challenge=abc123&hub_verify_token=tu-webhook-verify-token-aqui"
```

**Respuesta correcta:**
```
abc123
```

**Respuesta incorrecta:**
```json
{
  "error": "Invalid verification token"
}
```

---

## 📝 Ejemplo: Flujo Completo de Conversación

```bash
# 1. Crear cliente (simulando cliente nuevo)
API_KEY=$(curl -s -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restaurante El Buen Sabor",
    "phone_number_id": "9876543210",
    "access_token": "EAABC123",
    "system_prompt": "Eres mesero del restaurante El Buen Sabor. Ayuda con reservas, menú y recomendaciones. Sé amable."
  }' | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)

echo "API Key: $API_KEY"

# 2. Verificar que el cliente se creó
curl http://localhost:8000/customers/me \
  -H "Authorization: Bearer $API_KEY"

# 3. Simular primer mensaje
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "metadata": {"phone_number_id": "9876543210"},
          "messages": [{
            "from": "5511987654",
            "id": "msg1",
            "timestamp": "1705326645",
            "text": {"body": "Hola, ¿qué platos del menú me recomiendan?"}
          }]
        }
      }]
    }]
  }'

# 4. Ver la conversación guardada
curl http://localhost:8000/conversations \
  -H "Authorization: Bearer $API_KEY"

# 5. Simular segundo mensaje del mismo usuario
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "metadata": {"phone_number_id": "9876543210"},
          "messages": [{
            "from": "5511987654",
            "id": "msg2",
            "timestamp": "1705326700",
            "text": {"body": "¿Tienen opciones vegetarianas?"}
          }]
        }
      }]
    }]
  }'

# 6. Ver historial completo con ese contacto
curl http://localhost:8000/conversations/5511987654 \
  -H "Authorization: Bearer $API_KEY"

# 7. Ver analytics
curl "http://localhost:8000/analytics?days=1" \
  -H "Authorization: Bearer $API_KEY"
```

---

## 🐛 Debugging

### Ver Logs del Servidor

Si ejecutas con DEBUG:

```bash
# En terminal, durante el desarrollo:
python -m uvicorn main:app --reload --log-level debug
```

Verás logs detallados como:
```
INFO:     Processing message from 5512345678: Hola, ¿cuál es...
INFO:     Claude response generated for 5512345678 in 1250ms
INFO:     Response sent to 5512345678
```

### Verificar Base de Datos

```bash
# Listar tablas
sqlite3 conversations.db ".tables"

# Ver conversaciones
sqlite3 conversations.db "SELECT * FROM conversations;"

# Ver clientes
sqlite3 conversations.db "SELECT id, name, phone_number_id FROM customers;"
```

---

## 🚨 Errores Comunes

### "Customer not found for phone_number_id"
```
✅ Solución: Verifica que phone_number_id en webhook coincide con el registrado
```

### "CLAUDE_API_KEY not set"
```
✅ Solución: export CLAUDE_API_KEY=sk-ant-v0-xxx...
```

### "Connection refused"
```
✅ Solución: Asegúrate que el servidor está corriendo en puerto 8000
```

### "Invalid API key"
```
✅ Solución: Copia exactamente el api_key del response anterior
```

---

**¡Listo para probar!** Usa estos ejemplos para verificar que todo funciona correctamente. 🎉
