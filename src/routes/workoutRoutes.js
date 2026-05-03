const express = require('express');
const auth = require('../middleware/auth');
const allowRoles = require('../middleware/role');
const {
  createWorkout,
  assignWorkout,
  getMyCreatedWorkouts,
  getAssignedWorkoutsForClient,
  getAssignmentsForTrainer,
} = require('../controllers/workoutController');
const {
  createWorkoutValidator,
  assignWorkoutValidator,
} = require('../validators/workoutValidators');

const router = express.Router();

router.post('/trainer', auth, allowRoles('trainer'), createWorkoutValidator, createWorkout);
router.post('/client', auth, allowRoles('client'), createWorkoutValidator, createWorkout);
router.post(
  '/:id/assign',
  auth,
  allowRoles('trainer'),
  assignWorkoutValidator,
  assignWorkout
);

router.get('/mine', auth, getMyCreatedWorkouts);
router.get('/assigned/me', auth, allowRoles('client'), getAssignedWorkoutsForClient);
router.get('/assigned/by-me', auth, allowRoles('trainer'), getAssignmentsForTrainer);

module.exports = router;
