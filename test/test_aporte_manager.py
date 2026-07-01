import unittest

from services.aporte_manager import AporteManager


class AporteManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = AporteManager()
        self.user_id = 10
        self.manager.iniciar_aporte(self.user_id)
        self.manager.omitir_comentario(self.user_id)

    def test_preserva_orden_por_message_id(self):
        self.manager.agregar_mensaje(self.user_id, 10, 30, "photo")
        self.manager.agregar_mensaje(self.user_id, 10, 28, "video")
        self.manager.agregar_mensaje(self.user_id, 10, 29, "document")

        lotes = self.manager.construir_lotes_copia(self.user_id)
        self.assertEqual(lotes, [{"source_chat_id": 10, "message_ids": [28, 29, 30]}])

    def test_no_corta_album_al_formar_lotes(self):
        for message_id in range(1, 99):
            self.manager.agregar_mensaje(self.user_id, 10, message_id, "photo")

        for message_id in (99, 100, 101):
            self.manager.agregar_mensaje(
                self.user_id,
                10,
                message_id,
                "photo",
                media_group_id="album-1",
            )

        lotes = self.manager.construir_lotes_copia(self.user_id, max_items=100)
        self.assertEqual(len(lotes), 2)
        self.assertEqual(lotes[0]["message_ids"], list(range(1, 99)))
        self.assertEqual(lotes[1]["message_ids"], [99, 100, 101])

    def test_ignora_mensaje_duplicado(self):
        self.assertTrue(
            self.manager.agregar_mensaje(self.user_id, 10, 1, "photo")
        )
        self.assertFalse(
            self.manager.agregar_mensaje(self.user_id, 10, 1, "photo")
        )
        self.assertEqual(self.manager.total(self.user_id), 1)

    def test_no_acepta_archivos_tras_fallo_de_entrega(self):
        self.manager.terminar_intento_envio(self.user_id, completado=False)
        self.assertFalse(
            self.manager.agregar_mensaje(self.user_id, 10, 1, "photo")
        )


if __name__ == "__main__":
    unittest.main()
