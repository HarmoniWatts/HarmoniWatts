REM Construir imagen
docker-compose -f docker-compose.yml up -d

REM Ver logs
docker-compose -f docker-compose.yml logs -f



REM Probar health check (usando el puerto 7001)
curl http://localhost:7001/health