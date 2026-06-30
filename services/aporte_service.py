from datetime import datetime


class AporteService:
    def __init__(self):
        self.usuarios = {}
        self.timers = {}
        self.version = {}

    # ---------------- APORTE ----------------

    def iniciar_aporte(self, user_id):
        self.usuarios[user_id] = {
            "estado": "WAITING_COMMENT",
            "comentario": "",
            "archivos": [],          # archivos sueltos
            "albums": {},           # 🔥 NUEVO: álbumes separados
            "inicio": datetime.now(),
            "status_message_id": None
        }
        self.version[user_id] = 0

    def existe_aporte(self, user_id):
        return user_id in self.usuarios

    def get(self, user_id):
        return self.usuarios.get(user_id)

    # ---------------- COMENTARIO ----------------

    def set_comentario(self, user_id, comentario):
        aporte = self.get(user_id)
        if not aporte:
            return
        aporte["comentario"] = comentario
        aporte["estado"] = "WAITING_MEDIA"

    # ---------------- ARCHIVOS SUELTOS ----------------

    def agregar_archivo(self, user_id, file_id, tipo):
        aporte = self.get(user_id)
        if not aporte:
            return

        aporte["archivos"].append({
            "file_id": file_id,
            "tipo": tipo
        })

    # ---------------- ÁLBUMES ----------------

    def agregar_album_archivo(self, user_id, album_id, file_id, tipo):
        """
        🔥 Guarda archivos agrupados por media_group_id
        """

        aporte = self.get(user_id)
        if not aporte:
            return

        if album_id not in aporte["albums"]:
            aporte["albums"][album_id] = []

        aporte["albums"][album_id].append({
            "file_id": file_id,
            "tipo": tipo
        })

    # ---------------- CONTADORES ----------------

    def contar_archivos(self, user_id):
        aporte = self.get(user_id)
        if not aporte:
            return {"photo": 0, "video": 0, "document": 0, "audio": 0}

        contador = {"photo": 0, "video": 0, "document": 0, "audio": 0}

        # sueltos
        for a in aporte["archivos"]:
            if a["tipo"] in contador:
                contador[a["tipo"]] += 1

        # álbumes
        for album in aporte["albums"].values():
            for a in album:
                if a["tipo"] in contador:
                    contador[a["tipo"]] += 1

        return contador

    # ---------------- STATUS MESSAGE ----------------

    def get_status_message(self, user_id):
        a = self.get(user_id)
        return a["status_message_id"] if a else None

    def set_status_message(self, user_id, message_id):
        a = self.get(user_id)
        if a:
            a["status_message_id"] = message_id

    # ---------------- VERSION (DEBOUNCE) ----------------

    def bump_version(self, user_id):
        self.version[user_id] = self.version.get(user_id, 0) + 1
        return self.version[user_id]

    def get_version(self, user_id):
        return self.version.get(user_id, 0)

    # ---------------- CLEAN ----------------

    def limpiar(self, user_id):
        self.usuarios.pop(user_id, None)
        self.version.pop(user_id, None)
        self.timers.pop(user_id, None)


service = AporteService()