import { useState } from 'react';

const CharacterCard = ({ imageUrl, isLoading }) => {
  const [imageError, setImageError] = useState(false);

  if (isLoading) {
    return (
      <div className="card aspect-square max-w-md mx-auto flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#F59E0B]"></div>
      </div>
    );
  }

  if (imageError) {
    return (
      <div className="card aspect-square max-w-md mx-auto flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">🖼️</div>
          <p className="text-secondary">Image not available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card aspect-square max-w-md mx-auto overflow-hidden">
      <img
        src={imageUrl}
        alt="Character"
        className="w-full h-full object-cover"
        onError={() => setImageError(true)}
      />
    </div>
  );
};

export default CharacterCard;
