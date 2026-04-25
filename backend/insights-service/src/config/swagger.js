import swaggerJsdoc from 'swagger-jsdoc';

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'HarmoniWatts Insights Service API',
      version: '1.0.0',
      description: 'Servicio de agregación para el dashboard - Consumo real + predicción + franjas horarias',
      contact: {
        name: 'API Support',
        email: 'support@insights-service.com'
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT'
      }
    },
    servers: [
      {
        url: 'http://localhost:7001/api/v1',
        description: 'Servidor de desarrollo'
      },
      {
        url: 'https://api.insights-service.com/api/v1',
        description: 'Servidor de producción'
      }
    ],
    components: {
      schemas: {
        DashboardSummaryResponse: {
          type: 'object',
          properties: {
            date: { type: 'string', format: 'date', example: '2026-03-30' },
            timezone: { type: 'string', example: 'America/Bogota' },
            consumptionTodayKwh: { type: 'number', example: 12.4 },
            consumptionVsYesterdayPercent: { type: 'number', example: -8.0 },
            estimatedCostTodayCop: { type: 'integer', example: 4230 },
            currentTariffSlot: {
              type: 'object',
              properties: {
                type: { type: 'string', enum: ['VALLE', 'MEDIA', 'PUNTA'] },
                label: { type: 'string' },
                energyPriceCopPerKwh: { type: 'integer' }
              }
            },
            savingsAccumulatedCop: { type: 'integer', example: 18900 },
            savingsPeriod: {
              type: 'object',
              properties: {
                label: { type: 'string' },
                from: { type: 'string', format: 'date' },
                to: { type: 'string', format: 'date' }
              }
            },
            nextHighTariffWindow: {
              type: 'object',
              properties: {
                type: { type: 'string' },
                label: { type: 'string' },
                startsAt: { type: 'string', format: 'date-time' },
                endsAt: { type: 'string', format: 'date-time' },
                displayHint: { type: 'string' }
              }
            }
          }
        },
        ConsumptionChartResponse: {
          type: 'object',
          properties: {
            date: { type: 'string', format: 'date' },
            timezone: { type: 'string' },
            granularity: { type: 'string', enum: ['HOUR'] },
            maxKwhScale: { type: 'number' },
            hours: { type: 'array', items: { type: 'integer' } },
            actualKwh: { type: 'array', items: { type: 'number' } },
            predictedKwh: { type: 'array', items: { type: 'number' }, nullable: true },
            currentHourLocal: { type: 'integer' },
            tariffBands: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  type: { type: 'string' },
                  startHour: { type: 'integer' },
                  endHour: { type: 'integer' },
                  energyPriceCopPerKwh: { type: 'integer' }
                }
              }
            },
            predictionUnavailable: { type: 'boolean' }
          }
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            error: { type: 'string' },
            message: { type: 'string' },
            code: { type: 'string' }
          }
        }
      }
    }
  },
  apis: ['./src/routes/*.js'], // Path a los archivos con anotaciones JSDoc
};

const swaggerSpec = swaggerJsdoc(options);

export default swaggerSpec;