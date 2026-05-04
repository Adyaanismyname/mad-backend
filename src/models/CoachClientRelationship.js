const mongoose = require('mongoose');

/**
 * Represents the relationship between a coach (trainer) and a client.
 *
 * Lifecycle:
 *   client sends request  → status: pending
 *   coach accepts         → status: active
 *   coach rejects         → status: rejected
 *   either party ends it  → status: terminated
 *
 * Uniqueness rules (enforced by compound index):
 *   - At most ONE non-rejected/terminated request per coach+client pair.
 *     Handled at service level; index prevents duplicates at DB level.
 */
const coachClientRelationshipSchema = new mongoose.Schema(
  {
    coach: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    client: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    status: {
      type: String,
      enum: ['pending', 'active', 'rejected', 'terminated'],
      default: 'pending',
    },
    requestedAt: {
      type: Date,
      default: Date.now,
    },
    resolvedAt: {
      type: Date,
      default: null,
    },
    resolvedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      default: null,
    },
    message: {
      type: String,
      trim: true,
      maxlength: 500,
      default: null,
    },
  },
  {
    timestamps: true,
  }
);

// Prevent duplicate pending/active relationships for the same coach+client pair.
// A new request is only allowed once the previous one is rejected or terminated.
coachClientRelationshipSchema.index({ coach: 1, client: 1 }, { unique: false });

module.exports = mongoose.model('CoachClientRelationship', coachClientRelationshipSchema);
