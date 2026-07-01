from datetime import datetime
import uuid


class Aporte:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.estado = "WAITING_COMMENT"
        self.comentario = ""

        # Cada elemento representa el mensaje original recibido por el bot.
        # Conservar chat_id y message_id permite copiarlo después sin perder
        # captions, spoilers, nombres de archivo ni agrupación de álbumes.
        self.timeline = []
        self.message_ids = set()

        self.created_at = datetime.now()
        self.status_message_id = None

        # Evita dobles pulsaciones y permite reanudar un envío parcial sin
        # volver a duplicar todo lo que ya llegó a un destino.
        self.sending = False
        self.delivery_progress = {}
