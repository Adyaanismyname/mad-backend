const { randomUUID } = require('crypto');
const { validationResult } = require('express-validator');
const Video = require('../models/Video');
const VideoAnnotation = require('../models/VideoAnnotation');
const WorkoutAssignment = require('../models/WorkoutAssignment');

const ensureValidation = (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    return false;
  }
  return true;
};

const trainerHasAccessToClient = async (trainerId, clientId) => {
  const assignment = await WorkoutAssignment.findOne({
    trainer: trainerId,
    client: clientId,
  }).select('_id');
  return Boolean(assignment);
};

const resolveVideoAccess = async (req, res) => {
  const video = await Video.findById(req.params.videoId).select('client');
  if (!video) {
    res.status(404).json({ message: 'Video not found' });
    return null;
  }

  if (req.user.role === 'client') {
    if (video.client.toString() !== req.user._id.toString()) {
      res.status(403).json({ message: 'Forbidden: not your video' });
      return null;
    }
  } else if (req.user.role === 'trainer') {
    const allowed = await trainerHasAccessToClient(req.user._id, video.client);
    if (!allowed) {
      res.status(403).json({ message: 'Forbidden: client not assigned to you' });
      return null;
    }
  } else {
    res.status(403).json({ message: 'Forbidden' });
    return null;
  }

  return video;
};

/**
 * GET /api/videos/:videoId/annotations
 * Client (own video) or trainer (assigned client video) can read.
 */
const getAnnotations = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const video = await resolveVideoAccess(req, res);
    if (!video) return;

    const annotation = await VideoAnnotation.findOne({ video: req.params.videoId });

    if (!annotation) {
      return res.status(200).json({ strokes: [] });
    }

    res.status(200).json({ strokes: annotation.strokes });
  } catch (error) {
    next(error);
  }
};

/**
 * POST /api/videos/:videoId/annotations/strokes
 * Trainer only — adds a single stroke to the video's annotation layer.
 */
const addStroke = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const video = await Video.findById(req.params.videoId).select('client');
    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    const allowed = await trainerHasAccessToClient(req.user._id, video.client);
    if (!allowed) {
      return res.status(403).json({ message: 'Forbidden: client not assigned to you' });
    }

    const strokeId = randomUUID();
    const { type, color, strokeWidth, points, label } = req.body;

    const newStroke = {
      strokeId,
      type: type || 'freehand',
      color: color || '#FF0000',
      strokeWidth: strokeWidth !== undefined ? strokeWidth : 2,
      points: points || [],
      label: label || null,
    };

    const annotation = await VideoAnnotation.findOneAndUpdate(
      { video: req.params.videoId },
      {
        $setOnInsert: { trainer: req.user._id },
        $push: { strokes: newStroke },
      },
      { upsert: true, new: true }
    );

    res.status(201).json({
      message: 'Stroke added successfully',
      stroke: newStroke,
      strokes: annotation.strokes,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * DELETE /api/videos/:videoId/annotations/strokes/:strokeId
 * Trainer only — removes a single stroke by its strokeId.
 */
const deleteStroke = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const video = await Video.findById(req.params.videoId).select('client');
    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    const allowed = await trainerHasAccessToClient(req.user._id, video.client);
    if (!allowed) {
      return res.status(403).json({ message: 'Forbidden: client not assigned to you' });
    }

    const annotation = await VideoAnnotation.findOneAndUpdate(
      { video: req.params.videoId },
      { $pull: { strokes: { strokeId: req.params.strokeId } } },
      { new: true }
    );

    if (!annotation) {
      return res.status(404).json({ message: 'No annotations found for this video' });
    }

    res.status(200).json({
      message: 'Stroke deleted successfully',
      strokes: annotation.strokes,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * DELETE /api/videos/:videoId/annotations
 * Trainer only — clears all strokes for a video.
 */
const clearAnnotations = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const video = await Video.findById(req.params.videoId).select('client');
    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    const allowed = await trainerHasAccessToClient(req.user._id, video.client);
    if (!allowed) {
      return res.status(403).json({ message: 'Forbidden: client not assigned to you' });
    }

    await VideoAnnotation.findOneAndUpdate(
      { video: req.params.videoId },
      { $set: { strokes: [] } }
    );

    res.status(200).json({ message: 'All annotations cleared' });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getAnnotations,
  addStroke,
  deleteStroke,
  clearAnnotations,
};
