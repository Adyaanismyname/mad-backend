const { validationResult } = require('express-validator');
const CoachClientRelationship = require('../models/CoachClientRelationship');
const User = require('../models/User');

const ensureValidation = (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    return false;
  }
  return true;
};

/**
 * POST /api/relationships/request
 * Client sends a coaching request to a trainer.
 * Guards:
 *   - coachId must be a trainer
 *   - no pending or active relationship already exists for this pair
 */
const sendRequest = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const { coachId, message } = req.body;

    // Verify target is actually a trainer
    const coach = await User.findById(coachId).select('role name');
    if (!coach || coach.role !== 'trainer') {
      return res.status(404).json({ message: 'Coach not found.' });
    }

    // Block duplicate pending/active requests
    const existing = await CoachClientRelationship.findOne({
      coach: coachId,
      client: req.user._id,
      status: { $in: ['pending', 'active'] },
    });

    if (existing) {
      const msg =
        existing.status === 'active'
          ? 'You already have an active relationship with this coach.'
          : 'A pending request to this coach already exists.';
      return res.status(409).json({ message: msg, relationship: existing });
    }

    const relationship = await CoachClientRelationship.create({
      coach: coachId,
      client: req.user._id,
      message: message || null,
    });

    res.status(201).json({
      message: 'Request sent successfully.',
      relationship,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/relationships/my-requests
 * Client: list all requests they have sent (any status).
 */
const getMyRequests = async (req, res, next) => {
  try {
    const relationships = await CoachClientRelationship.find({ client: req.user._id })
      .populate('coach', 'name email profile')
      .sort({ createdAt: -1 });

    res.status(200).json({ relationships });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/relationships/incoming
 * Trainer: list all pending requests they have received.
 */
const getIncomingRequests = async (req, res, next) => {
  try {
    const relationships = await CoachClientRelationship.find({
      coach: req.user._id,
      status: 'pending',
    })
      .populate('client', 'name email profile')
      .sort({ createdAt: -1 });

    res.status(200).json({ relationships });
  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/relationships/:id/accept
 * Trainer: accept a pending request.
 */
const acceptRequest = async (req, res, next) => {
  try {
    const relationship = await CoachClientRelationship.findOne({
      _id: req.params.id,
      coach: req.user._id,
      status: 'pending',
    });

    if (!relationship) {
      return res.status(404).json({ message: 'Pending request not found.' });
    }

    relationship.status = 'active';
    relationship.resolvedAt = new Date();
    relationship.resolvedBy = req.user._id;
    await relationship.save();

    res.status(200).json({ message: 'Request accepted.', relationship });
  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/relationships/:id/reject
 * Trainer: reject a pending request.
 */
const rejectRequest = async (req, res, next) => {
  try {
    const relationship = await CoachClientRelationship.findOne({
      _id: req.params.id,
      coach: req.user._id,
      status: 'pending',
    });

    if (!relationship) {
      return res.status(404).json({ message: 'Pending request not found.' });
    }

    relationship.status = 'rejected';
    relationship.resolvedAt = new Date();
    relationship.resolvedBy = req.user._id;
    await relationship.save();

    res.status(200).json({ message: 'Request rejected.', relationship });
  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/relationships/:id/terminate
 * Coach or client: end an active relationship.
 */
const terminateRelationship = async (req, res, next) => {
  try {
    const relationship = await CoachClientRelationship.findOne({
      _id: req.params.id,
      status: 'active',
      $or: [{ coach: req.user._id }, { client: req.user._id }],
    });

    if (!relationship) {
      return res.status(404).json({ message: 'Active relationship not found.' });
    }

    relationship.status = 'terminated';
    relationship.resolvedAt = new Date();
    relationship.resolvedBy = req.user._id;
    await relationship.save();

    res.status(200).json({ message: 'Relationship terminated.', relationship });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/relationships/my-coach
 * Client: get their currently active coach (if any).
 */
const getMyCoach = async (req, res, next) => {
  try {
    const relationship = await CoachClientRelationship.findOne({
      client: req.user._id,
      status: 'active',
    }).populate('coach', 'name email profile');

    res.status(200).json({ relationship: relationship || null });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/relationships/my-clients
 * Trainer: list all active clients.
 */
const getMyClients = async (req, res, next) => {
  try {
    const relationships = await CoachClientRelationship.find({
      coach: req.user._id,
      status: 'active',
    })
      .populate('client', 'name email profile')
      .sort({ resolvedAt: -1 });

    res.status(200).json({ relationships });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  sendRequest,
  getMyRequests,
  getIncomingRequests,
  acceptRequest,
  rejectRequest,
  terminateRelationship,
  getMyCoach,
  getMyClients,
};
