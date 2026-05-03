const mongoose = require('mongoose');

const videoCommentSchema = new mongoose.Schema(
  {
    video: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Video',
      required: true,
    },
    trainer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    comment: {
      type: String,
      required: true,
      trim: true,
      maxlength: 2000,
    },
  },
  {
    timestamps: true,
  }
);

videoCommentSchema.index({ video: 1, createdAt: 1 });

module.exports = mongoose.model('VideoComment', videoCommentSchema);
