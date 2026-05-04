const { GoogleGenerativeAI } = require('@google/generative-ai');

if (!process.env.GEMINI_API_KEY) {
  throw new Error('GEMINI_API_KEY is not set in environment variables.');
}

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

/**
 * Returns a Gemini model instance.
 * Default: gemini-1.5-flash (fast, cost-effective for structured text generation)
 */
const getModel = (modelName = 'gemini-1.5-flash') => genAI.getGenerativeModel({ model: modelName });

module.exports = { getModel };
