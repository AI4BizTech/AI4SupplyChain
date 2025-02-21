# inventory_assistant/database/db.py
from sqlmodel import SQLModel, Session, create_engine
from typing import Optional
from contextlib import contextmanager
from inventory_assistant.models.laptop import Laptop, WarehouseStock, Transaction
from inventory_assistant.config import DB_PATH

class Database:
    _instance: Optional['Database'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'engine'):
            self.engine = create_engine(
                f"sqlite:///{DB_PATH}",
                echo=False  # Disable SQL echoing
            )
            
    def init_db(self) -> None:
        """Initialize the database, creating all tables."""
        SQLModel.metadata.create_all(self.engine)
    
    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations."""
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_record(self, model: SQLModel) -> SQLModel:
        """Create a new record."""
        with self.session() as session:
            session.add(model)
            session.commit()
            session.refresh(model)
            return model
    
    def get_by_id(self, model_class: type[SQLModel], id: str) -> Optional[SQLModel]:
        """Get record by ID."""
        with self.session() as session:
            return session.get(model_class, id)
    
    def update_record(self, model: SQLModel) -> SQLModel:
        """Update an existing record."""
        with self.session() as session:
            session.add(model)
            session.commit()
            session.refresh(model)
            return model
    
    def delete_record(self, model: SQLModel) -> None:
        """Delete a record."""
        with self.session() as session:
            session.delete(model)
            session.commit()

    def bulk_create(self, models: list[SQLModel]) -> list[SQLModel]:
        """Create multiple records at once."""
        with self.session() as session:
            session.add_all(models)
            session.commit()
            for model in models:
                session.refresh(model)
            return models
        
    def get_all(self, model_class: type[SQLModel]) -> list[SQLModel]:
        """Get all records for a given model."""
        with self.session() as session:
            return session.query(model_class).all()
        
    def execute_query(self, query):
        """Execute a custom query."""
        with self.session() as session:
            return session.execute(query)