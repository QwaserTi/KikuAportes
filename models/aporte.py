from datetime import datetime
import uuid


class Aporte:

    def __init__(self):
        # Identificador único del aporte
        self.id = str(uuid.uuid4())

        # Estado del flujo
        self.estado = "WAITING_COMMENT"

        # Comentario del usuario
        self.comentario = ""

        # Línea de tiempo del aporte.
        # Aquí se guardará TODO respetando el orden:
        #
        # [
        #     {"tipo": "album", "media_group_id": "...", "items": [...]},
        #     {"tipo": "video", "file_id": "..."},
        #     {"tipo": "photo", "file_id": "..."},
        #     {"tipo": "document", "file_id": "..."}
        # ]
        #
        self.timeline = []

        # Fecha de creación
        self.created_at = datetime.now()

        # Mensaje del panel "Aporte en progreso"
        self.status_message_id = None