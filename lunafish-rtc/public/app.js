const output = document.getElementById('output');
const button = document.getElementById('loadCaps');

const ws = new WebSocket(`ws://${location.host}`);

ws.onopen = () => {
  output.textContent = 'WebSocket connected\n';
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  output.textContent += JSON.stringify(msg, null, 2) + '\n';
};

button.onclick = () => {
  ws.send(JSON.stringify({ action: 'getRouterRtpCapabilities' }));
};
