const mongoose = require('mongoose');

const workoutAssignmentSchema = new mongoose.Schema(
  {
    workout: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Workout',
      required: true,
    },
    trainer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    client: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    notes: {
      type: String,
      trim: true,
    },
    startDate: Date,
    endDate: Date,
    status: {
      type: String,
      enum: ['assigned', 'in_progress', 'completed'],
      default: 'assigned',
    },
  },
  {
    timestamps: true,
  }
);

workoutAssignmentSchema.index({ workout: 1, client: 1 }, { unique: true });

module.exports = mongoose.model('WorkoutAssignment', workoutAssignmentSchema);
