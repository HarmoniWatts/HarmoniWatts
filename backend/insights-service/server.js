const app = require('./src/app');
const config = require('./src/config');

const PORT = config.port;

app.listen(PORT, () => {
  console.log(`Insights Service running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Consumption Service URL: ${config.consumptionServiceUrl}`);
  console.log(`Prediction Service URL: ${config.predictionServiceUrl}`);
});