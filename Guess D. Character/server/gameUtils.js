const fs = require('fs');
const path = require('path');

// Load characters dataset
let characters = [];
try {
  const dataPath = path.join(__dirname, 'characters.json');
  const rawData = fs.readFileSync(dataPath, 'utf8');
  characters = JSON.parse(rawData);
  console.log(`Loaded ${characters.length} characters from dataset`);
} catch (error) {
  console.error('Error loading characters dataset:', error);
}

// Difficulty settings based on character index (sorted by favorites)
const DIFFICULTY_RANGES = {
  easy: { start: 0, end: 500 },      // Top 500 most popular
  medium: { start: 0, end: 1000 },   // Top 1000 most popular
  hard: { start: 0, end: characters.length }, // All characters
};

function getCharacterPool(difficulty) {
  const range = DIFFICULTY_RANGES[difficulty] || DIFFICULTY_RANGES.medium;
  return characters.slice(range.start, range.end);
}

function getRandomCharacter(pool, excludeIds = new Set()) {
  const available = pool.filter(char => !excludeIds.has(char.id));
  if (available.length === 0) return null;
  const randomIndex = Math.floor(Math.random() * available.length);
  return available[randomIndex];
}

function getRandomCharacters(pool, count, excludeIds = new Set()) {
  const selected = [];
  const tempExclude = new Set(excludeIds);
  
  while (selected.length < count) {
    const char = getRandomCharacter(pool, tempExclude);
    if (!char) break;
    selected.push(char);
    tempExclude.add(char.id);
  }
  
  return selected;
}

function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

function generateQuestion(session, pool) {
  const correctCharacter = getRandomCharacter(pool, session.usedCharacterIds);
  if (!correctCharacter) return null;

  const incorrectCharacters = getRandomCharacters(pool, 3, session.usedCharacterIds);
  if (incorrectCharacters.length < 3) return null;

  const allOptions = shuffleArray([correctCharacter, ...incorrectCharacters]);

  return {
    questionId: correctCharacter.id,
    imageUrl: correctCharacter.image_url,
    options: allOptions.map(char => ({
      id: char.id,
      name: char.character_en,
      anime: char.anime_en,
    })),
  };
}

module.exports = {
  getCharacterPool,
  generateQuestion,
  shuffleArray,
};
