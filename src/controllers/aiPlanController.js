const { validationResult } = require('express-validator');
const User = require('../models/User');
const AIPlan = require('../models/AIPlan');
const CoachClientRelationship = require('../models/CoachClientRelationship');
const { getModel } = require('../config/gemini');

const ensureValidation = (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    return false;
  }
  return true;
};

/**
 * Verify the requesting trainer has an active relationship with the target client.
 */
const verifyTrainerClientAccess = async (trainerId, clientId) => {
  const rel = await CoachClientRelationship.findOne({
    coach: trainerId,
    client: clientId,
    status: 'active',
  }).select('_id');
  return Boolean(rel);
};

// ─────────────────────────────────────────────
// PROMPT BUILDERS
// ─────────────────────────────────────────────

const buildDietPrompt = (client, coachNotes) => {
  const { name, age, weight, bmi, bio } = client;

  const profileBlock = [
    `- Name: ${name}`,
    age != null ? `- Age: ${age} years` : null,
    weight != null ? `- Weight: ${weight} kg` : null,
    bmi != null ? `- BMI: ${bmi}` : null,
    bio ? `- Goals / Background: ${bio}` : null,
    coachNotes ? `- Coach notes: ${coachNotes}` : null,
  ]
    .filter(Boolean)
    .join('\n');

  return `You are an expert sports nutritionist and registered dietitian working with a personal trainer who manages clients via a fitness app.

The trainer has provided the following client profile:

${profileBlock}

Your task is to create a detailed, personalized 7-day meal plan for this client. Follow these rules:

1. Calculate an appropriate daily caloric target based on the client's stats and goals.
2. Distribute macros sensibly (protein, carbs, fats) and state the daily macro targets in grams.
3. Provide a full day-by-day plan: Breakfast, Mid-Morning Snack, Lunch, Afternoon Snack, Dinner, and (if needed) an Evening Snack.
4. For each meal include: meal name, key ingredients, approximate calories, and a one-line preparation tip.
5. Highlight any important nutritional notes (e.g. hydration, supplementation, foods to avoid).
6. Use clear markdown formatting: use ## for day headings and ### for meal headings.
7. Keep language practical and motivating — the trainer will share this directly with the client in the app.
8. Do not add disclaimers about consulting a doctor unless a specific medical condition is mentioned.

Begin the plan now.`;
};

const buildWorkoutPrompt = (client, coachNotes) => {
  const { name, age, weight, bmi, bio } = client;

  const profileBlock = [
    `- Name: ${name}`,
    age != null ? `- Age: ${age} years` : null,
    weight != null ? `- Weight: ${weight} kg` : null,
    bmi != null ? `- BMI: ${bmi}` : null,
    bio ? `- Goals / Background: ${bio}` : null,
    coachNotes ? `- Coach notes: ${coachNotes}` : null,
  ]
    .filter(Boolean)
    .join('\n');

  return `You are an expert certified personal trainer (CPT) and strength & conditioning coach working inside a fitness app called Fit & Fuel.

The trainer has provided the following client profile:

${profileBlock}

Your task is to design a detailed, personalized weekly workout plan for this client. Follow these rules:

1. Choose an appropriate training split (e.g. Push/Pull/Legs, Upper/Lower, Full Body) based on the client's goals and fitness level. Explain your choice briefly.
2. Provide a 7-day schedule. Include rest days or active recovery where appropriate.
3. For each training day:
   - State the day's focus (e.g. "Day 1 — Chest & Triceps")
   - List every exercise with: sets × reps (or time for cardio/holds), rest period, and a short coaching cue.
4. Include a warm-up routine (5-10 min) and cool-down/stretch routine (5-10 min) for each training day.
5. Add a progression note at the end explaining how the client should increase intensity week over week.
6. Use clear markdown formatting: use ## for day headings and ### for section headings (Warm-Up, Main Workout, Cool-Down).
7. Keep language practical and motivating — the trainer will share this directly with the client in the app.

Begin the plan now.`;
};

// ─────────────────────────────────────────────
// CONTROLLERS
// ─────────────────────────────────────────────

/**
 * POST /api/ai-plans/:clientId/diet
 * Trainer generates a personalized diet plan for a client.
 */
