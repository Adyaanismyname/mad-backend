const mongoose = require('mongoose');

const pointSchema = new mongoose.Schema(
  {
    x: { type: Number, required: true },
    y: { type: Number, required: true },
  },
  { _id: false }
);

const strokeSchema = new mongoose.Schema(
  {
    strokeId: {
      type: String,
      required: true,
    },
    type: {
      type: String,
      enum: ['freehand', 'line', 'arrow', 'rect', 'circle', 'text'],
      default: 'freehand',
    },
    color: {
      type: String,
      default: '#FF0000',
      maxlength: 20,
    },
    strokeWidth: {
      type: Number,
      default: 2,
      min: 1,
      max: 50,
    },
    points: {
      type: [pointSchema],
      default: [],
    },
    label: {
      type: String,
      maxlength: 500,
      default: null,
    },
  },
  { _id: false }
);

const videoAnnotationSchema = new mongoose.Schema(
  {
    video: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Video',
      required: true,
      unique: true,
    },
    trainer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    strokes: {
      type: [strokeSchema],
      default: [],
    },
  },
  {
    timestamps: true,
  }
);

videoAnnotationSchema.index({ video: 1 });

module.exports = mongoose.model('VideoAnnotation', videoAnnotationSchema);
