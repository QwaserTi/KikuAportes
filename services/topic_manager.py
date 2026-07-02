import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)


MONTH_NAMES = (
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)


class MonthlyTopicManager:
    """Crea y recuerda un tema de Telegram por cada mes y grupo."""

    def __init__(
        self,
        registry_path=None,
        timezone_name="America/Mexico_City",
    ):
        project_dir = Path(__file__).resolve().parent.parent

        self.registry_path = Path(
            registry_path
            or project_dir / "data" / "monthly_topics.json"
        )
        self.timezone = ZoneInfo(timezone_name)
        self._lock = asyncio.Lock()

    def month_info(self, moment=None):
        """Devuelve una clave estable y el nombre visible del tema."""
        if moment is None:
            local_time = datetime.now(self.timezone)
        elif moment.tzinfo is None:
            local_time = moment.replace(tzinfo=self.timezone)
        else:
            local_time = moment.astimezone(self.timezone)

        month_key = f"{local_time.year:04d}-{local_time.month:02d}"
        topic_name = f"{MONTH_NAMES[local_time.month]} {local_time.year}"

        return month_key, topic_name

    def _load_registry(self):
        if not self.registry_path.exists():
            return {"groups": {}}

        try:
            with self.registry_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "El archivo data/monthly_topics.json está dañado. "
                "No se creará otro tema para evitar duplicados."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "El archivo data/monthly_topics.json no tiene un formato válido."
            )

        groups = data.setdefault("groups", {})
        if not isinstance(groups, dict):
            raise RuntimeError(
                "La sección 'groups' de monthly_topics.json no es válida."
            )

        return data

    def _save_registry(self, data):
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = self.registry_path.with_suffix(".json.tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")

        temporary_path.replace(self.registry_path)

    async def _validate_group(self, bot, chat_id):
        chat = await bot.get_chat(chat_id)

        if not getattr(chat, "is_forum", False):
            raise RuntimeError(
                "El GROUP_ID configurado no tiene los temas activados."
            )

        bot_user = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_user.id)
        raw_status = getattr(member, "status", "")
        status = str(getattr(raw_status, "value", raw_status))
        is_owner = status in {"creator", "owner"}
        can_manage_topics = bool(
            getattr(member, "can_manage_topics", False)
        )

        if not is_owner and not can_manage_topics:
            raise RuntimeError(
                "El bot necesita ser administrador del grupo con el permiso "
                "'Administrar temas'."
            )

    async def get_or_create(self, bot, chat_id, moment=None):
        """
        Devuelve (message_thread_id, topic_name).

        Un bloqueo impide que dos aportes simultáneos creen dos temas iguales.
        """
        month_key, topic_name = self.month_info(moment)
        group_key = str(chat_id)

        async with self._lock:
            registry = self._load_registry()
            groups = registry["groups"]
            group_topics = groups.setdefault(group_key, {})

            saved = group_topics.get(month_key)
            if saved is not None:
                if isinstance(saved, dict):
                    thread_id = saved.get("message_thread_id")
                else:
                    # Compatibilidad con un formato simple antiguo.
                    thread_id = saved

                if thread_id is None:
                    raise RuntimeError(
                        f"El registro del tema {topic_name} no contiene un ID."
                    )

                return int(thread_id), topic_name

            # Comprueba que el archivo puede escribirse antes de crear el tema.
            # Así se reduce el riesgo de crear temas duplicados si faltan permisos
            # de escritura en el VPS.
            self._save_registry(registry)

            await self._validate_group(bot, chat_id)

            topic = await bot.create_forum_topic(
                chat_id=chat_id,
                name=topic_name,
            )

            thread_id = int(topic.message_thread_id)
            group_topics[month_key] = {
                "message_thread_id": thread_id,
                "name": topic_name,
            }
            self._save_registry(registry)

            logger.info(
                "Tema mensual creado: grupo=%s tema=%s thread_id=%s",
                chat_id,
                topic_name,
                thread_id,
            )

            return thread_id, topic_name


monthly_topics = MonthlyTopicManager()
