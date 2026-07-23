import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import Navbar from '../components/Navbar';

const Home = () => {
  const navigate = useNavigate();
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(10);

  const startGame = () => {
    navigate('/game', { state: { difficulty, questionCount } });
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <Navbar />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="max-w-2xl mx-auto"
      >
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-3 text-primary">
          Guess D. Anime Character
          </h1>
          <p className="text-lg text-secondary">
            Test your anime knowledge with 2000+ characters
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          className="card p-6 space-y-6"
        >
          <div>
            <label className="block text-sm font-semibold mb-3 text-secondary uppercase tracking-wide">
              Difficulty
            </label>
            <div className="grid grid-cols-3 gap-3">
              {['easy', 'medium', 'hard'].map((level) => (
                <button
                  key={level}
                  onClick={() => setDifficulty(level)}
                  className={`p-4 rounded-card border-2 transition-colors duration-200 ${
                    difficulty === level
                      ? 'border-[#F59E0B] bg-[rgba(245,158,11,0.1)]'
                      : 'border-custom hover:border-[rgba(245,158,11,0.5)]'
                  }`}
                >
                  <div className="capitalize font-semibold text-primary">{level}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-3 text-secondary uppercase tracking-wide">
              Questions
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[10, 20, 'endless'].map((count) => (
                <button
                  key={count}
                  onClick={() => setQuestionCount(count)}
                  className={`p-4 rounded-card border-2 transition-colors duration-200 ${
                    questionCount === count
                      ? 'border-[#F59E0B] bg-[rgba(245,158,11,0.1)]'
                      : 'border-custom hover:border-[rgba(245,158,11,0.5)]'
                  }`}
                >
                  <div className="text-xl font-semibold text-primary">
                    {count === 'endless' ? '∞' : count}
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    {count === 'endless' ? 'Endless' : 'Questions'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={startGame}
            className="btn-primary w-full text-lg py-3"
          >
            Start Game
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-6 text-center text-secondary text-sm"
        >
          <p>Powered by AniList API</p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Home;
