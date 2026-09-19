workspace "HarmoniWatts" "Sistema de Predicción y Análisis de Consumo Energético" {

    model {
        # Actores Externos
        user = person "Usuario Residencial" "Propietario/arrendatario que monitorea su consumo"
        utility = person "Empresa Energética" "Proveedor de energía eléctrica"
        iot_device = person "Dispositivo IoT" "Medidor inteligente/Sensor de consumo"
        tariff_provider = softwareSystem "Comercializador de Tarifas" "Sistema externo de gestión de tarifas energéticas dinámicas"

        # Sistema Principal
        harmoniwatts = softwareSystem "HarmoniWatts" "Sistema inteligente de análisis y predicción de consumo energético" {

            # Frontend
            web = container "Frontend Web" "Angular SPA" "TypeScript/Angular" "Web Browser"

            # Backend - Microservicios
            consumption_api = container "Consumption Service" "Ingesta y almacenamiento de datos de consumo" "Python/FastAPI" {
                api_routes = component "API Routes" "Endpoints REST" "FastAPI Router"
                data_service = component "Data Service" "Lógica de ingesta" "FastAPI Service"
                mongo_driver = component "MongoDB Driver" "Acceso a MongoDB" "Motor"
                celery_tasks = component "Celery Tasks" "Procesamiento asincrónico" "Celery"
            }

            insights_api = container "Insights Service" "Agregación y análisis de datos" "Node.js/Express" {
                dashboard_routes = component "Dashboard Routes" "Endpoints de dashboards" "Express Router"
                insights_service = component "Insights Service" "Lógica de análisis" "Express Service"
                consumption_client = component "Consumption Client" "Cliente HTTP" "Axios"
                prediction_client = component "Prediction Client" "Cliente HTTP" "Axios"
            }

            houses_api = container "Vivienda API" "Gestión de viviendas y usuarios" "Java/Spring Boot" {
                houses_controller = component "Houses Controller" "Endpoints de viviendas" "Spring Controller"
                houses_service = component "Houses Service" "Lógica de negocio" "Spring Service"
                houses_repo = component "Houses Repository" "Acceso a datos" "Spring JPA"
            }

            appliances_api = container "Electrodomésticos API" "Gestión y predicción de dispositivos" "Java/Spring Boot" {
                appliances_controller = component "Appliances Controller" "Endpoints de dispositivos" "Spring Controller"
                appliances_service = component "Appliances Service" "Lógica de predicción" "Spring Service"
                appliances_repo = component "Appliances Repository" "Acceso a datos" "Spring JPA"
            }

            prediction_api = container "Prediction Service" "IA para predicción de consumo mensual" "Python/FastAPI" {
                ml_model = component "ML Model" "Modelo de Machine Learning" "TensorFlow/scikit-learn"
                prediction_routes = component "Prediction Routes" "Endpoints de predicción" "FastAPI Router"
                data_aggregator = component "Data Aggregator" "Agregación de datos históricos" "Python Service"
            }

            tariff_api = container "Tariff Service" "Persistencia y gestión de tarifas energéticas" "Java/Spring Boot" {
                tariff_controller = component "Tariff Controller" "Endpoints de tarifas" "Spring Controller"
                tariff_service = component "Tariff Service" "Lógica de tarifas" "Spring Service"
                tariff_repo = component "Tariff Repository" "Acceso a datos de tarifas" "Spring JPA"
            }

            # Bases de Datos
            mongodb = container "MongoDB" "Base de datos NoSQL" "MongoDB" "Database" {
                consumption_collection = component "Consumption Collection" "Documentos de consumo" "MongoDB Collection"
                daily_summaries = component "Daily Summaries" "Resúmenes diarios" "MongoDB Collection"
            }

            postgresql = container "PostgreSQL" "Base de datos relacional" "PostgreSQL" "Database" {
                households_table = component "Households Table" "Datos de viviendas" "PostgreSQL Table"
                appliances_table = component "Appliances Table" "Datos de electrodomésticos" "PostgreSQL Table"
                users_table = component "Users Table" "Datos de usuarios" "PostgreSQL Table"
            }

            # Cache y Task Queue
            redis = container "Redis" "Cache y task queue" "Redis" "Cache"

            # Autenticación
            keycloak = container "Keycloak" "SSO y gestión de identidades" "Keycloak" "Identity Provider"
        }

        # Relaciones de Usuario
        user -> web "Usa"
        user -> utility "Paga servicios"
        iot_device -> utility "Envía lecturas de consumo (contador inteligente)"
        utility -> consumption_api "Proporciona datos históricos de consumo"
        tariff_provider -> tariff_api "Envía tarifas energéticas dinámicas"

        # Relaciones Frontend-Backend
        web -> consumption_api "GET /api/v1/consumption"
        web -> insights_api "GET /api/v1/dashboard"
        web -> houses_api "API de viviendas"
        web -> appliances_api "API de dispositivos"
        web -> keycloak "Autentica usuario"

        # Relaciones entre Microservicios
        insights_api -> consumption_api "Consulta datos históricos"
        insights_api -> prediction_api "Solicita predicciones"
        appliances_api -> prediction_api "Predicción por dispositivo"
        appliances_api -> consumption_api "Datos históricos"
        consumption_api -> keycloak "Valida JWT tokens"
        houses_api -> keycloak "Valida JWT tokens"

        # Relaciones con Bases de Datos
        consumption_api -> mongodb "Lee/escribe datos de consumo"
        consumption_api -> redis "Task queue (Celery)"
        houses_api -> postgresql "Lee/escribe datos de viviendas"
        appliances_api -> postgresql "Lee/escribe datos de dispositivos"
        tariff_api -> postgresql "Lee/escribe tarifas por hora"

        # Relaciones internas de Consumption Service
        api_routes -> data_service "Procesa requests"
        data_service -> mongo_driver "Accede a datos"
        data_service -> celery_tasks "Enqueue tasks"
        celery_tasks -> redis "Lectura de tasks"

        # Relaciones internas de Insights Service
        dashboard_routes -> insights_service "Procesa requests"
        insights_service -> consumption_client "Consulta consumo"
        insights_service -> prediction_client "Solicita predicciones"

        # Relaciones internas de Tariff Service
        tariff_controller -> tariff_service "Procesa requests"
        tariff_service -> tariff_repo "Accede a datos"

        # Relaciones internas de Bases de Datos
        mongo_driver -> consumption_collection "Lee/escribe"
        mongo_driver -> daily_summaries "Lee/escribe"
        houses_repo -> households_table "Lee/escribe"
        appliances_repo -> appliances_table "Lee/escribe"
        tariff_repo -> postgresql "Lee/escribe tarifas"
    }

    views {
        systemContext harmoniwatts {
            include *
            autoLayout
        }

        container harmoniwatts {
            include *
            include user utility iot_device tariff_provider
            autoLayout
        }

        component consumption_api {
            include *
            autoLayout
        }

        component insights_api {
            include *
            autoLayout
        }

        component houses_api {
            include *
            autoLayout
        }

        component appliances_api {
            include *
            autoLayout
        }

        component prediction_api {
            include *
            autoLayout
        }

        component tariff_api {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85BBF0
                color #000000
            }
            element "Person" {
                background #08427b
                color #ffffff
                fontSize 22
                shape Box
            }
            element "Database" {
                shape Cylinder
            }
            element "Cache" {
                shape Cylinder
                background #ff6b35
            }
            element "Identity Provider" {
                background #f97316
            }
        }
    }

    configuration {
        scope softwareSystem
    }
}
