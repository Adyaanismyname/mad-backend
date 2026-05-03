const { body, param, query } = require('express-validator');

const uploadVideoValidator = [
  body('title')
    .optional()
    .isString()
    .isLength({ min: 2, max: 120 })
    .withMessage('title must be between 2 and 120 characters'),
  body('description')
    .optional()
    .isString()
    .isLength({ max: 1000 })
    .withMessage('description must be less than 1000 characters'),
  body('workoutId').optional().isMongoId().withMessage('workoutId must be a valid Mongo ID'),
  body('workoutAssignmentId')
    .optional()
    .isMongoId()
    .withMessage('workoutAssignmentId must be a valid Mongo ID'),
];

const videoIdParamValidator = [
  param('videoId').isMongoId().withMessage('videoId must be a valid Mongo ID'),
];

const trainerClientQueryValidator = [
  query('clientId').optional().isMongoId().withMessage('clientId must be a valid Mongo ID'),
];

const addCommentValidator = [
  ...videoIdParamValidator,
  body('comment')
    .trim()
    .notEmpty()
    .withMessage('comment is required')
    .isLength({ min: 2, max: 2000 })
    .withMessage('comment must be between 2 and 2000 characters'),
];

module.exports = {
  uploadVideoValidator,
  videoIdParamValidator,
  trainerClientQueryValidator,
  addCommentValidator,
};
