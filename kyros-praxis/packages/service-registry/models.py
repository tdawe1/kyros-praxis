"""Database models for the service registry application."""

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Service(Base):
    """ORM model for a registered service."""

    __tablename__ = "registered_services"

    name = Column(String, primary_key=True)
    host = Column(String)
    port = Column(String)
    capabilities = Column(JSON)
    last_heartbeat = Column(DateTime)
