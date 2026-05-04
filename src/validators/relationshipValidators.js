const { body, param } = require('express-validator');

const sendRequestValidator = [
  body('coachId').isMongoId().withMessage('coachId must be a valid Mongo ID'),
  body('message')
    .optional({ nullable: true })
    .isString()
    .isLength({ max: 500 })
    .withMessage('message must be a string with max 500 characters'),
];

const relationshipIdParamValidator = [
  param('id').isMongoId().withMessage('id must be a valid Mongo ID'),
];

module.exports = {
  sendRequestValidator,
  relationshipIdParamValidator,
};
