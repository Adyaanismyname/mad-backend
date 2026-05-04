const express = require('express');
const auth = require('../middleware/auth');
const allowRoles = require('../middleware/role');
const { logMetrics, getMetricsHistory, getLatestMetrics, updateMetrics } = require('../controllers/metricsController');
const { logMetricsValidator, getMetricsHistoryValidator } = require('../validators/metricsValidators');

const router = express.Router();

// All metrics routes require authentication and client role
router.use(auth, allowRoles('client'));

router.post('/', logMetricsValidator, logMetrics);
router.get('/', getMetricsHistoryValidator, getMetricsHistory);
router.get('/latest', getLatestMetrics);
router.put('/:id', logMetricsValidator, updateMetrics);

module.exports = router;
