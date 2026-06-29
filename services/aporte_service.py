from datetime import datetime

class AporteService:
    def __init__(self):
        self.usuarios = {}

    def iniciar_aporte(self, user_id):
        self.usuarios[user_id] = {
            "estado": "WAITING_COMMENT",
            "comentario": "",
            "archivos": [],
            "inicio": datetime.now()
        }

    def existe_aporte(self, user_id):
        return user_id in self.usuarios

    def get(self, user_id):
        return self.usuarios.get(user_id)

    def set_comentario(self, user_id, texto):
        if user_id in self.usuarios:
            self.usuarios[user_id]["comentario"] = texto
            self.usuarios[user_id]["estado"] = "WAITING_MEDIA"

    def agregar_archivo(self, user_id, file_id, tipo):
        if user_id in self.usuarios:
            self.usuarios[user_id]["archivos"].append({
                "file_id": file_id,
                "tipo": tipo
            })

    def limpiar(self, user_id):
        if user_id in self.usuarios:
            del self.usuarios[user_id]