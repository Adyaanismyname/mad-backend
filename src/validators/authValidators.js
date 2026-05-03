const { body } = require('express-validator');

const signupValidator = [
  body('name').trim().notEmpty().withMessage('name is required'),
  body('email').isEmail().withMessage('valid email is required'),
  body('password').isLength({ min: 6 }).withMessage('password must be at least 6 characters'),
  body('role').isIn(['trainer', 'client']).withMessage('role must be trainer or client'),
];

const loginValidator = [
  body('email').isEmail().withMessage('valid email is required'),
  body('password').notEmpty().withMessage('password is required'),
];

module.exports = {
  signupValidator,
  loginValidator,
};
