const output = document.getElementById('output');
const clearButton = document.getElementById('clear-output');

function writeOutput(value, isError = false) {
  output.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  output.style.color = isError ? '#fecdd3' : '#dbeafe';
}

async function sendRequest(url, options) {
  const response = await fetch(url, options);
  const text = await response.text();
  let parsed;

  try {
    parsed = text ? JSON.parse(text) : {};
  } catch {
    parsed = text;
  }

  if (!response.ok) {
    const message = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
    throw new Error(`HTTP ${response.status}\n${message}`);
  }

  return parsed;
}

document.getElementById('signup-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await sendRequest('/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    writeOutput(data);
  } catch (error) {
    writeOutput(error.message, true);
  }
});

document.getElementById('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await sendRequest('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    writeOutput(data);
  } catch (error) {
    writeOutput(error.message, true);
  }
});

document.getElementById('user-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const userId = formData.get('user_id');

  try {
    const data = await sendRequest(`/users/${userId}`);
    writeOutput(data);
  } catch (error) {
    writeOutput(error.message, true);
  }
});

clearButton.addEventListener('click', () => {
  writeOutput('Use one of the forms above to test the API.');
});