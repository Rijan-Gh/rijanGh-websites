const { v4: uuidv4 } = require('uuid');

class SessionManager {
  constructor() {
    this.sessions = new Map();
    this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
    this.cleanupInterval = 5 * 60 * 1000; // 5 minutes
    this.startCleanup();
  }

  createSession(difficulty, totalQuestions) {
    const sessionId = uuidv4();
    const session = {
      id: sessionId,
      difficulty,
      totalQuestions,
      usedCharacterIds: new Set(),
      score: 0,
      streak: 0,
      maxStreak: 0,
      currentQuestion: 0,
      correctAnswers: 0,
      createdAt: Date.now(),
      lastActivity: Date.now(),
    };
    this.sessions.set(sessionId, session);
    return session;
  }

  getSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.lastActivity = Date.now();
      return session;
    }
    return null;
  }

  updateSession(sessionId, updates) {
    const session = this.sessions.get(sessionId);
    if (session) {
      Object.assign(session, updates);
      session.lastActivity = Date.now();
      return session;
    }
    return null;
  }

  deleteSession(sessionId) {
    return this.sessions.delete(sessionId);
  }

  startCleanup() {
    setInterval(() => {
      const now = Date.now();
      for (const [sessionId, session] of this.sessions.entries()) {
        if (now - session.lastActivity > this.sessionTimeout) {
          this.sessions.delete(sessionId);
        }
      }
    }, this.cleanupInterval);
  }

  getSessionStats(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;
    return {
      score: session.score,
      streak: session.streak,
      maxStreak: session.maxStreak,
      currentQuestion: session.currentQuestion,
      totalQuestions: session.totalQuestions,
      correctAnswers: session.correctAnswers,
      accuracy: session.currentQuestion > 0 
        ? Math.round((session.correctAnswers / session.currentQuestion) * 100) 
        : 0,
    };
  }
}

module.exports = new SessionManager();
