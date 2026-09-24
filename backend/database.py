from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./research_agent.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ResearchHistoryModel(Base):
    __tablename__ = "research_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    topic = Column(String)
    summary = Column(Text)
    sources = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)