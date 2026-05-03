const { body, param } = require('express-validator');

const exerciseValidator = body('exercises')
  .isArray({ min: 1 })
  .withMessage('exercises must be a non-empty array');

const createWorkoutValidator = [
  body('title').trim().notEmpty().withMessage('title is required'),
  body('description').optional().isString().withMessage('description must be a string'),
  exerciseValidator,
  body('exercises.*.name').trim().notEmpty().withMessage('exercise name is required'),
  body('exercises.*.sets').optional().isNumeric().withMessage('sets must be numeric'),
  body('exercises.*.reps').optional().isNumeric().withMessage('reps must be numeric'),
  body('exercises.*.durationSec').optional().isNumeric().withMessage('durationSec must be numeric'),
  body('exercises.*.restSec').optional().isNumeric().withMessage('restSec must be numeric'),
  body('exercises.*.notes').optional().isString().withMessage('notes must be a string'),
];

const assignWorkoutValidator = [
  param('id').isMongoId().withMessage('valid workout id is required'),
  body('clientId').isMongoId().withMessage('valid clientId is required'),
  body('notes').optional().isString().withMessage('notes must be a string'),
  body('startDate').optional().isISO8601().withMessage('startDate must be ISO date'),
  body('endDate').optional().isISO8601().withMessage('endDate must be ISO date'),
];

module.exports = {
  createWorkoutValidator,
  assignWorkoutValidator,
};
