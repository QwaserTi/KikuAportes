from datetime import datetime
import uuid


class Aporte:

    def __init__(self):
        self.id = str(uuid.uuid4())

        self.estado = "WAITING_COMMENT"
        self.comentario = ""

        self.archivos = []
        self.albums = {}

        self.created_at = datetime.now()

        self.status_message_id = None