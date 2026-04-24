import app from './src/app.js';
import config from './src/config/index.js';

const PORT = config.port;

const server = app.listen(PORT, () => {
  console.log('═══════════════════════════════════════════════════');
  console.log(`Insights Service running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Consumption Service: ${config.consumptionServiceUrl}`);
  console.log(`Prediction Service: ${config.predictionServiceUrl}`);
  console.log(`API endpoints:`);
  console.log(`   GET  /api/v1/dashboard/summary`);
  console.log(`   GET  /api/v1/dashboard/consumption-chart`);
  console.log(`   GET  /api/v1/dashboard/recommendations`);
  console.log(`   GET  /api/v1/dashboard/appliances/top`);
  console.log(`   POST /api/v1/recommendations/:id/apply | dismiss`);
  console.log(`   Health check: GET /health`);
  console.log('═══════════════════════════════════════════════════');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

export default server;
