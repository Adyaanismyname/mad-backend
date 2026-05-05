const express = require('express');
const auth = require('../middleware/auth');
const allowRoles = require('../middleware/role');
const uploadVideoMiddleware = require('../middleware/uploadVideo');
const {
  uploadVideo,
  getMyVideos,
  getTrainerReviewVideos,
  getVideoById,
  addVideoComment,
  getVideoComments,
  deleteMyVideo,
} = require('../controllers/videoController');
const {
  uploadVideoValidator,
  videoIdParamValidator,
  trainerClientQueryValidator,
  addCommentValidator,
} = require('../validators/videoValidators');
const {
  getAnnotations,
  addStroke,
  deleteStroke,
  clearAnnotations,
} = require('../controllers/annotationController');
const {
  addStrokeValidator,
  strokeIdParamValidator,
} = require('../validators/annotationValidators');

const router = express.Router();

router.post(
  '/upload',
  auth,
  allowRoles('client'),
  uploadVideoMiddleware.single('video'),
  uploadVideoValidator,
  uploadVideo
);

router.get('/mine', auth, allowRoles('client'), getMyVideos);
router.get('/review', auth, allowRoles('trainer'), trainerClientQueryValidator, getTrainerReviewVideos);
router.get('/:videoId', auth, videoIdParamValidator, getVideoById);
router.get('/:videoId/comments', auth, videoIdParamValidator, getVideoComments);
router.post('/:videoId/comments', auth, allowRoles('trainer'), addCommentValidator, addVideoComment);
router.delete('/:videoId', auth, allowRoles('client'), videoIdParamValidator, deleteMyVideo);

// Annotation routes
router.get('/:videoId/annotations', auth, videoIdParamValidator, getAnnotations);
router.post('/:videoId/annotations/strokes', auth, allowRoles('trainer'), addStrokeValidator, addStroke);
router.delete('/:videoId/annotations/strokes/:strokeId', auth, allowRoles('trainer'), strokeIdParamValidator, deleteStroke);
router.delete('/:videoId/annotations', auth, allowRoles('trainer'), videoIdParamValidator, clearAnnotations);

module.exports = router;
