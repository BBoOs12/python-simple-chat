const socket = io();

const form = document.getElementById('form');
const input = document.getElementById('message');
const messages = document.getElementById('messages');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  if (input.value) {
    socket.emit('send_message', { message: input.value });
    input.value = '';
  }
});

socket.on('receive_message', (data) => {
  const item = document.createElement('li');
  item.innerHTML = `<span class="time">[${data.timestamp}]</span> <strong>${data.username}:</strong> ${data.message}`;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
});
