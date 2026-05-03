const mongoose = require('mongoose');

const exerciseVideoSchema = new mongoose.Schema(
  {
    client: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    trainer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    workout: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Workout',
    },
    workoutAssignment: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'WorkoutAssignment',
    },
    title: {
      type: String,
      required: true,
      trim: true,
    },
    description: {
      type: String,
      trim: true,
    },
    originalFileName: {
      type: String,
      required: true,
    },
    storedFileName: {
      type: String,
      required: true,
      unique: true,
    },
    filePath: {
      type: String,
      required: true,
    },
    mimeType: {
      type: String,
      required: true,
    },
    fileSizeBytes: {
      type: Number,
      required: true,
    },
    status: {
      type: String,
      enum: ['uploaded', 'reviewed'],
      default: 'uploaded',
    },
    reviewedAt: Date,
  },
  {
    timestamps: true,
  }
);

exerciseVideoSchema.index({ client: 1, createdAt: -1 });
exerciseVideoSchema.index({ trainer: 1, createdAt: -1 });

module.exports = mongoose.model('ExerciseVideo', exerciseVideoSchema);
