const ResultPopup = ({ correct, characterName, animeName }) => {
  return (
    <div className="card p-6 text-center max-w-sm mx-auto">
      <div className="text-4xl mb-3">
        {correct ? '✓' : '✗'}
      </div>
      <p className={`text-xl font-bold mb-4 ${correct ? 'text-green-400' : 'text-red-400'}`}>
        {correct ? 'Correct!' : 'Wrong!'}
      </p>
      <div className="text-left space-y-2">
        <p>
          <span className="text-text-secondary">Character:</span>{' '}
          <span className="font-semibold text-text-primary">{characterName}</span>
        </p>
        <p>
          <span className="text-text-secondary">Anime:</span>{' '}
          <span className="font-semibold text-text-primary">{animeName}</span>
        </p>
      </div>
    </div>
  );
};

export default ResultPopup;
