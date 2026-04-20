import e from 'express';

import dotenv from 'dotenv';
dotenv.config();


export const port = process.env.PORT || 3001;
export const consumptionServiceUrl = process.env.CONSUMPTION_SERVICE_URL || 'http://localhost:8001';
export const predictionServiceUrl = process.env.PREDICTION_SERVICE_URL || 'http://localhost:3003';
export const defaultTimezone = process.env.DEFAULT_TIMEZONE || 'America/Bogota';
export const tariffBands = [
    { type: 'VALLE', label: 'Valle', startHour: 0, endHour: 6, price: 280 },
    { type: 'MEDIA', label: 'Media', startHour: 6, endHour: 10, price: 520 },
    { type: 'PUNTA', label: 'Punta', startHour: 10, endHour: 13, price: 980 },
    { type: 'MEDIA', label: 'Media', startHour: 13, endHour: 18, price: 520 },
    { type: 'PUNTA', label: 'Punta', startHour: 18, endHour: 21, price: 980 },
    { type: 'VALLE', label: 'Valle', startHour: 21, endHour: 24, price: 280 }
];

export default {
    port,
    consumptionServiceUrl,
    predictionServiceUrl,
    defaultTimezone,
    tariffBands
};