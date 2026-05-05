const { param, body } = require('express-validator');

const videoIdParamValidator = [
  param('videoId').isMongoId().withMessage('videoId must be a valid Mongo ID'),
];

const addStrokeValidator = [
  ...videoIdParamValidator,
  body('type')
    .optional()
    .isIn(['freehand', 'line', 'arrow', 'rect', 'circle', 'text'])
    .withMessage('type must be one of: freehand, line, arrow, rect, circle, text'),
  body('color')
    .optional()
    .isString()
    .matches(/^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$/)
    .withMessage('color must be a valid hex color (e.g. #FF0000)'),
  body('strokeWidth')
    .optional()
    .isFloat({ min: 1, max: 50 })
    .withMessage('strokeWidth must be a number between 1 and 50'),
  body('points')
    .optional()
    .isArray()
    .withMessage('points must be an array'),
  body('points.*.x')
    .optional()
    .isFloat({ min: 0, max: 1 })
    .withMessage('each point.x must be a float between 0 and 1'),
  body('points.*.y')
    .optional()
    .isFloat({ min: 0, max: 1 })
    .withMessage('each point.y must be a float between 0 and 1'),
  body('label')
    .optional({ nullable: true })
    .isString()
    .isLength({ max: 500 })
    .withMessage('label must be a string up to 500 characters'),
];

const strokeIdParamValidator = [
  ...videoIdParamValidator,
  param('strokeId')
    .trim()
    .notEmpty()
    .withMessage('strokeId is required'),
];

module.exports = {
  videoIdParamValidator,
  addStrokeValidator,
  strokeIdParamValidator,
};
