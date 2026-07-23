import { useNavigate } from 'react-router-dom';

const GameOverModal = ({ stats }) => {
  const navigate = useNavigate();

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="card p-8 max-w-md w-full text-center">
        <div className="text-5xl mb-4">
          🏆
        </div>
        <h2 className="text-3xl font-bold mb-6 text-text-primary">
          Game Over!
        </h2>
        
        <div className="space-y-4 mb-8">
          <div className="card p-4">
            <p className="text-text-secondary text-sm">Final Score</p>
            <p className="text-4xl font-bold text-accent">{stats.score}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-4">
              <p className="text-text-secondary text-sm">Accuracy</p>
              <p className="text-2xl font-bold text-text-primary">{stats.accuracy}%</p>
            </div>
            <div className="card p-4">
              <p className="text-text-secondary text-sm">Max Streak</p>
              <p className="text-2xl font-bold text-text-primary">{stats.maxStreak}</p>
            </div>
          </div>
          
          <div className="card p-4">
            <p className="text-text-secondary text-sm">Questions Answered</p>
            <p className="text-xl font-semibold text-text-primary">{stats.currentQuestion}</p>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => navigate('/')}
            className="btn-secondary flex-1"
          >
            Back to Home
          </button>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary flex-1"
          >
            Play Again
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameOverModal;
