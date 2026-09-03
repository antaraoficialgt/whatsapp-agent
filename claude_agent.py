import os
from typing import List, Dict, Optional
from anthropic import Anthropic
from database import db
import time
import logging

logger = logging.getLogger(__name__)

class ClaudeAgent:
    def __init__(self):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY environment variable not set")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 1024
        self.temperature = 0.7

    def build_conversation_context(self, customer_id: int, sender_phone: str) -> List[Dict]:
        """Build context from previous conversations."""
        history = db.get_conversation_history(customer_id, sender_phone, limit=5)
        messages = []

        for exchange in history:
            if exchange['message_text']:
                messages.append({
                    "role": "user",
                    "content": exchange['message_text']
                })
            if exchange['response_text']:
                messages.append({
                    "role": "assistant",
                    "content": exchange['response_text']
                })

        return messages

    def generate_response(self, customer_id: int, sender_phone: str, message_text: str) -> tuple[str, int]:
        """Generate response using Claude API with conversation memory."""
        try:
            # Get customer configuration
            customer = db.get_customer_by_id(customer_id)
            if not customer:
                logger.error(f"Customer {customer_id} not found")
                return "Disculpa, no puedo procesar tu mensaje en este momento.", 0

            system_prompt = customer.get('system_prompt') or self._get_default_system_prompt()

            # Build conversation history
            messages = self.build_conversation_context(customer_id, sender_phone)

            # Add current message
            messages.append({
                "role": "user",
                "content": message_text
            })

            start_time = time.time()

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages,
                temperature=self.temperature
            )

            response_time_ms = int((time.time() - start_time) * 1000)
            response_text = response.content[0].text

            logger.info(f"Claude response generated for {sender_phone} in {response_time_ms}ms")
            return response_text, response_time_ms

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Lo siento, hubo un error procesando tu mensaje. Intenta de nuevo.", 0

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for customer service."""
        return """Eres un agente de atención al cliente amable, profesional y eficiente.
Tu objetivo es:
1. Responder preguntas de los clientes de manera clara y concisa
2. Ser empático y cortés en todas las interacciones
3. Proporcionar información útil y relevante
4. Resolver problemas o dirigir al cliente al departamento correcto
5. Mantener un tono profesional pero amigable

Responde siempre en el idioma del cliente. Sé breve y directo en tus respuestas.
Si no puedes resolver algo, explica claramente qué pasos seguir."""

    @staticmethod
    def get_system_prompts_examples() -> Dict[str, str]:
        """Provide example system prompts for different industries."""
        return {
            "hotel": """Eres un asistente de hotel profesional y amable.
Tu objetivo es:
1. Responder preguntas sobre habitaciones, servicios e instalaciones
2. Ayudar con reservas y cambios de booking
3. Proporcionar información sobre check-in/check-out
4. Sugerir servicios y actividades del hotel
5. Resolver quejas de forma profesional

Sé cortés, eficiente y siempre ofrece soluciones.""",

            "restaurant": """Eres un asistente de restaurante profesional.
Tu objetivo es:
1. Proporcionar información del menú y recomendaciones
2. Recibir reservas y pedidos
3. Responder preguntas sobre ingredientes, alergias y preparación
4. Ofrecer promociones especiales
5. Manejar cambios o cancelaciones

Sé entusiasta sobre nuestros platillos y siempre cortés con los clientes.""",

            "ecommerce": """Eres un asistente de e-commerce experto y amable.
Tu objetivo es:
1. Ayudar a los clientes a encontrar productos
2. Responder preguntas sobre disponibilidad, precios y envíos
3. Asistir en el proceso de compra
4. Manejar devoluciones y cambios
5. Proporcionar información de rastreo de pedidos

Sé persuasivo pero honesto, y siempre prioriza la satisfacción del cliente."""
        }
