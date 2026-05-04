const express = require('express');
const auth = require('../middleware/auth');
const allowRoles = require('../middleware/role');
const {
  sendRequest,
  getMyRequests,
  getIncomingRequests,
  acceptRequest,
  rejectRequest,
  terminateRelationship,
  getMyCoach,
  getMyClients,
} = require('../controllers/relationshipController');
const {
  sendRequestValidator,
  relationshipIdParamValidator,
} = require('../validators/relationshipValidators');

const router = express.Router();

// Client routes
router.post('/request', auth, allowRoles('client'), sendRequestValidator, sendRequest);
router.get('/my-requests', auth, allowRoles('client'), getMyRequests);
router.get('/my-coach', auth, allowRoles('client'), getMyCoach);

// Trainer routes
router.get('/incoming', auth, allowRoles('trainer'), getIncomingRequests);
router.get('/my-clients', auth, allowRoles('trainer'), getMyClients);
router.patch('/:id/accept', auth, allowRoles('trainer'), relationshipIdParamValidator, acceptRequest);
router.patch('/:id/reject', auth, allowRoles('trainer'), relationshipIdParamValidator, rejectRequest);

// Both roles can terminate
router.patch('/:id/terminate', auth, relationshipIdParamValidator, terminateRelationship);

module.exports = router;
