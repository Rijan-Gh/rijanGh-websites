const OptionButton = ({ option, onSelect, disabled, showResult, isCorrect, isSelected }) => {
  const getButtonClass = () => {
    if (showResult) {
      if (isCorrect) return 'option-correct';
      if (isSelected && !isCorrect) return 'option-wrong';
    }
    return '';
  };

  return (
    <button
      onClick={() => !disabled && !showResult && onSelect(option.id)}
      disabled={disabled || showResult}
      className={`option-btn ${getButtonClass()}`}
    >
      <div className="flex items-start gap-3">
        <span className="w-8 h-8 rounded-full bg-surfaceHover flex items-center justify-center text-sm flex-shrink-0 mt-1 text-text-secondary">
          {option.displayId || option.id}
        </span>
        <div className="flex-1">
          <div className="font-medium text-text-primary">{option.name}</div>
          {option.anime && (
            <div className="text-sm text-text-secondary">{option.anime}</div>
          )}
        </div>
        {showResult && isCorrect && (
          <span className="ml-auto text-green-400 flex-shrink-0">
            ✓
          </span>
        )}
        {showResult && isSelected && !isCorrect && (
          <span className="ml-auto text-red-400 flex-shrink-0">
            ✗
          </span>
        )}
      </div>
    </button>
  );
};

export default OptionButton;
