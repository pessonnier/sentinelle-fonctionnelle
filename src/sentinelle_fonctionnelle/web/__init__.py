"""Interface web commune, composée ici pour le mode local."""

from .app import create_web_app
from .settings import ServerSettings, UnsupportedDeploymentMode

__all__ = [
    "ServerSettings",
    "UnsupportedDeploymentMode",
    "create_web_app",
]
