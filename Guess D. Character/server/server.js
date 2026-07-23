const express = require('express');
const cors = require('cors');
const sessionManager = require('./sessionManager');
const { getCharacterPool, generateQuestion } = require('./gameUtils');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', activeSessions: sessionManager.sessions.size });
});

// Start a new game session
app.post('/api/game/start', (req, res) => {
  try {
    const { difficulty = 'medium', totalQuestions = 10 } = req.body;
    
    if (!['easy', 'medium', 'hard'].includes(difficulty)) {
      return res.status(400).json({ error: 'Invalid difficulty level' });
    }

    if (totalQuestions !== 'endless' && (totalQuestions < 1 || totalQuestions > 100)) {
      return res.status(400).json({ error: 'Invalid number of questions' });
    }

    const session = sessionManager.createSession(difficulty, totalQuestions);
    const pool = getCharacterPool(difficulty);
    const question = generateQuestion(session, pool);

    if (!question) {
      sessionManager.deleteSession(session.id);
      return res.status(500).json({ error: 'Failed to generate question' });
    }

    session.usedCharacterIds.add(question.questionId);
    session.currentQuestion++;

    res.json({
      sessionId: session.id,
      question,
      totalQuestions: session.totalQuestions,
      currentQuestion: session.currentQuestion,
    });
  } catch (error) {
    console.error('Error starting game:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get next question
app.get('/api/game/question/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    const session = sessionManager.getSession(sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    // Check if game should end
    if (session.totalQuestions !== 'endless' && session.currentQuestion >= session.totalQuestions) {
      return res.json({
        gameFinished: true,
        stats: sessionManager.getSessionStats(sessionId),
      });
    }

    const pool = getCharacterPool(session.difficulty);
    const question = generateQuestion(session, pool);

    if (!question) {
      return res.json({
        gameFinished: true,
        stats: sessionManager.getSessionStats(sessionId),
      });
    }

    session.usedCharacterIds.add(question.questionId);
    session.currentQuestion++;

    res.json({
      question,
      currentQuestion: session.currentQuestion,
      totalQuestions: session.totalQuestions,
    });
  } catch (error) {
    console.error('Error getting question:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Submit answer
app.post('/api/game/answer', (req, res) => {
  try {
    const { sessionId, questionId, selectedId } = req.body;

    if (!sessionId || !questionId || !selectedId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const session = sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    const pool = getCharacterPool(session.difficulty);
    const correctCharacter = pool.find(char => char.id === questionId);

    if (!correctCharacter) {
      return res.status(404).json({ error: 'Character not found' });
    }

    const isCorrect = selectedId === questionId;

    if (isCorrect) {
      session.score += 10 + (session.streak * 2); // Base 10 points + streak bonus
      session.streak++;
      session.correctAnswers++;
      if (session.streak > session.maxStreak) {
        session.maxStreak = session.streak;
      }
    } else {
      session.streak = 0;
    }

    const isGameFinished = session.totalQuestions !== 'endless' && session.currentQuestion >= session.totalQuestions;

    res.json({
      correct: isCorrect,
      correctAnswer: {
        id: correctCharacter.id,
        name: correctCharacter.character_en,
        anime: correctCharacter.anime_en,
      },
      score: session.score,
      streak: session.streak,
      gameFinished: isGameFinished,
      ...(isGameFinished && { stats: sessionManager.getSessionStats(sessionId) }),
    });
  } catch (error) {
    console.error('Error submitting answer:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get session stats
app.get('/api/game/stats/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    const stats = sessionManager.getSessionStats(sessionId);

    if (!stats) {
      return res.status(404).json({ error: 'Session not found' });
    }

    res.json(stats);
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete session
app.delete('/api/game/session/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    sessionManager.deleteSession(sessionId);
    res.json({ message: 'Session deleted' });
  } catch (error) {
    console.error('Error deleting session:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
