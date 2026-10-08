from app.config import Settings


def test_mongodb_url_sin_credenciales():
    s = Settings(MONGODB_HOST="mongo", MONGODB_PORT=27017, MONGODB_USER=None, MONGODB_PASSWORD=None)
    assert s.MONGODB_URL == "mongodb://mongo:27017"


def test_mongodb_url_con_credenciales():
    s = Settings(MONGODB_HOST="mongo", MONGODB_USER="u", MONGODB_PASSWORD="p")
    assert s.MONGODB_URL == "mongodb://u:p@mongo:27017"
