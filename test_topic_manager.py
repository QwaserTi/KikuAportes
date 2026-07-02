import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from services.topic_manager import MonthlyTopicManager


class FakeBot:
    def __init__(self):
        self.created_topics = []

    async def get_chat(self, chat_id):
        return SimpleNamespace(is_forum=True)

    async def get_me(self):
        return SimpleNamespace(id=999)

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(
            status="administrator",
            can_manage_topics=True,
        )

    async def create_forum_topic(self, chat_id, name):
        self.created_topics.append((chat_id, name))
        return SimpleNamespace(message_thread_id=700 + len(self.created_topics))


class MonthlyTopicManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_crea_un_solo_tema_y_lo_reutiliza(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "topics.json"
            manager = MonthlyTopicManager(registry_path=registry_path)
            bot = FakeBot()
            moment = datetime(2026, 7, 15, 18, 0, tzinfo=timezone.utc)

            first = await manager.get_or_create(bot, -100123, moment)
            second = await manager.get_or_create(bot, -100123, moment)

            self.assertEqual(first, (701, "Julio 2026"))
            self.assertEqual(second, first)
            self.assertEqual(bot.created_topics, [(-100123, "Julio 2026")])

            data = json.loads(registry_path.read_text(encoding="utf-8"))
            saved = data["groups"]["-100123"]["2026-07"]
            self.assertEqual(saved["message_thread_id"], 701)

    async def test_separa_meses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = MonthlyTopicManager(
                registry_path=Path(temp_dir) / "topics.json"
            )
            bot = FakeBot()

            july = await manager.get_or_create(
                bot,
                -100123,
                datetime(2026, 7, 31, 20, 0, tzinfo=timezone.utc),
            )
            august = await manager.get_or_create(
                bot,
                -100123,
                datetime(2026, 8, 15, 20, 0, tzinfo=timezone.utc),
            )

            self.assertEqual(july[1], "Julio 2026")
            self.assertEqual(august[1], "Agosto 2026")
            self.assertNotEqual(july[0], august[0])


if __name__ == "__main__":
    unittest.main()
