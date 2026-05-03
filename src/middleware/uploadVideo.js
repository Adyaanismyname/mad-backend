const fs = require('fs');
const path = require('path');
const multer = require('multer');

const uploadsDir = path.join(__dirname, '..', '..', 'uploads', 'videos');

const ensureUploadsDir = () => {
  if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
  }
};

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    ensureUploadsDir();
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const baseName = path.basename(file.originalname);
    const safeOriginalName = baseName.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, `${Date.now()}-${safeOriginalName}`);
  },
});

const fileFilter = (req, file, cb) => {
  if (!file.mimetype.startsWith('video/')) {
    return cb(new Error('Only video files are allowed.'));
  }

  cb(null, true);
};

const maxVideoSizeMb = Number(process.env.MAX_VIDEO_SIZE_MB || 100);

const uploadVideo = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: maxVideoSizeMb * 1024 * 1024,
  },
});

module.exports = uploadVideo;
