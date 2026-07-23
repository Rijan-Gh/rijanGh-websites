const ProgressBar = ({ current, total }) => {
  const percentage = total === 'endless' ? 100 : (current / total) * 100;

  return (
    <div className="w-full max-w-md mx-auto mb-6">
      <div className="flex justify-between text-sm text-text-secondary mb-2">
        <span>Question {current}</span>
        <span>{total === 'endless' ? 'Endless' : `of ${total}`}</span>
      </div>
      <div className="h-2 bg-surfaceHover rounded-full overflow-hidden">
        <div
          style={{ width: `${percentage}%` }}
          className="h-full bg-accent rounded-full transition-all duration-300"
        />
      </div>
    </div>
  );
};

export default ProgressBar;
