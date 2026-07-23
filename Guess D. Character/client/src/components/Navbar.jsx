import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="card fixed top-0 left-0 right-0 z-50 mx-4 mt-4 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <span className="text-xl">🎮</span>
          <span className="text-lg font-bold text-primary">
          Guess D. Anime Character
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="text-secondary hover:text-primary transition-colors"
          >
            Home
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
