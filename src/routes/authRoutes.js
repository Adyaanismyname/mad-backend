const express = require('express');
const { signup, login, me } = require('../controllers/authController');
const { signupValidator, loginValidator } = require('../validators/authValidators');
const auth = require('../middleware/auth');

const router = express.Router();

router.post('/signup', signupValidator, signup);
router.post('/login', loginValidator, login);
router.get('/me', auth, me);

module.exports = router;
