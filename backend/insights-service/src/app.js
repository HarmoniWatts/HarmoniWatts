const express = require('express');
const cors = require('cors');
const DashboardController = require('./controllers/dashboardController');
const ConsumptionService = require('./services/consumptionService');
const PredictionService = require('./services/predictionService');
const InsightsService = require('./services/insightsService');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', service: 'insights-service' });
});

// Initialize services
const consumptionService = new ConsumptionService();
const predictionService = new PredictionService();
const insightsService = new InsightsService(consumptionService, predictionService);
const dashboardController = new DashboardController(insightsService);

// Routes
app.get('/api/v1/dashboard/summary', dashboardController.getSummary);
app.get('/api/v1/dashboard/consumption-chart', dashboardController.getConsumptionChart);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message
  });
});

module.exports = app;