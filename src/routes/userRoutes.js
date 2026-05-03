const express = require('express');
const auth = require('../middleware/auth');
const { listUsersByRole, updateProfile } = require('../controllers/userController');
const { updateProfileValidator } = require('../validators/userValidators');

const router = express.Router();

router.get('/', auth, listUsersByRole);
router.put('/profile', auth, updateProfileValidator, updateProfile);

module.exports = router;
