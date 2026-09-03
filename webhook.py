import requests
import json
import logging
from typing import Dict, Optional
from database import db
from claude_agent import ClaudeAgent

logger = logging.getLogger(__name__)

class WhatsAppWebhookHandler:
    def __init__(self):
        self.claude_agent = ClaudeAgent()

    def handle_webhook(self, data: Dict) -> bool:
        """Process incoming webhook from Meta WhatsApp."""
        try:
            # Meta sends changes array
            if "entry" not in data or not data["entry"]:
                return True

            for entry in data["entry"]:
                # Find messaging changes
                if "changes" not in entry:
                    continue

                for change in entry["changes"]:
                    if change.get("field") != "messages":
                        continue

                    value = change.get("value", {})

                    # Extract phone number ID (identifies customer)
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")
                    if not phone_number_id:
                        logger.warning("No phone_number_id in webhook")
                        continue

                    # Get customer configuration
                    customer = db.get_customer_by_phone_number_id(phone_number_id)
                    if not customer:
                        logger.warning(f"Customer not found for phone_number_id: {phone_number_id}")
                        continue

                    # Process messages
                    if "messages" in value:
                        for message in value["messages"]:
                            self._process_message(customer, message)

                    # Handle delivery confirmations
                    if "statuses" in value:
                        for status in value["statuses"]:
                            self._process_status(status)

            return True

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False

    def _process_message(self, customer: Dict, message: Dict) -> bool:
        """Process a single incoming message."""
        try:
            sender_phone = message.get("from")
            message_id = message.get("id")
            timestamp = message.get("timestamp")

            # Extract message content
            message_text = self._extract_message_text(message)
            if not message_text:
                logger.warning(f"Could not extract message text from {sender_phone}")
                return False

            logger.info(f"Processing message from {sender_phone}: {message_text[:50]}...")

            # Save incoming message
            conversation_id = db.save_conversation(
                customer_id=customer["id"],
                sender_phone=sender_phone,
                message_text=message_text,
                message_id=message_id
            )

            # Generate response using Claude
            response_text, response_time_ms = self.claude_agent.generate_response(
                customer_id=customer["id"],
                sender_phone=sender_phone,
                message_text=message_text
            )

            # Save response
            db.update_conversation_response(
                conversation_id=conversation_id,
                response_text=response_text,
                response_time_ms=response_time_ms
            )

            # Update analytics
            db.update_analytics(customer["id"], response_time_ms)

            # Send response back via WhatsApp API
            success = self.send_message(
                customer=customer,
                recipient_phone=sender_phone,
                message_text=response_text
            )

            if success:
                logger.info(f"Response sent to {sender_phone}")
            else:
                logger.error(f"Failed to send response to {sender_phone}")

            return success

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return False

    def _extract_message_text(self, message: Dict) -> Optional[str]:
        """Extract text content from different message types."""
        if "text" in message:
            return message["text"].get("body")
        elif "interactive" in message:
            interactive = message["interactive"]
            if "button_reply" in interactive:
                return interactive["button_reply"].get("title")
            elif "list_reply" in interactive:
                return interactive["list_reply"].get("title")
        return None

    def _process_status(self, status: Dict) -> bool:
        """Process message delivery/read status."""
        try:
            message_id = status.get("id")
            status_type = status.get("status")  # sent, delivered, read, failed

            logger.info(f"Message {message_id} status: {status_type}")
            # Could extend this to track delivery metrics
            return True

        except Exception as e:
            logger.error(f"Error processing status: {str(e)}")
            return False

    def send_message(self, customer: Dict, recipient_phone: str, message_text: str) -> bool:
        """Send message back to WhatsApp user via Meta API."""
        try:
            phone_number_id = customer["phone_number_id"]
            access_token = customer["access_token"]
            api_version = "v18.0"

            url = f"https://graph.instagram.com/{api_version}/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Message sent successfully to {recipient_phone}")
                return True
            else:
                logger.error(
                    f"Failed to send message: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"Request error sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    def verify_webhook(self, verify_token: str, challenge: str, received_token: str) -> Optional[str]:
        """Verify webhook with Meta."""
        if verify_token == received_token:
            return challenge
        return None
