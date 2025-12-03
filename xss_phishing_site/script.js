const form = document.getElementById('commentForm');
const nameInput = document.getElementById('name');
const messageInput = document.getElementById('message');
const feedList = document.getElementById('feedList');
const payloadButton = document.getElementById('payloadButton');
const runScenario = document.getElementById('runScenario');
const phishOverlay = document.getElementById('phishOverlay');
const phishMessage = document.getElementById('phishMessage');

const attackPayload = '<img src="x" alt="" onerror="openPhish(\'Portal timed out — log back in to keep editing\')">';

const escapeHtml = (input = '') =>
    input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

const postComment = (author, message, { malicious = false } = {}) => {
    const li = document.createElement('li');
    if (malicious) {
        li.classList.add('malicious');
    }
    const safeAuthor = escapeHtml(author || 'Anonymous');
    li.innerHTML = `<span class="author">${safeAuthor}</span><p>${message || '<em>(empty message)</em>'}</p>`;
    feedList.prepend(li);
};

form?.addEventListener('submit', (event) => {
    event.preventDefault();
    const author = nameInput.value.trim() || 'Anonymous';
    const message = messageInput.value.trim() || '(no message)';
    postComment(author, message);
    form.reset();
    nameInput.focus();
});

payloadButton?.addEventListener('click', () => {
    messageInput.value = attackPayload;
    messageInput.focus();
});

runScenario?.addEventListener('click', () => {
    postComment('Security_Update', attackPayload, { malicious: true });
    setTimeout(() => openPhish('Security update: re-authenticate to apply grades.'), 600);
});

window.openPhish = (message) => {
    phishMessage.textContent = message || 'Please verify your credentials.';
    phishOverlay.classList.add('show');
};

const closePhish = () => phishOverlay.classList.remove('show');

document.querySelectorAll('[data-close]').forEach((btn) => {
    btn.addEventListener('click', closePhish);
});

phishOverlay?.addEventListener('click', (event) => {
    if (event.target === phishOverlay) {
        closePhish();
    }
});
