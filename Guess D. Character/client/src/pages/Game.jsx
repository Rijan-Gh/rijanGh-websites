import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import CharacterCard from '../components/CharacterCard';
import OptionButton from '../components/OptionButton';
import ProgressBar from '../components/ProgressBar';
import ScoreBoard from '../components/ScoreBoard';
import ResultPopup from '../components/ResultPopup';
import LoadingSpinner from '../components/LoadingSpinner';
import GameOverModal from '../components/GameOverModal';
import { gameApi } from '../services/api';

const Game = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { difficulty, questionCount } = location.state || { difficulty: 'medium', questionCount: 10 };

  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(questionCount);
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [gameOver, setGameOver] = useState(false);
  const [gameStats, setGameStats] = useState(null);

  useEffect(() => {
    startGame();
  }, []);

  const startGame = async () => {
    try {
      setIsLoading(true);
      const response = await gameApi.startGame(difficulty, questionCount);
      setSessionId(response.sessionId);
      setQuestion(response.question);
      setCurrentQuestion(response.currentQuestion);
      setTotalQuestions(response.totalQuestions);
      setIsLoading(false);
    } catch (error) {
      console.error('Error starting game:', error);
      navigate('/');
    }
  };

  const loadNextQuestion = async () => {
    try {
      setIsLoading(true);
      const response = await gameApi.getNextQuestion(sessionId);
      
      if (response.gameFinished) {
        setGameOver(true);
        setGameStats(response.stats);
        setIsLoading(false);
        return;
      }

      setQuestion(response.question);
      setCurrentQuestion(response.currentQuestion);
      setTotalQuestions(response.totalQuestions);
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading next question:', error);
      navigate('/');
    }
  };

  const handleAnswer = async (optionId) => {
    if (showResult || isLoading) return;

    setSelectedOption(optionId);
    setShowResult(true);

    try {
      const response = await gameApi.submitAnswer(sessionId, question.questionId, optionId);
      setScore(response.score);
      setStreak(response.streak);
      setResultData({
        correct: response.correct,
        characterName: response.correctAnswer.name,
        animeName: response.correctAnswer.anime,
      });

      if (response.gameFinished) {
        setGameOver(true);
        setGameStats(response.stats);
      } else {
        setTimeout(() => {
          setShowResult(false);
          setSelectedOption(null);
          setResultData(null);
          loadNextQuestion();
        }, 2000);
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  const handleKeyDown = (e) => {
    if (showResult || isLoading || !question) return;
    
    const key = parseInt(e.key);
    if (key >= 1 && key <= 4) {
      const optionIndex = key - 1;
      if (question.options[optionIndex]) {
        handleAnswer(question.options[optionIndex].id);
      }
    }
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [question, showResult, isLoading]);

  if (gameOver && gameStats) {
    return (
      <div>
        <Navbar />
        <GameOverModal stats={gameStats} />
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 px-4 pb-8">
      <Navbar />
      
      <div className="max-w-2xl mx-auto">
        <ScoreBoard score={score} streak={streak} />
        <ProgressBar current={currentQuestion} total={totalQuestions} />

        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-6">
            <CharacterCard imageUrl={question.imageUrl} isLoading={isLoading} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {question.options.map((option, index) => (
                <OptionButton
                  key={option.id}
                  option={{ ...option, displayId: index + 1 }}
                  onSelect={handleAnswer}
                  disabled={showResult}
                  showResult={showResult}
                  isCorrect={resultData?.correct && option.id === selectedOption}
                  isSelected={option.id === selectedOption}
                />
              ))}
            </div>

            {showResult && resultData && (
              <ResultPopup
                correct={resultData.correct}
                characterName={resultData.characterName}
                animeName={resultData.animeName}
              />
            )}

            <p className="text-center text-text-secondary text-sm mt-4">
              Press 1-4 to answer
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Game;
