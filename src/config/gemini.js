const { GoogleGenerativeAI } = require('@google/generative-ai');

if (!process.env.GEMINI_API_KEY) {
  throw new Error('GEMINI_API_KEY is not set in environment variables.');
}

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

/**
 * Returns a Gemini model instance.
 * Default: gemini-2.0-flash-lite (fast, higher free tier limits)
 */
const getModel = (modelName = 'gemini-2.5-flash') => genAI.getGenerativeModel({ model: modelName });

module.exports = { getModel };
