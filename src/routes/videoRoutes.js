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

module.exports = router;
