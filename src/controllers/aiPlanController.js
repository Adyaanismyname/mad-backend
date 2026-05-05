const { validationResult } = require('express-validator');
const User = require('../models/User');
const AIPlan = require('../models/AIPlan');
const CoachClientRelationship = require('../models/CoachClientRelationship');
const { generateWithFallback } = require('../config/gemini');

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
  const { age, weight, bmi, bio } = client;

  const profileBlock = [
    age != null ? `- Age: ${age} years` : null,
    weight != null ? `- Weight: ${weight} kg` : null,
    bmi != null ? `- BMI: ${bmi}` : null,
    bio ? `- Goals/Background: ${bio}` : null,
    coachNotes ? `- Coach notes: ${coachNotes}` : null,
  ]
    .filter(Boolean)
    .join('\n');

  return `Generate a 7-day meal plan based on the following client stats:

${profileBlock}

Rules:
- State daily caloric target and macro breakdown (protein/carbs/fats in grams) upfront.
- Each day: Breakfast, Morning Snack, Lunch, Afternoon Snack, Dinner. Add Evening Snack only if needed.
- Per meal: name, key ingredients, approximate calories, one-line prep tip.
- End with a short nutrition notes section (hydration, supplements, foods to avoid).
- Use ## for day headings, ### for meal headings.
- Be direct. No disclaimers. No filler text.`;
};

const buildWorkoutPrompt = (client, coachNotes) => {
  const { age, weight, bmi, bio } = client;

  const profileBlock = [
    age != null ? `- Age: ${age} years` : null,
    weight != null ? `- Weight: ${weight} kg` : null,
    bmi != null ? `- BMI: ${bmi}` : null,
    bio ? `- Goals/Background: ${bio}` : null,
    coachNotes ? `- Coach notes: ${coachNotes}` : null,
  ]
    .filter(Boolean)
    .join('\n');

  return `Generate a 7-day workout plan based on the following client stats:

${profileBlock}

Rules:
- Pick a training split suited to the goals (Push/Pull/Legs, Upper/Lower, or Full Body). State the choice and reason in one line.
- 7-day schedule with rest or active recovery where appropriate.
- Each training day: Warm-Up (5-10 min), Main Workout (exercises with sets×reps or duration, rest period, one coaching cue each), Cool-Down (5-10 min).
- End with a one-paragraph weekly progression note.
- Use ## for day headings (e.g. ## Day 1 — Push), ### for Warm-Up / Main Workout / Cool-Down.
- Be direct. No disclaimers. No filler text.`;
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
    const content = await generateWithFallback(prompt);

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
    const content = await generateWithFallback(prompt);

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
