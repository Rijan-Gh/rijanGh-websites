# Guess the Anime Character

A full-stack web application where players test their anime knowledge by guessing popular anime characters from their images.

## Features

- **2000+ Anime Characters**: Dataset sourced from AniList API
- **Multiple Difficulty Levels**: Easy, Medium, and Hard modes
- **Flexible Game Modes**: Choose 10, 20, or endless questions
- **Real-time Scoring**: Track score, streak, and accuracy
- **Modern UI**: Dark theme with purple, blue, and pink gradient accents
- **Smooth Animations**: Powered by Framer Motion
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Keyboard Support**: Press 1-4 to quickly answer questions

## Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- Framer Motion
- React Router
- Axios

### Backend
- Node.js
- Express.js
- CORS

## Project Structure

```
guess-the-anime/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   ├── utils/          # Utility functions
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
└── server/                 # Express backend
    ├── server.js           # Main server file
    ├── sessionManager.js   # Session management
    ├── gameUtils.js        # Game logic utilities
    ├── characters.json     # Character dataset
    └── package.json
```

## Installation

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Setup

1. **Clone the repository**
   ```bash
   cd guess-the-anime
   ```

2. **Install server dependencies**
   ```bash
   cd server
   npm install
   ```

3. **Install client dependencies**
   ```bash
   cd ../client
   npm install
   ```

## Running the Application

### Start the Backend Server

In the `server` directory:
```bash
npm start
```

The server will run on `http://localhost:3001`

### Start the Frontend Development Server

In the `client` directory:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

### Quick Start

Alternatively, you can run both servers simultaneously by opening two terminal windows:

**Terminal 1 (Backend):**
```bash
cd server
npm start
```

**Terminal 2 (Frontend):**
```bash
cd client
npm run dev
```

Then open `http://localhost:3000` in your browser.

## API Endpoints

### POST `/api/game/start`
Start a new game session.

**Request Body:**
```json
{
  "difficulty": "medium",
  "totalQuestions": 10
}
```

**Response:**
```json
{
  "sessionId": "uuid",
  "question": {
    "questionId": 45627,
    "imageUrl": "https://...",
    "options": [
      { "id": 1, "name": "Levi" },
      { "id": 2, "name": "Eren" },
      { "id": 3, "name": "Mikasa" },
      { "id": 4, "name": "Armin" }
    ]
  },
  "totalQuestions": 10,
  "currentQuestion": 1
}
```

### GET `/api/game/question/:sessionId`
Get the next question for a session.

**Response:**
```json
{
  "question": { ... },
  "currentQuestion": 2,
  "totalQuestions": 10
}
```

### POST `/api/game/answer`
Submit an answer for a question.

**Request Body:**
```json
{
  "sessionId": "uuid",
  "questionId": 45627,
  "selectedId": 1
}
```

**Response:**
```json
{
  "correct": true,
  "correctAnswer": {
    "id": 45627,
    "name": "Levi",
    "anime": "Attack on Titan"
  },
  "score": 10,
  "streak": 1,
  "gameFinished": false
}
```

### GET `/api/game/stats/:sessionId`
Get session statistics.

### DELETE `/api/game/session/:sessionId`
Delete a game session.

## Game Mechanics

### Difficulty Levels
- **Easy**: Top 500 most popular characters
- **Medium**: Top 1000 most popular characters
- **Hard**: All 2000+ characters

### Scoring
- Base score: 10 points per correct answer
- Streak bonus: +2 points for each consecutive correct answer
- Streak resets on incorrect answer

### Session Management
- Sessions are stored in server memory
- Inactive sessions are automatically deleted after 30 minutes
- Each session tracks used characters to prevent repeats

## Building for Production

### Build the Frontend
```bash
cd client
npm run build
```

The built files will be in the `client/dist` directory.

### Serve with Production Backend
1. Build the frontend as shown above
2. Update the backend to serve static files from `client/dist`
3. Run the backend with `npm start`

## Troubleshooting

### Port Already in Use
If you get a "port already in use" error, you can:
- Change the port in `server/server.js` (line: `const PORT = process.env.PORT || 3001`)
- Change the port in `client/vite.config.js` (line: `port: 3000`)

### CORS Errors
The backend is configured to allow CORS. If you encounter CORS issues, ensure:
- The backend is running on port 3001
- The frontend proxy is configured correctly in `vite.config.js`

### Image Loading Issues
If character images fail to load:
- Check your internet connection (images are served from AniList CDN)
- The app includes fallback placeholders for broken images

## License

ISC

## Acknowledgments

- Character data sourced from [AniList](https://anilist.co/)
- Built with React, Vite, and Express
- UI styled with Tailwind CSS
- Animations powered by Framer Motion
