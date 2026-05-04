const { validationResult } = require('express-validator');
const User = require('../models/User');
const CoachClientRelationship = require('../models/CoachClientRelationship');

const listUsersByRole = async (req, res, next) => {
  try {
    const { role } = req.query;
    if (!['trainer', 'client'].includes(role)) {
      return res.status(400).json({ message: 'role query must be trainer or client' });
    }

    const users = await User.find({ role }).select('name email role profile');

    // When a client browses trainers, attach their relationship status for each coach
    // so the frontend can correctly enable/disable the "Send Request" button.
    if (role === 'trainer' && req.user.role === 'client') {
      const trainerIds = users.map((u) => u._id);
      const relationships = await CoachClientRelationship.find({
        client: req.user._id,
        coach: { $in: trainerIds },
      }).select('coach status');

      const statusByCoach = {};
      for (const rel of relationships) {
        // Most-recent relevant status wins; $in returns all, so just map
        statusByCoach[rel.coach.toString()] = rel.status;
      }

      const usersWithStatus = users.map((u) => ({
        ...u.toObject(),
        relationshipStatus: statusByCoach[u._id.toString()] || 'none',
      }));

      return res.status(200).json({ users: usersWithStatus });
    }

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
