from datetime import datetime


class AporteService:
    def __init__(self):
        self.usuarios = {}

    def iniciar_aporte(self, user_id):
        self.usuarios[user_id] = {
            "estado": "WAITING_COMMENT",
            "comentario": "",
            "archivos": [],
            "inicio": datetime.now(),
            "status_message_id": None
        }

    def existe_aporte(self, user_id):
        return user_id in self.usuarios

    def get(self, user_id):
        return self.usuarios.get(user_id)

    def set_comentario(self, user_id, comentario):
        aporte = self.get(user_id)
        if not aporte:
            return

        aporte["comentario"] = comentario
        aporte["estado"] = "WAITING_MEDIA"

    def agregar_archivo(self, user_id, file_id, tipo):
        aporte = self.get(user_id)
        if not aporte:
            return

        aporte["archivos"].append({
            "file_id": file_id,
            "tipo": tipo
        })

    def contar_archivos(self, user_id):
        aporte = self.get(user_id)

        if not aporte:
            return {
                "photo": 0,
                "video": 0,
                "document": 0,
                "audio": 0
            }

        contador = {
            "photo": 0,
            "video": 0,
            "document": 0,
            "audio": 0
        }

        for archivo in aporte["archivos"]:
            tipo = archivo["tipo"]

            if tipo in contador:
                contador[tipo] += 1

        return contador

    # ---------------- MENSAJE DE ESTADO ----------------

    def get_status_message(self, user_id):
        aporte = self.get(user_id)
        if not aporte:
            return None

        return aporte["status_message_id"]

    def set_status_message(self, user_id, message_id):
        aporte = self.get(user_id)
        if not aporte:
            return

        aporte["status_message_id"] = message_id

    def limpiar(self, user_id):
        self.usuarios.pop(user_id, None)


service = AporteService()