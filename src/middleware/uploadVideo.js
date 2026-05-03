const fs = require('fs');
const path = require('path');
const multer = require('multer');

const uploadDir = process.env.VIDEO_UPLOAD_DIR || path.join(process.cwd(), 'uploads', 'videos');
fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const safeOriginal = file.originalname.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9._-]/g, '');
    const ext = path.extname(safeOriginal) || '.mp4';
    const base = path.basename(safeOriginal, ext) || 'video';
    const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, `${base}-${unique}${ext}`);
  },
});

const videoOnlyFilter = (req, file, cb) => {
  if (!file.mimetype || !file.mimetype.startsWith('video/')) {
    return cb(new Error('Only video files are allowed'));
  }

  cb(null, true);
};

const maxSizeMb = Number(process.env.MAX_VIDEO_SIZE_MB || 200);

const uploadVideo = multer({
  storage,
  fileFilter: videoOnlyFilter,
  limits: {
    fileSize: maxSizeMb * 1024 * 1024,
  },
});

module.exports = uploadVideo;
