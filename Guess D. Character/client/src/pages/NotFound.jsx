import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pt-20 px-4">
      <Navbar />
      
      <div className="max-w-md mx-auto text-center">
        <div className="text-6xl mb-4">
          🤔
        </div>
        <h1 className="text-4xl font-bold mb-4 text-text-primary">404</h1>
        <p className="text-lg text-text-secondary mb-8">Page not found</p>
        <button
          onClick={() => navigate('/')}
          className="btn-primary"
        >
          Go Home
        </button>
      </div>
    </div>
  );
};

export default NotFound;
