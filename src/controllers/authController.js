const { validationResult } = require('express-validator');
const User = require('../models/User');
const generateToken = require('../utils/generateToken');

const validateRequest = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    const err = new Error('Validation failed');
    err.statusCode = 400;
    err.details = errors.array();
    throw err;
  }
};

const validateRoleProfile = (role, profile = {}) => {
  if (role === 'client') {
    if (profile.age == null || profile.weight == null || profile.bmi == null) {
      const err = new Error('Clients must provide age, weight, and bmi.');
      err.statusCode = 400;
      throw err;
    }
  }

  if (role === 'trainer') {
    if (profile.experienceYears == null || !profile.expertise) {
      const err = new Error('Trainers must provide experienceYears and expertise.');
      err.statusCode = 400;
      throw err;
    }
  }
};

const signup = async (req, res, next) => {
  try {
    validateRequest(req);

    const { name, email, password, role, profile } = req.body;
    validateRoleProfile(role, profile);

    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) {
      return res.status(409).json({ message: 'Email already in use.' });
    }

    const user = await User.create({
      name,
      email: email.toLowerCase(),
      password,
      role,
      profile,
    });

    const token = generateToken(user._id.toString());

    res.status(201).json({
      message: 'Signup successful',
      token,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        profile: user.profile,
      },
    });
  } catch (error) {
    if (error.details) {
      return res.status(400).json({ message: error.message, errors: error.details });
    }
    next(error);
  }
};

const login = async (req, res, next) => {
  try {
    validateRequest(req);

    const { email, password } = req.body;

    const user = await User.findOne({ email: email.toLowerCase() }).select('+password');
    if (!user) {
      return res.status(401).json({ message: 'Invalid credentials.' });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({ message: 'Invalid credentials.' });
    }

    const token = generateToken(user._id.toString());

    res.status(200).json({
      message: 'Login successful',
      token,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        profile: user.profile,
      },
    });
  } catch (error) {
    if (error.details) {
      return res.status(400).json({ message: error.message, errors: error.details });
    }
    next(error);
  }
};

const me = async (req, res) => {
  res.status(200).json({ user: req.user });
};

module.exports = {
  signup,
  login,
  me,
};
