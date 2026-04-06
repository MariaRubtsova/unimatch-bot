from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime,
    Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deadlines = relationship("UserDeadline", back_populates="user", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="user", cascade="all, delete-orphan")


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    university_name = Column(Text, nullable=False)
    program_name = Column(Text, nullable=False)
    country = Column(Text, nullable=False)
    field = Column(Text, nullable=False)        # cs / business / engineering / science / medicine / other
    degree_type = Column(Text, nullable=False)  # master / bachelor / mba / phd
    min_gpa = Column(Float, nullable=False, default=0.0)
    avg_gpa = Column(Float, nullable=True)
    min_ielts = Column(Float, nullable=False, default=0.0)
    avg_ielts = Column(Float, nullable=True)
    tuition_year = Column(Integer, nullable=True)   # EUR per year
    deadline = Column(Date, nullable=True)
    url = Column(Text, nullable=True)
    requirements_text = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # pgvector, for RAG
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user_deadlines = relationship("UserDeadline", back_populates="program")
    checklist_items = relationship("ChecklistItem", back_populates="program")


class UserDeadline(Base):
    __tablename__ = "user_deadlines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    deadline = Column(Date, nullable=False)
    notified_30 = Column(Boolean, default=False, nullable=False)
    notified_7 = Column(Boolean, default=False, nullable=False)
    notified_1 = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="deadlines")
    program = relationship("Program", back_populates="user_deadlines")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    is_done = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="checklist_items")
    program = relationship("Program", back_populates="checklist_items")


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    degree_type = Column(Text, nullable=False)  # all / master / bachelor / mba / phd
    item_name = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
