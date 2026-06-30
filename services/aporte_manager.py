from collections import defaultdict
from models.aporte import Aporte


class AporteManager:

    def __init__(self):
        # user_id → {aporte_id → Aporte}
        self.aportes = defaultdict(dict)

        # user_id → active aporte_id
        self.active = {}

    # -------------------------
    # CREAR APORTE
    # -------------------------
    def iniciar_aporte(self, user_id):
        aporte = Aporte()

        self.aportes[user_id][aporte.id] = aporte
        self.active[user_id] = aporte.id

        return aporte

    # -------------------------
    # OBTENER ACTIVO
    # -------------------------
    def get_active(self, user_id):
        aid = self.active.get(user_id)
        if not aid:
            return None
        return self.aportes[user_id].get(aid)

    # -------------------------
    # COMENTARIO
    # -------------------------
    def set_comentario(self, user_id, comentario):
        aporte = self.get_active(user_id)
        if not aporte:
            return

        aporte.comentario = comentario
        aporte.estado = "WAITING_MEDIA"

    # -------------------------
    # ARCHIVOS SUELTOS
    # -------------------------
    def agregar_archivo(self, user_id, file_id, tipo):
        aporte = self.get_active(user_id)
        if not aporte:
            return

        aporte.archivos.append({
            "tipo": tipo,
            "file_id": file_id
        })

    # -------------------------
    # ALBUMS
    # -------------------------
    def agregar_album(self, user_id, media_group_id, file_id, tipo):
        aporte = self.get_active(user_id)
        if not aporte:
            return

        if media_group_id not in aporte.albums:
            aporte.albums[media_group_id] = []

        aporte.albums[media_group_id].append({
            "tipo": tipo,
            "file_id": file_id
        })

    # -------------------------
    # CONTADOR
    # -------------------------
    def contar(self, user_id):
        aporte = self.get_active(user_id)

        base = {"photo": 0, "video": 0, "document": 0, "audio": 0}

        if not aporte:
            return base

        for f in aporte.archivos:
            if f["tipo"] in base:
                base[f["tipo"]] += 1

        for album in aporte.albums.values():
            for f in album:
                if f["tipo"] in base:
                    base[f["tipo"]] += 1

        return base

    # -------------------------
    # STATUS MESSAGE
    # -------------------------
    def set_status(self, user_id, msg_id):
        aporte = self.get_active(user_id)
        if aporte:
            aporte.status_message_id = msg_id

    def get_status(self, user_id):
        aporte = self.get_active(user_id)
        return aporte.status_message_id if aporte else None


# 🔥 INSTANCIA GLOBAL (IMPORTANTE)
manager = AporteManager()