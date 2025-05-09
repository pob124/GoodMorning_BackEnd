# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user_models import User  # noqa
from app.models.chatroom import Chatroom, Message, Coordinate  # noqa 