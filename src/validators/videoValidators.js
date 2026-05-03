const { body, param } = require('express-validator');

const uploadVideoValidator = [
  body('trainerId').isMongoId().withMessage('valid trainerId is required'),
  body('title').trim().notEmpty().withMessage('title is required'),
  body('description').optional().isString().withMessage('description must be a string'),
  body('workoutId').optional().isMongoId().withMessage('workoutId must be a valid id'),
  body('workoutAssignmentId')
    .optional()
    .isMongoId()
    .withMessage('workoutAssignmentId must be a valid id'),
];

const videoIdParamValidator = [
  param('videoId').isMongoId().withMessage('valid videoId is required'),
];

const addFeedbackValidator = [
  ...videoIdParamValidator,
  body('comment').trim().notEmpty().withMessage('comment is required'),
];

module.exports = {
  uploadVideoValidator,
  videoIdParamValidator,
  addFeedbackValidator,
};
