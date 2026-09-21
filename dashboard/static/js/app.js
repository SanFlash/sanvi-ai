let taskId = null;
let recognition = null;
let listening = false;
let pollTimer = null;
let screenTimer = null;

const $ = id => document.getElementById(id);

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = $('language').value === 'hi-IN' ? 'hi-IN' : 'en-IN';
  u.rate = 1.0;
  window.speechSynthesis.speak(u);
}

function setVoiceState(text, active=false) {
  $('voiceState').textContent = text;
  $('mic').classList.toggle('listening', active);
  $('mic').textContent = active ? '⏹ Stop Listening' : '🎙️ Enable Microphone';
}

function setupRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    setVoiceState('Voice recognition is not supported by this browser');
    $('heard').textContent = 'Use current Chrome or Edge for microphone voice commands.';
    return null;
  }
  const r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.maxAlternatives = 1;
  r.onstart = () => { listening = true; setVoiceState('Listening for “Hey Sanvi”…', true); };
  r.onerror = e => {
    console.warn('Speech recognition:', e.error);
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      listening = false; setVoiceState('Microphone permission denied');
      speak('Microphone permission is required for voice commands.');
    }
  };
  r.onend = () => {
    if (listening) {
      try { r.lang = $('language').value; r.start(); } catch (_) {}
    }
  };
  r.onresult = event => {
    let finalText = '';
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript.trim();
      if (event.results[i].isFinal) finalText += ' ' + t;
      else interim += ' ' + t;
    }
    if (interim) $('heard').textContent = 'Heard: ' + interim;
    if (!finalText) return;
    finalText = finalText.trim();
    $('heard').textContent = 'Heard: ' + finalText;
    const lower = finalText.toLowerCase();
    const wake = ['hey sanvi', 'hey senvy', 'hey sanvee'];
    const match = wake.find(w => lower.includes(w));
    if (match) {
      const command = finalText.slice(lower.indexOf(match) + match.length).trim().replace(/^[,.:;-]+/, '').trim();
      if (command) runCommand(command, true);
      else speak('Yes sir, I am listening.');
      return;
    }
    if (listening && finalText.length > 2) runCommand(finalText, true);
  };
  return r;
}

async function toggleVoice() {
  if (listening) {
    listening = false;
    if (recognition) recognition.stop();
    setVoiceState('Microphone is off');
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    stream.getTracks().forEach(t => t.stop());
  } catch (e) {
    setVoiceState('Microphone permission is required');
    $('heard').textContent = 'Allow microphone access in the browser permission popup, then try again.';
    return;
  }
  recognition = recognition || setupRecognition();
  if (!recognition) return;
  recognition.lang = $('language').value;
  try { recognition.start(); } catch (_) {}
}

async function send() {
  const command = $('command').value.trim();
  if (command) await runCommand(command, false);
}

async function runCommand(command, fromVoice=false) {
  $('command').value = command;
  $('output').textContent = 'Planning: ' + command;
  $('status').textContent = 'BUSY';
  speak(fromVoice ? 'Okay sir, I am working on it.' : 'Starting the task.');
  try {
    const r = await fetch('/api/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command, source:fromVoice?'voice':'text'})});
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || d.error || 'Command request failed');
    taskId = d.task_id;
    startPolling();
    startScreenPolling();
  } catch (e) {
    $('status').textContent = 'ERROR';
    $('output').textContent = e.message;
    speak('I could not start that task.');
  }
}

function startPolling() {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (!taskId) return;
    const r = await fetch(`/api/tasks/${taskId}`);
    const d = await r.json();
    const current = d.current_step || 0;
    const total = d.total_steps || 0;
    $('progressText').textContent = `${current} / ${total}`;
    $('progress').style.width = total ? `${Math.min(100, current/total*100)}%` : '0%';
    $('taskText').textContent = d.current_description || d.status || 'Working';
    $('output').textContent = JSON.stringify(d, null, 2);
    if (['COMPLETED','FAILED','CANCELLED','WAITING_CONFIRMATION'].includes(d.status)) {
      clearInterval(pollTimer); pollTimer = null;
      $('status').textContent = d.status;
      speak(d.status === 'COMPLETED' ? 'Done sir. The task is complete.' : `Task ${d.status.toLowerCase()}.`);
    }
  }, 500);
}

function startScreenPolling() {
  clearInterval(screenTimer);
  const refresh = () => {
    if (!taskId) return;
    $('liveScreen').src = `/api/screenshot/latest?t=${Date.now()}`;
    $('screenState').textContent = 'LIVE';
  };
  refresh();
  screenTimer = setInterval(refresh, 1000);
}

async function action(path) {
  if (!taskId) return;
  await fetch(`/api/tasks/${taskId}/${path}`, {method:'POST'});
}
function stop(){action('stop')}
function pause(){action('pause')}
function resume(){action('resume')}

$('language').addEventListener('change', () => {
  if (recognition && listening) {
    recognition.lang = $('language').value;
    $('heard').textContent = 'Voice language changed to ' + $('language').selectedOptions[0].text;
  }
});
