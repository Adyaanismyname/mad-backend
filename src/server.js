const dotenv = require('dotenv');
dotenv.config();

const app = require('./app');
const connectDB = require('./config/db');

const PORT = process.env.PORT || 8000;

// Local dev: start a real HTTP server
if (process.env.NODE_ENV !== 'production') {
  const startServer = async () => {
    try {
      await connectDB();
      app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
      });
    } catch (error) {
      console.error('Failed to start server:', error.message);
      process.exit(1);
    }
  };
  startServer();
}

// Vercel serverless export
module.exports = app;
// hello sneakpeek