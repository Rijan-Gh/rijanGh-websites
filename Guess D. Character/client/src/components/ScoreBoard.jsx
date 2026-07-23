const ScoreBoard = ({ score, streak }) => {
  return (
    <div className="flex gap-4 justify-center mb-6">
      <div className="card px-5 py-3 flex items-center gap-3">
        <span className="text-xl">⭐</span>
        <div>
          <p className="text-xs text-text-secondary">Score</p>
          <p className="text-lg font-bold text-text-primary">{score}</p>
        </div>
      </div>
      <div className="card px-5 py-3 flex items-center gap-3">
        <span className="text-xl">🔥</span>
        <div>
          <p className="text-xs text-text-secondary">Streak</p>
          <p className="text-lg font-bold text-text-primary">{streak}</p>
        </div>
      </div>
    </div>
  );
};

export default ScoreBoard;
