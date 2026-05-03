const { validationResult } = require('express-validator');
const User = require('../models/User');
const Workout = require('../models/Workout');
const WorkoutAssignment = require('../models/WorkoutAssignment');

const createWorkout = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const { title, description, exercises } = req.body;

    const workout = await Workout.create({
      title,
      description,
      exercises,
      createdBy: req.user._id,
      creatorRole: req.user.role,
    });

    res.status(201).json({ message: 'Workout created successfully', workout });
  } catch (error) {
    next(error);
  }
};

const assignWorkout = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }

    const { id: workoutId } = req.params;
    const { clientId, notes, startDate, endDate } = req.body;

    const workout = await Workout.findById(workoutId);
    if (!workout) {
      return res.status(404).json({ message: 'Workout not found' });
    }

    if (workout.creatorRole !== 'trainer' || workout.createdBy.toString() !== req.user._id.toString()) {
      return res.status(403).json({
        message: 'You can only assign trainer workouts created by yourself.',
      });
    }

    const client = await User.findById(clientId);
    if (!client || client.role !== 'client') {
      return res.status(400).json({ message: 'Invalid clientId' });
    }

    const assignment = await WorkoutAssignment.findOneAndUpdate(
      { workout: workoutId, client: clientId },
      {
        workout: workoutId,
        trainer: req.user._id,
        client: clientId,
        notes,
        startDate,
        endDate,
      },
      {
        upsert: true,
        returnDocument: 'after',
        runValidators: true,
        setDefaultsOnInsert: true,
      }
    )
      .populate('workout')
      .populate('client', 'name email role')
      .populate('trainer', 'name email role');

    res.status(200).json({
      message: 'Workout assigned successfully',
      assignment,
    });
  } catch (error) {
    next(error);
  }
};

const getMyCreatedWorkouts = async (req, res, next) => {
  try {
    const workouts = await Workout.find({ createdBy: req.user._id }).sort({ createdAt: -1 });
    res.status(200).json({ workouts });
  } catch (error) {
    next(error);
  }
};

const getAssignedWorkoutsForClient = async (req, res, next) => {
  try {
    const assignments = await WorkoutAssignment.find({ client: req.user._id })
      .populate('workout')
      .populate('trainer', 'name email profile.expertise')
      .sort({ createdAt: -1 });

    res.status(200).json({ assignments });
  } catch (error) {
    next(error);
  }
};

const getAssignmentsForTrainer = async (req, res, next) => {
  try {
    const assignments = await WorkoutAssignment.find({ trainer: req.user._id })
      .populate('workout')
      .populate('client', 'name email profile.age profile.weight profile.bmi')
      .sort({ createdAt: -1 });

    res.status(200).json({ assignments });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  createWorkout,
  assignWorkout,
  getMyCreatedWorkouts,
  getAssignedWorkoutsForClient,
  getAssignmentsForTrainer,
};