const generateDietPlan = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const { clientId } = req.params;
    const { coachNotes } = req.body;

    const hasAccess = await verifyTrainerClientAccess(req.user._id, clientId);
    if (!hasAccess) {
      return res.status(403).json({
        message: 'You do not have an active relationship with this client.',
      });
    }

    const client = await User.findById(clientId).select('name profile role');
    if (!client || client.role !== 'client') {
      return res.status(404).json({ message: 'Client not found.' });
    }

    const clientData = {
      name: client.name,
      age: client.profile?.age ?? null,
      weight: client.profile?.weight ?? null,
      bmi: client.profile?.bmi ?? null,
      bio: client.profile?.bio ?? null,
    };

    const prompt = buildDietPrompt(clientData, coachNotes);
    const model = getModel();
    const result = await model.generateContent(prompt);
    const content = result.response.text();

    const plan = await AIPlan.create({
      client: clientId,
      generatedBy: req.user._id,
      type: 'diet',
      coachNotes: coachNotes || null,
      clientSnapshot: clientData,
      content,
    });

    res.status(201).json({
      message: 'Diet plan generated successfully.',
      plan,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * POST /api/ai-plans/:clientId/workout
 * Trainer generates a personalized workout plan for a client.
 */
const generateWorkoutPlan = async (req, res, next) => {
  try {
    if (!ensureValidation(req, res)) return;

    const { clientId } = req.params;
    const { coachNotes } = req.body;

    const hasAccess = await verifyTrainerClientAccess(req.user._id, clientId);
    if (!hasAccess) {
      return res.status(403).json({
        message: 'You do not have an active relationship with this client.',
      });
    }

    const client = await User.findById(clientId).select('name profile role');
    if (!client || client.role !== 'client') {
      return res.status(404).json({ message: 'Client not found.' });
    }

    const clientData = {
      name: client.name,
      age: client.profile?.age ?? null,
      weight: client.profile?.weight ?? null,
      bmi: client.profile?.bmi ?? null,
      bio: client.profile?.bio ?? null,
    };

    const prompt = buildWorkoutPrompt(clientData, coachNotes);
    const model = getModel();
    const result = await model.generateContent(prompt);
    const content = result.response.text();

    const plan = await AIPlan.create({
      client: clientId,
      generatedBy: req.user._id,
      type: 'workout',
      coachNotes: coachNotes || null,
      clientSnapshot: clientData,
      content,
    });

    res.status(201).json({
      message: 'Workout plan generated successfully.',
      plan,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/ai-plans/:clientId
 * Trainer: list all AI plans for a specific client.
 * Client: list their own plans (clientId must match their own id).
 */
const getPlansForClient = async (req, res, next) => {
  try {
    const { clientId } = req.params;
    const { type } = req.query;

    if (req.user.role === 'client') {
      if (req.user._id.toString() !== clientId) {
        return res.status(403).json({ message: 'You can only view your own plans.' });
      }
    } else {
      // trainer
      const hasAccess = await verifyTrainerClientAccess(req.user._id, clientId);
      if (!hasAccess) {
        return res.status(403).json({
          message: 'You do not have an active relationship with this client.',
        });
      }
    }

    const filter = { client: clientId };
    if (type === 'diet' || type === 'workout') filter.type = type;

    const plans = await AIPlan.find(filter)
      .populate('generatedBy', 'name email')
      .sort({ createdAt: -1 });

    res.status(200).json({ plans });
  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/ai-plans/mine
 * Client: shortcut to list their own AI plans.
 */
const getMyPlans = async (req, res, next) => {
  try {
    const { type } = req.query;
    const filter = { client: req.user._id };
    if (type === 'diet' || type === 'workout') filter.type = type;

    const plans = await AIPlan.find(filter)
      .populate('generatedBy', 'name email')
      .sort({ createdAt: -1 });

    res.status(200).json({ plans });
  } catch (error) {
    next(error);
  }
};

/**
 * DELETE /api/ai-plans/:planId
 * Trainer: delete a plan they generated.
 */
const deletePlan = async (req, res, next) => {
  try {
    const plan = await AIPlan.findOne({
      _id: req.params.planId,
      generatedBy: req.user._id,
    });

    if (!plan) {
      return res.status(404).json({ message: 'Plan not found or not owned by you.' });
    }

    await plan.deleteOne();
    res.status(200).json({ message: 'Plan deleted.' });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  generateDietPlan,
  generateWorkoutPlan,
  getPlansForClient,
  getMyPlans,
  deletePlan,
};
