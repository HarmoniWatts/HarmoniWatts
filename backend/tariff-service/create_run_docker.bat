REM Construir y levantar (versión simple)
docker-compose -f docker-compose.yml up -d

REM Ver logs
docker-compose -f docker-compose.yml logs -f

REM Probar API
curl http://localhost:8001/health

REM Probar endpoint de consumo actual
curl http://localhost:8001/api/v1/consumption/current/45754113