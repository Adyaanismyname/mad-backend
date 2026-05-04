const { body, query } = require('express-validator');

const logMetricsValidator = [
  body('weight')
    .optional({ nullable: true })
    .custom((val) => val === null || (typeof val === 'number' && val > 0))
    .withMessage('weight must be a positive number or null'),
  body('height')
    .optional({ nullable: true })
    .custom((val) => val === null || (typeof val === 'number' && val > 0))
    .withMessage('height must be a positive number or null'),
  body('bmi')
    .optional({ nullable: true })
    .custom((val) => val === null || (typeof val === 'number' && val > 0))
    .withMessage('bmi must be a positive number or null'),
  body('age')
    .optional({ nullable: true })
    .custom((val) => val === null || (Number.isInteger(val) && val > 0 && val < 150))
    .withMessage('age must be a positive integer or null'),
  body('fitnessGoal')
    .optional({ nullable: true })
    .custom((val) => val === null || typeof val === 'string')
    .withMessage('fitnessGoal must be a string or null'),
];

const getMetricsHistoryValidator = [
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('limit must be between 1 and 100'),
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('page must be a positive integer'),
];

module.exports = { logMetricsValidator, getMetricsHistoryValidator };
