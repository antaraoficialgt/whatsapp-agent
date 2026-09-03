import pytest
import sys
import os
import tempfile
import shutil

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from auth import AuthManager

@pytest.fixture
def test_db():
    """Create a test database using a temporary file"""
    # Crear un archivo temporal para la BD
    temp_dir = tempfile.mkdtemp()
    db_path = f"sqlite:///{os.path.join(temp_dir, 'test.db')}"

    # Crear la BD
    db = Database(db_path)

    yield db

    # Limpiar después del test
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

@pytest.fixture
def auth_manager(test_db):
    """Create an auth manager with test database"""
    auth = AuthManager(database=test_db)
    return auth
