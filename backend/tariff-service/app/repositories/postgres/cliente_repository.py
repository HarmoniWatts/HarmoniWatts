# app/repositories/postgres/cliente_repository.py

from sqlalchemy.orm import Session
from typing import Optional
from app.models.postgres.cliente import Cliente


class ClienteRepository:
    """Repositorio para operaciones CRUD de clientes."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id_cliente: int) -> Optional[Cliente]:
        """Obtiene un cliente por su ID."""
        return (
            self.db.query(Cliente)
            .filter(Cliente.id_cliente == id_cliente)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[Cliente]:
        """Obtiene un cliente por email."""
        return (
            self.db.query(Cliente)
            .filter(Cliente.email == email)
            .first()
        )