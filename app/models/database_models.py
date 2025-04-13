from sqlalchemy import Column, String, Boolean, DateTime, func, Text
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
       
       # 프로필 관련 추가 필드
       profile_picture = Column(String, nullable=True)
       bio = Column(Text, nullable=True)
       phone_number = Column(String, nullable=True)
       location = Column(String, nullable=True)
       birth_date = Column(DateTime, nullable=True)
       gender = Column(String, nullable=True)
       
       # 로그인 관련 추가 필드
       last_login_at = Column(DateTime, nullable=True)
       last_login_ip = Column(String, nullable=True)