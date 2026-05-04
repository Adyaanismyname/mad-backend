const { param, body, query } = require('express-validator');

const clientIdParamValidator = [
  param('clientId').isMongoId().withMessage('clientId must be a valid Mongo ID'),
];

const planIdParamValidator = [
  param('planId').isMongoId().withMessage('planId must be a valid Mongo ID'),
];

const coachNotesValidator = [
  body('coachNotes')
    .optional({ nullable: true })
    .isString()
    .isLength({ max: 1000 })
    .withMessage('coachNotes must be a string with max 1000 characters'),
];

const planTypeQueryValidator = [
  query('type')
    .optional()
    .isIn(['diet', 'workout'])
    .withMessage('type must be diet or workout'),
];

module.exports = {
  clientIdParamValidator,
  planIdParamValidator,
  coachNotesValidator,
  planTypeQueryValidator,
};
