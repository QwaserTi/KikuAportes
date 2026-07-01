"""Compatibilidad con imports antiguos.

La implementación real de los callbacks está unificada en handlers.buttons.
"""

from handlers.buttons import buttons

__all__ = ["buttons"]
