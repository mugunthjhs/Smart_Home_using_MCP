"""Database module for home automation."""
from app.db.database import db, Database
from app.db.seed_data import seed_database

__all__ = ["db", "Database", "seed_database"]