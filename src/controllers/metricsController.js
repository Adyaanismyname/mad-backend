const { validationResult } = require('express-validator');
const ClientMetrics = require('../models/ClientMetrics');

/**
 * POST /api/metrics
 * Log a new metrics snapshot. All fields optional and nullable.
 * Only clients can call this.
 */
const logMetrics = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const { weight, height, bmi, age, fitnessGoal } = req.body;

    const entry = await ClientMetrics.create({
      user: req.user._id,
      weight: weight !== undefined ? weight : null,
      height: height !== undefined ? height : null,
      bmi: bmi !== undefined ? bmi : null,
      age: age !== undefined ? age : null,
      fitnessGoal: fitnessGoal !== undefined ? fitnessGoal : null,
    });

    res.status(201).json({ message: 'Metrics logged successfully', metrics: entry });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/metrics
 * Get paginated metrics history for the authenticated client.
 * Query params: limit (default 20), page (default 1)
 */
const getMetricsHistory = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const limit = parseInt(req.query.limit, 10) || 20;
    const page = parseInt(req.query.page, 10) || 1;
    const skip = (page - 1) * limit;

    const [entries, total] = await Promise.all([
      ClientMetrics.find({ user: req.user._id })
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit),
      ClientMetrics.countDocuments({ user: req.user._id }),
    ]);

    res.status(200).json({
      metrics: entries,
      pagination: {
        total,
        page,
        limit,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/metrics/latest
 * Get the most recent metrics entry for the authenticated client.
 */
const getLatestMetrics = async (req, res, next) => {
  try {
    const entry = await ClientMetrics.findOne({ user: req.user._id }).sort({ createdAt: -1 });

    if (!entry) {
      return res.status(404).json({ message: 'No metrics found for this user' });
    }

    res.status(200).json({ metrics: entry });
  } catch (error) {
    next(error);
  }
};

/**
 * PUT /api/metrics/:id
 * Update a specific metrics entry by ID (must belong to the authenticated client).
 */
const updateMetrics = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const entry = await ClientMetrics.findOne({ _id: req.params.id, user: req.user._id });

    if (!entry) {
      return res.status(404).json({ message: 'Metrics entry not found' });
    }

    const allowedFields = ['weight', 'height', 'bmi', 'age', 'fitnessGoal'];
    for (const field of allowedFields) {
      if (req.body[field] !== undefined) {
        entry[field] = req.body[field];
      }
    }

    await entry.save();

    res.status(200).json({ message: 'Metrics updated successfully', metrics: entry });
  } catch (error) {
    next(error);
  }
};

module.exports = { logMetrics, getMetricsHistory, getLatestMetrics, updateMetrics };
