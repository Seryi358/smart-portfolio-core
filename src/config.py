"""config.py — Configuración Profesional y Gestión de Secretos.

Sesión 5.2: Separación entre código, configuración y secretos.

Dos enfoques complementarios:
1. ``Settings``    — dataclass simple que lee ``os.getenv`` (sin dependencias extra).
2. ``AppSettings`` — clase Pydantic-Settings que valida y lee ``.env`` automáticamente.

Flujo recomendado:
    Desarrollo local → .env → python-dotenv / pydantic-settings → objeto Settings
    Producción       → variables de CI/CD              → objeto Settings

Seguridad:
    - Nunca imprimir claves completas; usar ``masked_key``.
    - ``.env`` está bloqueado en ``.gitignore``; ``.env.example`` sí va en Git.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _PYDANTIC_SETTINGS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYDANTIC_SETTINGS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Opción 1: Settings con dataclass estándar (sin dependencias extras)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Settings:
    """Centraliza la configuración del sistema.

    Lee las variables de entorno al momento de llamar a ``Settings.load()``.
    Si falta alguna variable obligatoria o el valor es inválido, lanza
    una excepción clara antes de que el sistema arranque.

    Uso:
        >>> import os; os.environ["ALPHA_VANTAGE_KEY"] = "demo_key"
        >>> settings = Settings.load()
        >>> settings.environment
        'dev'
    """

    alpha_vantage_key: str
    environment: str = "dev"

    @classmethod
    def load(cls) -> "Settings":
        """Carga y valida la configuración desde variables de entorno.

        Raises:
            RuntimeError: Si ``ALPHA_VANTAGE_KEY`` no está definida.
            ValueError: Si ``ENVIRONMENT`` tiene un valor no reconocido.
        """
        api_key = os.getenv("ALPHA_VANTAGE_KEY", "")
        env = os.getenv("ENVIRONMENT", "dev")

        if not api_key:
            raise RuntimeError(
                "Falta ALPHA_VANTAGE_KEY. "
                "Defínela en las variables de entorno o en un archivo .env."
            )

        valid_envs = {"dev", "test", "prod"}
        if env not in valid_envs:
            raise ValueError(
                f"ENVIRONMENT '{env}' no es válido. Usa: {', '.join(sorted(valid_envs))}."
            )

        return cls(alpha_vantage_key=api_key, environment=env)

    @property
    def masked_key(self) -> str:
        """Representación segura de la clave API (solo muestra los primeros 4 caracteres)."""
        return self.alpha_vantage_key[:4] + "****"

    def info(self) -> str:
        """Descripción legible de la configuración activa."""
        return (
            f"Environment: {self.environment} | "
            f"Alpha Vantage key: {self.masked_key}"
        )


# ---------------------------------------------------------------------------
# Opción 2: AppSettings con Pydantic-Settings (recomendado para producción)
# ---------------------------------------------------------------------------

if _PYDANTIC_SETTINGS_AVAILABLE:

    class AppSettings(BaseSettings):
        """Configuración con validación automática mediante Pydantic v2.

        Lee automáticamente desde variables de entorno y desde ``.env``
        si el archivo existe en el directorio de trabajo.

        Ventaja sobre ``Settings``: tipado estricto, validación automática
        y soporte nativo para múltiples fuentes (env vars, archivos, secrets).

        Uso:
            >>> app_settings = AppSettings()
            >>> app_settings.environment
            'dev'
        """

        alpha_vantage_key: str = "demo_key"
        environment: str = "dev"

        model_config = SettingsConfigDict(
            env_file=".env",
            extra="ignore",  # ignora variables no declaradas en el modelo
        )

        @property
        def masked_key(self) -> str:
            """Representación segura de la clave API."""
            return self.alpha_vantage_key[:4] + "****"

        def info(self) -> str:
            """Descripción legible de la configuración activa."""
            return (
                f"Environment: {self.environment} | "
                f"Alpha Vantage key: {self.masked_key}"
            )

else:  # pragma: no cover
    AppSettings = None  # type: ignore[assignment,misc]
