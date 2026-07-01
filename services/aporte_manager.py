from collections import defaultdict
from models.aporte import Aporte


class AporteManager:

    def __init__(self):

        # user_id -> {aporte_id: Aporte}
        self.aportes = defaultdict(dict)

        # user_id -> aporte activo
        self.active = {}

    # -------------------------------------------------
    # CREAR APORTE
    # -------------------------------------------------

    def iniciar_aporte(self, user_id):

        aporte = Aporte()

        self.aportes[user_id][aporte.id] = aporte
        self.active[user_id] = aporte.id

        return aporte

    # -------------------------------------------------
    # OBTENER APORTE ACTIVO
    # -------------------------------------------------

    def get_active(self, user_id):

        aporte_id = self.active.get(user_id)

        if not aporte_id:
            return None

        return self.aportes[user_id].get(aporte_id)

    # -------------------------------------------------
    # COMENTARIO
    # -------------------------------------------------

    def set_comentario(self, user_id, comentario):

        aporte = self.get_active(user_id)

        if not aporte:
            return

        aporte.comentario = comentario
        aporte.estado = "WAITING_MEDIA"

    # -------------------------------------------------
    # TIMELINE
    # -------------------------------------------------

    def agregar_archivo(self, user_id, file_id, tipo):

        aporte = self.get_active(user_id)

        if not aporte:
            return

        aporte.timeline.append({
            "tipo": tipo,
            "file_id": file_id
        })

    def crear_album(self, user_id, media_group_id):

        aporte = self.get_active(user_id)

        if not aporte:
            return

        album = {
            "tipo": "album",
            "media_group_id": media_group_id,
            "items": []
        }

        aporte.timeline.append(album)

        return album

    def obtener_album(self, user_id, media_group_id):

        aporte = self.get_active(user_id)

        if not aporte:
            return None

        for item in aporte.timeline:

            if (
                item["tipo"] == "album"
                and item["media_group_id"] == media_group_id
            ):
                return item

        return None

    def agregar_album_archivo(self, user_id, media_group_id, file_id, tipo):

        album = self.obtener_album(user_id, media_group_id)

        if album is None:
            album = self.crear_album(user_id, media_group_id)

        album["items"].append({
            "tipo": tipo,
            "file_id": file_id
        })

    # -------------------------------------------------
    # CONTADOR
    # -------------------------------------------------

    def contar(self, user_id):

        aporte = self.get_active(user_id)

        contador = {
            "photo": 0,
            "video": 0,
            "document": 0,
            "audio": 0
        }

        if not aporte:
            return contador

        for item in aporte.timeline:

            if item["tipo"] == "album":

                for archivo in item["items"]:

                    if archivo["tipo"] in contador:
                        contador[archivo["tipo"]] += 1

            else:

                if item["tipo"] in contador:
                    contador[item["tipo"]] += 1

        return contador

    # -------------------------------------------------
    # STATUS PANEL
    # -------------------------------------------------

    def set_status(self, user_id, message_id):

        aporte = self.get_active(user_id)

        if aporte:
            aporte.status_message_id = message_id

    def get_status(self, user_id):

        aporte = self.get_active(user_id)

        if not aporte:
            return None

        return aporte.status_message_id

    # -------------------------------------------------
    # LIMPIAR
    # -------------------------------------------------

    def limpiar(self, user_id):

        aporte_id = self.active.pop(user_id, None)

        if aporte_id:

            self.aportes[user_id].pop(aporte_id, None)


manager = AporteManager()