# __init__.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Importer tous les modèles ici pour que Alembic les détecte
from .media import Media, Subtitle

# Tu pourras rajouter d'autres fichiers ici plus tard
