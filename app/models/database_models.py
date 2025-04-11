from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
       __tablename__ = "users"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       firebase_uid = Column(String, unique=True, index=True)
       email = Column(String, unique=True, index=True)
       username = Column(String, unique=True, index=True, nullable=True)
       name = Column(String, nullable=True)
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime, default=func.now())
       updated_at = Column(DateTime, default=func.now(), onupdate=func.now())