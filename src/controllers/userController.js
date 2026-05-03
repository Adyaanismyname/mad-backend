const { validationResult } = require('express-validator');
const User = require('../models/User');

const listUsersByRole = async (req, res, next) => {
  try {
    const { role } = req.query;
    if (!['trainer', 'client'].includes(role)) {
      return res.status(400).json({ message: 'role query must be trainer or client' });
    }

    const users = await User.find({ role }).select('name email role profile');
    res.status(200).json({ users });
  } catch (error) {
    next(error);
  }
};

const updateProfile = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const allowedCommonFields = ['name'];
    const allowedClientProfileFields = ['age', 'weight', 'bmi', 'bio'];
    const allowedTrainerProfileFields = ['experienceYears', 'expertise', 'bio'];

    const updates = {};
    const profileUpdates = {};

    for (const key of allowedCommonFields) {
      if (req.body[key] !== undefined) updates[key] = req.body[key];
    }

    const roleBasedFields =
      req.user.role === 'client' ? allowedClientProfileFields : allowedTrainerProfileFields;

    for (const key of roleBasedFields) {
      if (req.body.profile && req.body.profile[key] !== undefined) {
        profileUpdates[`profile.${key}`] = req.body.profile[key];
      }
    }

    const updatedUser = await User.findByIdAndUpdate(
      req.user._id,
      { ...updates, ...profileUpdates },
      { new: true, runValidators: true }
    ).select('-password');

    res.status(200).json({
      message: 'Profile updated successfully',
      user: updatedUser,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  listUsersByRole,
  updateProfile,
};
