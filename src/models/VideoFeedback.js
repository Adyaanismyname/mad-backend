const mongoose = require('mongoose');

const videoFeedbackSchema = new mongoose.Schema(
  {
    video: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'ExerciseVideo',
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
    comment: {
      type: String,
      required: true,
      trim: true,
      minlength: 1,
    },
  },
  {
    timestamps: true,
  }
);

videoFeedbackSchema.index({ video: 1, createdAt: 1 });

module.exports = mongoose.model('VideoFeedback', videoFeedbackSchema);
