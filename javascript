const SERVER_URL = window.location.origin;

const loginScreen = document.getElementById('loginScreen');
const gameScreen = document.getElementById('gameScreen');
const statusEl = document.getElementById('status');
const playerNameEl = document.getElementById('playerName');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let currentUser = null;
let players = {};
let keys = {};
let playerX = 100;
let playerY = 100;

function showStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.style.color = isError ? '#f87171' : '#facc15';
}

function showLogin() {
  loginScreen.classList.add('active');
  gameScreen.classList.remove('active');
}

function showGame() {
  loginScreen.classList.remove('active');
  gameScreen.classList.add('active');
}

async function registerUser() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (!username || !password) {
    showStatus('Please enter a username and password.', true);
    return;
  }

  try {
    const res = await fetch(`${SERVER_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();
    if (res.ok) {
      showStatus('Account created! You can now log in.');
    } else {
      showStatus(data.error || 'Registration failed.', true);
    }
  } catch (err) {
    showStatus('Server error. Start the backend first.', true);
  }
}

async function loginUser() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (!username || !password) {
    showStatus('Please enter a username and password.', true);
    return;
  }

  try {
    const res = await fetch(`${SERVER_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (res.ok) {
      currentUser = data.username;
      playerNameEl.textContent = `Player: ${currentUser}`;
      showStatus('');
      showGame();
      initGame();
    } else {
      showStatus(data.error || 'Login failed.', true);
    }
  } catch (err) {
    showStatus('Server error. Start the backend first.', true);
  }
}

async function logoutUser() {
  if (!currentUser) return;

  try {
    await fetch(`${SERVER_URL}/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: currentUser }),
    });
  } catch (err) {
    // ignore
  }

  currentUser = null;
  players = {};
  showLogin();
}

document.getElementById('registerBtn').addEventListener('click', registerUser);
document.getElementById('loginBtn').addEventListener('click', loginUser);
document.getElementById('logoutBtn').addEventListener('click', logoutUser);

document.addEventListener('keydown', (e) => {
  keys[e.key.toLowerCase()] = true;
});

document.addEventListener('keyup', (e) => {
  keys[e.key.toLowerCase()] = false;
});

function movePlayer() {
  const speed = 4;

  if (currentUser && keys['w']) playerY -= speed;
  if (currentUser && keys['s']) playerY += speed;
  if (currentUser && keys['a']) playerX -= speed;
  if (currentUser && keys['d']) playerX += speed;

  if (playerX < 20) playerX = 20;
  if (playerX > canvas.width - 20) playerX = canvas.width - 20;
  if (playerY < 20) playerY = 20;
  if (playerY > canvas.height - 20) playerY = canvas.height - 20;
}

async function updateServerPosition() {
  if (!currentUser) return;

  try {
    await fetch(`${SERVER_URL}/update_position`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: currentUser,
        x: Math.round(playerX),
        y: Math.round(playerY),
      }),
    });
  } catch (err) {
    // ignore
  }
}

async function refreshPlayers() {
  try {
    const res = await fetch(`${SERVER_URL}/players`);
    const data = await res.json();

    if (!data.players) return;

    const updated = {};
    for (const p of data.players) {
      if (p.username !== currentUser) {
        updated[p.username] = { x: p.x, y: p.y };
      }
    }
    players = updated;
  } catch (err) {
    // ignore
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#78c679';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (const name in players) {
    const p = players[name];
    ctx.fillStyle = '#1d4ed8';
    ctx.fillRect(p.x - 12, p.y - 12, 24, 24);
    ctx.fillStyle = '#fff';
    ctx.font = '12px Arial';
    ctx.fillText(name, p.x - 20, p.y - 18);
  }

  if (currentUser) {
    ctx.fillStyle = '#f97316';
    ctx.fillRect(playerX - 12, playerY - 12, 24, 24);
    ctx.fillStyle = '#fff';
    ctx.font = '12px Arial';
    ctx.fillText(currentUser, playerX - 18, playerY - 18);
  }

  requestAnimationFrame(draw);
}

function initGame() {
  playerX = 100;
  playerY = 100;
  players = {};

  setInterval(() => {
    movePlayer();
    updateServerPosition();
    refreshPlayers();
  }, 80);

  requestAnimationFrame(draw);
}

showLogin();