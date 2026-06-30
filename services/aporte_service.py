from datetime import datetime


class AporteService:

    def __init__(self):

        self.usuarios = {}
        self.version = {}

    # -------------------------------------------------
    # APORTE
    # -------------------------------------------------

    def iniciar_aporte(self, user_id):

        self.usuarios[user_id] = {
            "estado": "WAITING_COMMENT",
            "comentario": "",
            "archivos": [],          # archivos individuales
            "albums": {},            # media_group_id -> lista de archivos
            "inicio": datetime.now(),
            "status_message_id": None
        }

        self.version[user_id] = 0

    def existe_aporte(self, user_id):
        return user_id in self.usuarios

    def get(self, user_id):
        return self.usuarios.get(user_id)

    # -------------------------------------------------
    # COMENTARIO
    # -------------------------------------------------

    def set_comentario(self, user_id, comentario):

        aporte = self.get(user_id)

        if aporte is None:
            return

        aporte["comentario"] = comentario
        aporte["estado"] = "WAITING_MEDIA"

    # -------------------------------------------------
    # ARCHIVOS SUELTOS
    # -------------------------------------------------

    def agregar_archivo(self, user_id, file_id, tipo):

        aporte = self.get(user_id)

        if aporte is None:
            return

        aporte["archivos"].append({
            "tipo": tipo,
            "file_id": file_id
        })

    # -------------------------------------------------
    # ÁLBUMES
    # -------------------------------------------------

    def agregar_album_archivo(self, user_id, media_group_id, file_id, tipo):

        aporte = self.get(user_id)

        if aporte is None:
            return

        if media_group_id not in aporte["albums"]:
            aporte["albums"][media_group_id] = []

        aporte["albums"][media_group_id].append({
            "tipo": tipo,
            "file_id": file_id
        })

    # -------------------------------------------------
    # CONTADORES
    # -------------------------------------------------

    def contar_archivos(self, user_id):

        aporte = self.get(user_id)

        contador = {
            "photo": 0,
            "video": 0,
            "document": 0,
            "audio": 0
        }

        if aporte is None:
            return contador

        for archivo in aporte["archivos"]:

            if archivo["tipo"] in contador:
                contador[archivo["tipo"]] += 1

        for album in aporte["albums"].values():

            for archivo in album:

                if archivo["tipo"] in contador:
                    contador[archivo["tipo"]] += 1

        return contador

    # -------------------------------------------------
    # PANEL
    # -------------------------------------------------

    def get_status_message(self, user_id):

        aporte = self.get(user_id)

        if aporte is None:
            return None

        return aporte["status_message_id"]

    def set_status_message(self, user_id, message_id):

        aporte = self.get(user_id)

        if aporte is None:
            return

        aporte["status_message_id"] = message_id

    # -------------------------------------------------
    # DEBOUNCE
    # -------------------------------------------------

    def bump_version(self, user_id):

        self.version[user_id] = self.version.get(user_id, 0) + 1

        return self.version[user_id]

    def get_version(self, user_id):

        return self.version.get(user_id, 0)

    # -------------------------------------------------
    # LIMPIEZA
    # -------------------------------------------------

    def limpiar(self, user_id):

        self.usuarios.pop(user_id, None)
        self.version.pop(user_id, None)


service = AporteService()