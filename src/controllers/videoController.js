const path = require('path');
const fs = require('fs');
const { validationResult } = require('express-validator');
const WorkoutAssignment = require('../models/WorkoutAssignment');
const Workout = require('../models/Workout');
const Video = require('../models/Video');
const VideoComment = require('../models/VideoComment');

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

const uploadVideo = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    if (!req.file) {
      return res.status(400).json({ message: 'video file is required (field name: video)' });
    }

    const { title, description, workoutId, workoutAssignmentId, exerciseName } = req.body;

    if (workoutId) {
      const workout = await Workout.findById(workoutId).select('_id createdBy');
      if (!workout) {
        return res.status(404).json({ message: 'Workout not found for workoutId' });
      }

      const ownsWorkout = workout.createdBy.toString() === req.user._id.toString();
      if (!ownsWorkout) {
        const isAssignedWorkout = await WorkoutAssignment.findOne({
          client: req.user._id,
          workout: workoutId,
        }).select('_id');

        if (!isAssignedWorkout) {
          return res.status(403).json({
            message: 'You can only link workouts created by you or assigned to you.',
          });
        }
      }
    }

    if (workoutAssignmentId) {
      const assignment = await WorkoutAssignment.findById(workoutAssignmentId).select('client');
      if (!assignment) {
        return res.status(404).json({ message: 'Workout assignment not found' });
      }
      if (assignment.client.toString() !== req.user._id.toString()) {
        return res.status(403).json({ message: 'You can only link assignments for yourself.' });
      }
    }

    const relativeFilePath = path.join('uploads', 'videos', req.file.filename);

    const video = await Video.create({
      client: req.user._id,
      workout: workoutId || undefined,
      workoutAssignment: workoutAssignmentId || undefined,
      title: title || 'Workout Video',
      description,
      exerciseName: exerciseName || null,
      fileName: req.file.filename,
      originalName: req.file.originalname,
      filePath: relativeFilePath,
      mimeType: req.file.mimetype,
      sizeBytes: req.file.size,
    });

    res.status(201).json({
      message: 'Video uploaded successfully',
      video,
      playbackUrl: `/${relativeFilePath.replace(/\\/g, '/')}`,
    });
  } catch (error) {
    next(error);
  }
};

const getMyVideos = async (req, res, next) => {
  try {
    const videos = await Video.find({ client: req.user._id })
      .populate('workout', 'title')
      .populate('workoutAssignment', 'status startDate endDate')
      .sort({ createdAt: -1 });

    res.status(200).json({ videos });
  } catch (error) {
    next(error);
  }
};

const getTrainerReviewVideos = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const { clientId } = req.query;
    let allowedClientIds = await WorkoutAssignment.find({ trainer: req.user._id }).distinct('client');

    allowedClientIds = allowedClientIds.map((id) => id.toString());

    if (clientId) {
      const access = await trainerHasAccessToClient(req.user._id, clientId);
      if (!access) {
        return res.status(403).json({ message: 'You do not have access to this client videos.' });
      }
      allowedClientIds = [clientId];
    }

    const videos = await Video.find({ client: { $in: allowedClientIds } })
      .populate('client', 'name email profile')
      .populate('workout', 'title')
      .populate('workoutAssignment', 'status startDate endDate')
      .sort({ createdAt: -1 });

    res.status(200).json({ videos });
  } catch (error) {
    next(error);
  }
};

const verifyVideoAccess = async (videoId, user) => {
  const video = await Video.findById(videoId)
    .populate('client', 'name email role profile')
    .populate('workout', 'title')
    .populate('workoutAssignment', 'status startDate endDate');

  if (!video) {
    return { error: { status: 404, message: 'Video not found' } };
  }

  if (user.role === 'client') {
    if (video.client._id.toString() !== user._id.toString()) {
      return { error: { status: 403, message: 'You can only access your own videos.' } };
    }
  }

  if (user.role === 'trainer') {
    const allowed = await trainerHasAccessToClient(user._id, video.client._id);
    if (!allowed) {
      return { error: { status: 403, message: 'You do not have access to this video.' } };
    }
  }

  return { video };
};

const getVideoById = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const result = await verifyVideoAccess(req.params.videoId, req.user);
    if (result.error) {
      return res.status(result.error.status).json({ message: result.error.message });
    }

    res.status(200).json({ video: result.video });
  } catch (error) {
    next(error);
  }
};

const addVideoComment = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const result = await verifyVideoAccess(req.params.videoId, req.user);
    if (result.error) {
      return res.status(result.error.status).json({ message: result.error.message });
    }

    const commentDoc = await VideoComment.create({
      video: req.params.videoId,
      trainer: req.user._id,
      comment: req.body.comment,
    });

    await Video.findByIdAndUpdate(req.params.videoId, { status: 'reviewed' });

    const comment = await VideoComment.findById(commentDoc._id).populate(
      'trainer',
      'name email role profile.expertise'
    );

    res.status(201).json({
      message: 'Feedback added successfully',
      comment,
    });
  } catch (error) {
    next(error);
  }
};

const getVideoComments = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const result = await verifyVideoAccess(req.params.videoId, req.user);
    if (result.error) {
      return res.status(result.error.status).json({ message: result.error.message });
    }

    const comments = await VideoComment.find({ video: req.params.videoId })
      .populate('trainer', 'name email role profile.expertise')
      .sort({ createdAt: 1 });

    res.status(200).json({ comments });
  } catch (error) {
    next(error);
  }
};

const deleteMyVideo = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const video = await Video.findById(req.params.videoId);
    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    if (video.client.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'You can only delete your own videos.' });
    }

    await VideoComment.deleteMany({ video: video._id });
    await Video.findByIdAndDelete(video._id);

    const absolutePath = path.join(__dirname, '..', '..', video.filePath);
    if (fs.existsSync(absolutePath)) {
      fs.unlinkSync(absolutePath);
    }

    res.status(200).json({ message: 'Video deleted successfully' });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  uploadVideo,
  getMyVideos,
  getTrainerReviewVideos,
  getVideoById,
  addVideoComment,
  getVideoComments,
  deleteMyVideo,
};
