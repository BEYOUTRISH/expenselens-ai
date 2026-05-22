import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
Base = declarative_base()


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.get_effective_database_url()
        logger.info(f"Using database: {db_url.split('://')[0]}")
        
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            
        _engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            if str(engine.url).startswith("sqlite"):
                conn.execute(text("SELECT 1"))
            else:
                conn.execute(text("SELECT 1"))
            conn.commit()
        logger.info("Database connection successful")
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
