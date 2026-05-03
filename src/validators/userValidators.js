const { body } = require('express-validator');

const updateProfileValidator = [
  body('name').optional().isString().withMessage('name must be a string'),
  body('profile.age').optional().isNumeric().withMessage('profile.age must be numeric'),
  body('profile.weight').optional().isNumeric().withMessage('profile.weight must be numeric'),
  body('profile.bmi').optional().isNumeric().withMessage('profile.bmi must be numeric'),
  body('profile.experienceYears')
    .optional()
    .isNumeric()
    .withMessage('profile.experienceYears must be numeric'),
  body('profile.expertise').optional().isString().withMessage('profile.expertise must be a string'),
  body('profile.bio').optional().isString().withMessage('profile.bio must be a string'),
];

module.exports = {
  updateProfileValidator,
};
