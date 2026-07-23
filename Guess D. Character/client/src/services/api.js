import axios from 'axios';

const API_BASE_URL = '/api';

export const gameApi = {
  async startGame(difficulty = 'medium', totalQuestions = 10) {
    const response = await axios.post(`${API_BASE_URL}/game/start`, {
      difficulty,
      totalQuestions,
    });
    return response.data;
  },

  async getNextQuestion(sessionId) {
    const response = await axios.get(`${API_BASE_URL}/game/question/${sessionId}`);
    return response.data;
  },

  async submitAnswer(sessionId, questionId, selectedId) {
    const response = await axios.post(`${API_BASE_URL}/game/answer`, {
      sessionId,
      questionId,
      selectedId,
    });
    return response.data;
  },

  async getStats(sessionId) {
    const response = await axios.get(`${API_BASE_URL}/game/stats/${sessionId}`);
    return response.data;
  },

  async deleteSession(sessionId) {
    const response = await axios.delete(`${API_BASE_URL}/game/session/${sessionId}`);
    return response.data;
  },
};
