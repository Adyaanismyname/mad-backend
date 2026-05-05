const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const connectDB = require('./config/db');

const authRoutes = require('./routes/authRoutes');
const userRoutes = require('./routes/userRoutes');
const workoutRoutes = require('./routes/workoutRoutes');
const videoRoutes = require('./routes/videoRoutes');
const relationshipRoutes = require('./routes/relationshipRoutes');
const aiPlanRoutes = require('./routes/aiPlanRoutes');
const metricsRoutes = require('./routes/metricsRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// Ensure DB is connected before every request (required for Vercel serverless)
app.use(async (req, res, next) => {
  try {
    await connectDB();
    next();
  } catch (err) {
    next(err);
  }
});

app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }));
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));
app.use('/uploads', (req, res, next) => {
  res.setHeader('Cross-Origin-Resource-Policy', 'cross-origin');
  next();
}, express.static(path.join(__dirname, '..', 'uploads')));

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'Fit & Fuel API' });
});

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/workouts', workoutRoutes);
app.use('/api/videos', videoRoutes);
app.use('/api/relationships', relationshipRoutes);
app.use('/api/ai-plans', aiPlanRoutes);
app.use('/api/metrics', metricsRoutes);

app.use((req, res) => {
  res.status(404).json({ message: 'Route not found' });
});

app.use(errorHandler);

module.exports = app;
