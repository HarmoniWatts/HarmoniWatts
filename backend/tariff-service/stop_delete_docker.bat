REM Detener
docker-compose -f docker-compose.yml down

REM Detener y eliminar volúmenes (reiniciar datos)
docker-compose -f docker-compose.yml down -v