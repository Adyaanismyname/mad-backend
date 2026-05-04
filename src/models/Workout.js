const mongoose = require('mongoose');

const exerciseSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      trim: true,
    },
    sets: { type: Number, default: null },
    reps: { type: Number, default: null },
    durationSec: { type: Number, default: null },
    restSec: { type: Number, default: null },
    notes: String,
  },
  { _id: false }
);

const workoutSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: true,
      trim: true,
    },
    description: {
      type: String,
      trim: true,
    },
    exercises: {
      type: [exerciseSchema],
      default: [],
    },
    createdBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    creatorRole: {
      type: String,
      enum: ['trainer', 'client'],
      required: true,
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Workout', workoutSchema);
