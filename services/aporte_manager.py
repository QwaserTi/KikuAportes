from collections import defaultdict

from models.aporte import Aporte


class AporteManager:
    def __init__(self):
        self.aportes = defaultdict(dict)
        self.active = {}

    def iniciar_aporte(self, user_id):
        # Solo se permite un aporte activo por usuario.
        self.limpiar(user_id)

        aporte = Aporte()
        self.aportes[user_id][aporte.id] = aporte
        self.active[user_id] = aporte.id
        return aporte

    def get_active(self, user_id):
        aporte_id = self.active.get(user_id)
        if not aporte_id:
            return None
        return self.aportes[user_id].get(aporte_id)

    def set_comentario(self, user_id, comentario):
        aporte = self.get_active(user_id)
        if (
            not aporte
            or aporte.sending
            or aporte.estado != "WAITING_COMMENT"
        ):
            return False

        aporte.comentario = comentario.strip()
        aporte.estado = "WAITING_MEDIA"
        return True

    def omitir_comentario(self, user_id):
        return self.set_comentario(user_id, "")

    def agregar_mensaje(
        self,
        user_id,
        source_chat_id,
        message_id,
        tipo,
        media_group_id=None,
    ):
        aporte = self.get_active(user_id)
        if (
            not aporte
            or aporte.sending
            or aporte.estado != "WAITING_MEDIA"
        ):
            return False

        if message_id in aporte.message_ids:
            return False

        aporte.timeline.append(
            {
                "tipo": tipo,
                "source_chat_id": source_chat_id,
                "message_id": message_id,
                "media_group_id": media_group_id,
            }
        )
        aporte.message_ids.add(message_id)
        return True

    def contar(self, user_id):
        aporte = self.get_active(user_id)
        contador = {
            "photo": 0,
            "video": 0,
            "document": 0,
            "audio": 0,
        }

        if not aporte:
            return contador

        for item in aporte.timeline:
            if item["tipo"] in contador:
                contador[item["tipo"]] += 1

        return contador

    def total(self, user_id):
        return len(self.get_active(user_id).timeline) if self.get_active(user_id) else 0

    def construir_lotes_copia(self, user_id, max_items=100):
        """Construye lotes ordenados sin cortar un álbum entre dos lotes."""
        aporte = self.get_active(user_id)
        if not aporte:
            return []

        items = sorted(aporte.timeline, key=lambda item: item["message_id"])
        unidades = []

        for item in items:
            album_id = item.get("media_group_id")
            clave = (
                item["source_chat_id"],
                "album",
                album_id,
            ) if album_id else (
                item["source_chat_id"],
                "single",
                item["message_id"],
            )

            if unidades and unidades[-1]["clave"] == clave:
                unidades[-1]["message_ids"].append(item["message_id"])
            else:
                unidades.append(
                    {
                        "clave": clave,
                        "source_chat_id": item["source_chat_id"],
                        "message_ids": [item["message_id"]],
                    }
                )

        lotes = []
        actual = None

        for unidad in unidades:
            source_chat_id = unidad["source_chat_id"]
            ids = unidad["message_ids"]

            if len(ids) > max_items:
                raise ValueError("Un álbum supera el límite permitido por Telegram")

            puede_unirse = (
                actual
                and actual["source_chat_id"] == source_chat_id
                and len(actual["message_ids"]) + len(ids) <= max_items
            )

            if puede_unirse:
                actual["message_ids"].extend(ids)
            else:
                actual = {
                    "source_chat_id": source_chat_id,
                    "message_ids": list(ids),
                }
                lotes.append(actual)

        return lotes

    def iniciar_envio(self, user_id):
        aporte = self.get_active(user_id)
        if not aporte or aporte.sending:
            return None

        aporte.sending = True
        aporte.estado = "SENDING"
        return aporte

    def terminar_intento_envio(self, user_id, completado=False):
        aporte = self.get_active(user_id)
        if not aporte:
            return

        aporte.sending = False
        if not completado:
            # Tras un envío parcial no se aceptan archivos nuevos, porque los
            # índices de reanudación corresponden a la versión ya enviada.
            aporte.estado = "DELIVERY_FAILED"

    def get_delivery_progress(self, user_id, destination_id):
        aporte = self.get_active(user_id)
        if not aporte:
            return None

        return aporte.delivery_progress.setdefault(
            destination_id,
            {
                "header_sent": False,
                "comment_parts_sent": 0,
                "batches_sent": 0,
                "completed": False,
            },
        )

    def set_status(self, user_id, message_id):
        aporte = self.get_active(user_id)
        if aporte:
            aporte.status_message_id = message_id

    def get_status(self, user_id):
        aporte = self.get_active(user_id)
        return aporte.status_message_id if aporte else None

    def limpiar(self, user_id):
        aporte_id = self.active.pop(user_id, None)
        if aporte_id:
            self.aportes[user_id].pop(aporte_id, None)
        if not self.aportes[user_id]:
            self.aportes.pop(user_id, None)


manager = AporteManager()
