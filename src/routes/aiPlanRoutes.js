const express = require('express');
const auth = require('../middleware/auth');
const allowRoles = require('../middleware/role');
const {
  generateDietPlan,
  generateWorkoutPlan,
  getPlansForClient,
  getMyPlans,
  deletePlan,
} = require('../controllers/aiPlanController');
const {
  clientIdParamValidator,
  planIdParamValidator,
  coachNotesValidator,
  planTypeQueryValidator,
} = require('../validators/aiPlanValidators');

const router = express.Router();

// Trainer: generate plans for a client
router.post(
  '/:clientId/diet',
  auth,
  allowRoles('trainer'),
  [...clientIdParamValidator, ...coachNotesValidator],
  generateDietPlan
);

router.post(
  '/:clientId/workout',
  auth,
  allowRoles('trainer'),
  [...clientIdParamValidator, ...coachNotesValidator],
  generateWorkoutPlan
);

// Trainer or client: list plans for a client
router.get(
  '/mine',
  auth,
  allowRoles('client'),
  planTypeQueryValidator,
  getMyPlans
);

router.get(
  '/:clientId',
  auth,
  [...clientIdParamValidator, ...planTypeQueryValidator],
  getPlansForClient
);

// Trainer: delete a plan they generated
router.delete(
  '/:planId',
  auth,
  allowRoles('trainer'),
  planIdParamValidator,
  deletePlan
);

module.exports = router;
