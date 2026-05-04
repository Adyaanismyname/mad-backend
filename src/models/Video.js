const mongoose = require('mongoose');

const videoSchema = new mongoose.Schema(
  {
    client: {
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
      maxlength: 120,
    },
    description: {
      type: String,
      trim: true,
      maxlength: 1000,
    },
    fileName: {
      type: String,
      required: true,
    },
    originalName: {
      type: String,
      required: true,
    },
    filePath: {
      type: String,
      required: true,
    },
    mimeType: {
      type: String,
      required: true,
    },
    sizeBytes: {
      type: Number,
      required: true,
      min: 1,
    },
    exerciseName: {
      type: String,
      trim: true,
      maxlength: 100,
      default: null,
    },
    status: {
      type: String,
      enum: ['uploaded', 'reviewed'],
      default: 'uploaded',
    },
    uploadedAt: {
      type: Date,
      default: Date.now,
    },
  },
  {
    timestamps: true,
  }
);

videoSchema.index({ client: 1, createdAt: -1 });

module.exports = mongoose.model('Video', videoSchema);
