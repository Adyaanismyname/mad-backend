const { GoogleGenerativeAI } = require('@google/generative-ai');

if (!process.env.GEMINI_API_KEY) {
  throw new Error('GEMINI_API_KEY is not set in environment variables.');
}

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const PRIMARY_MODEL = 'gemini-2.5-flash';
const FALLBACK_MODEL = 'gemini-3.1-flash-lite-preview';

/**
 * Returns a Gemini model instance.
 * Falls back to gemini-3.1-flash-lite-preview if the primary model fails.
 */
const getModel = (modelName = PRIMARY_MODEL) => genAI.getGenerativeModel({ model: modelName });

/**
 * Generate content with automatic fallback to FALLBACK_MODEL on error.
 */
const generateWithFallback = async (prompt) => {
  try {
    const model = getModel(PRIMARY_MODEL);
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (err) {
    console.warn(`Primary model (${PRIMARY_MODEL}) failed: ${err.message}. Trying fallback...`);
    const fallback = getModel(FALLBACK_MODEL);
    const result = await fallback.generateContent(prompt);
    return result.response.text();
  }
};

module.exports = { getModel, generateWithFallback };
