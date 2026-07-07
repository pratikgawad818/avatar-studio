'use strict';
/* ── Avatar Studio — app.js (HeyGen-inspired) ── */

const S = {
  selectedVoiceId: null, selectedAvatarId: null, selectedBgFile: null,
  position: 'center', subStyle: 'netflix', subtitles: true,
  resolution: '1280x720', voiceSpeed: 1.0, avatarScale: 0.55,
  lipSyncQuality: 'enhanced', whisperModel: 'base', useWhisper: true,
  lowerName: '', lowerTitle: '',
  voiceMode: 'fast', voiceEdge: 'en-US-GuyNeural',
  aspectRatio: '16:9',
  mediaRecorder: null, recordedChunks: [], recordingBlob: null,
  recordingTimer: null, recordingSeconds: 0, analyser: null, animFrame: null,
};

const $ = id => document.getElementById(id);
const $$ = s => document.querySelectorAll(s);

document.addEventListener('DOMContentLoaded', () => {
  initNav(); initRecorder(); initDropZones(); initScript();
  initSettings(); initGenerate(); initResultActions();
  loadVoices(); loadAvatars(); loadStudioPickers();
});

// ── Nav ───────────────────────────────────────────────────────────────────
function initNav() { $$('.snav-btn').forEach(b => b.addEventListener('click', () => switchView(b.dataset.view))); }
function switchView(name) {
  $$('.snav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === name));
  $$('.view').forEach(v => v.classList.toggle('active', v.id === `view-${name}`));
  if (name === 'studio') loadStudioPickers();
  if (name === 'library') loadLibrary();
}

// ── Studio pickers ────────────────────────────────────────────────────────
async function loadStudioPickers() {
  const [vr, ar, br] = await Promise.all([
    fetch('/voices/list').then(r => r.json()),
    fetch('/avatars/list').then(r => r.json()),
    fetch('/backgrounds/list').then(r => r.json()),
  ]);
  renderVoicePicker(vr.voices || []);
  renderAvatarPicker(ar.avatars || []);
  renderBgGallery(br.backgrounds || []);
}

function renderAvatarPicker(avatars) {
  const el = $('studio-avatar-picker');
  if (!avatars.length) { el.innerHTML = '<div class="picker-empty">No avatars — upload a photo first</div>'; return; }
  el.innerHTML = avatars.map(a => `
    <div class="picker-card ${S.selectedAvatarId === a.id ? 'selected' : ''}" onclick="pickAvatar('${a.id}','${a.url}')">
      <img src="${a.url}" alt="${a.name}"/>${a.name}
    </div>`).join('');
}
function renderVoicePicker(voices) {
  const el = $('studio-voice-picker');
  if (!voices.length) { el.innerHTML = '<div class="picker-empty">No clones — go to Voice Lab</div>'; return; }
  el.innerHTML = voices.map(v => `
    <div class="picker-card ${S.selectedVoiceId === v.id ? 'selected' : ''}" onclick="pickVoice('${v.id}')">
      <span>🎵</span>${v.name}
    </div>`).join('');
}
function renderBgGallery(bgs) {
  const el = $('bg-gallery');
  if (!bgs.length) { el.innerHTML = ''; return; }
  el.innerHTML = bgs.map(bg => `
    <div class="bg-gallery-item ${S.selectedBgFile === bg.name ? 'selected' : ''}"
         onclick="pickBg('${bg.name}','${bg.url}')">
      <img src="${bg.url}" alt="${bg.name}" loading="lazy"/>
      ${bg.type === 'video' ? '<span class="bg-type-badge">▶</span>' : ''}
    </div>`).join('');
}

function pickAvatar(id, url) {
  S.selectedAvatarId = id;
  loadStudioPickers();
  // Update canvas preview
  const img = $('canvas-avatar-img');
  img.src = url; img.classList.remove('hidden');
  $('canvas-placeholder').classList.add('hidden');
}
function pickVoice(id) { S.selectedVoiceId = id; loadStudioPickers(); }
function pickBg(name, url) {
  S.selectedBgFile = name;
  $$('.bg-gallery-item').forEach(c => c.classList.remove('selected'));
  event.currentTarget.classList.add('selected');
  const bgImg = $('canvas-bg-img');
  bgImg.src = url; bgImg.classList.remove('hidden');
}

// ── Script ────────────────────────────────────────────────────────────────
function initScript() {
  $('studio-script').addEventListener('input', updateScriptInfo);
  $('btn-clear-script').addEventListener('click', () => { $('studio-script').value = ''; updateScriptInfo(); });
  $('btn-sample-script').addEventListener('click', () => {
    $('studio-script').value = 'Hi! I\'m your AI avatar running locally on your Mac. No cloud needed.';
    updateScriptInfo();
  });
}
function updateScriptInfo() {
  const words = ($('studio-script').value.trim().split(/\s+/).filter(Boolean)).length;
  const mode = S.voiceMode;
  const est = mode === 'fast' ? Math.max(1, Math.round((words * 0.3 + words * 2.5 + 30) / 60))
                               : Math.max(2, Math.round((words * 4 + words * 2.5 + 30) / 60));
  $('studio-word-count').textContent = words ? `${words} words` : '0 words';
  $('est-badge').textContent = `~${est} min`;
  if (words > 100) $('est-badge').style.color = 'var(--yellow)';
  else $('est-badge').style.color = '';
}

// ── Settings ──────────────────────────────────────────────────────────────
function initSettings() {
  initSegGroup('voice-mode-group', v => {
    S.voiceMode = v;
    $('voice-fast-panel').classList.toggle('hidden', v !== 'fast');
    $('voice-clone-panel').classList.toggle('hidden', v !== 'clone');
    updateScriptInfo();
  });
  $('edge-voice').addEventListener('change', e => S.voiceEdge = e.target.value);
  $('sel-ratio').addEventListener('change', e => {
    S.aspectRatio = e.target.value;
    // Update canvas preview aspect ratio
    const canvas = $('canvas-preview');
    const ratios = {'16:9':'16/9','9:16':'9/16','1:1':'1/1','4:5':'4/5','4:3':'4/3'};
    canvas.style.aspectRatio = ratios[e.target.value] || '16/9';
  });
  $('sel-position').addEventListener('change', e => S.position = e.target.value);
  $('sel-substyle').addEventListener('change', e => {
    S.subStyle = e.target.value;
    S.subtitles = e.target.value !== 'none';
  });
  $('sel-resolution').addEventListener('change', e => {
    S.resolution = e.target.value;
    $('canvas-res').textContent = e.target.value.replace('x', '×');
  });
  $('voice-speed').addEventListener('input', e => S.voiceSpeed = parseFloat(e.target.value));
  $('avatar-scale').addEventListener('input', e => S.avatarScale = parseFloat(e.target.value));
}
function initSegGroup(id, cb) {
  const g = $(id); if (!g) return;
  g.querySelectorAll('.seg').forEach(btn => {
    btn.addEventListener('click', () => {
      g.querySelectorAll('.seg').forEach(b => b.classList.remove('active'));
      btn.classList.add('active'); cb(btn.dataset.value);
    });
  });
}

// ── Generate ──────────────────────────────────────────────────────────────
function initGenerate() { $('btn-generate').addEventListener('click', generate); }

async function generate() {
  const script = $('studio-script').value.trim();
  if (!script) { toast('Write a script first', 'warn'); return; }
  if (!S.selectedAvatarId) { toast('Select an avatar', 'warn'); return; }
  if (S.voiceMode === 'clone' && !S.selectedVoiceId) { toast('Select a voice clone', 'warn'); return; }

  const fd = new FormData();
  fd.append('script', script);
  fd.append('voice_id', S.selectedVoiceId || 'none');
  fd.append('avatar_id', S.selectedAvatarId);
  fd.append('voice_transcript', ($('voice-transcript')?.value) || '');
  fd.append('voice_speed', S.voiceSpeed);
  fd.append('voice_mode', S.voiceMode);
  fd.append('voice_edge', S.voiceEdge);
  fd.append('position', S.position);
  fd.append('avatar_scale', S.avatarScale);
  fd.append('resolution', S.resolution);
  fd.append('subtitles', S.subtitles);
  fd.append('sub_style', S.subStyle);
  fd.append('use_whisper', S.useWhisper);
  fd.append('whisper_model', S.whisperModel);
  fd.append('lipsync_quality', S.lipSyncQuality);
  fd.append('lower_name', S.lowerName);
  fd.append('lower_title', S.lowerTitle);
  fd.append('background_file', S.selectedBgFile || '');
  fd.append('aspect_ratio', S.aspectRatio);

  try {
    const res = await fetch('/generate', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.error) { toast(data.error, 'err'); return; }
    showProgress(true); startSSE(); setGenerating(true);
  } catch (e) { toast('Failed: ' + e.message, 'err'); }
}

// ── SSE ───────────────────────────────────────────────────────────────────
let _sse = null, _elapsedInterval = null, _startedAt = null;

function startSSE() {
  if (_sse) _sse.close();
  _startedAt = Date.now(); _startElapsedTimer();
  _sse = new EventSource('/progress');
  _sse.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.heartbeat) return;
    if (d.started_at) _startedAt = new Date(d.started_at).getTime();
    updateProgressUI(d);
  };
  _sse.onerror = () => { _sse.close(); pollStatus(); };
}
function _startElapsedTimer() {
  clearInterval(_elapsedInterval);
  _elapsedInterval = setInterval(() => {
    if (!_startedAt) return;
    const sec = Math.floor((Date.now() - _startedAt) / 1000);
    const el = $('prog-elapsed');
    if (el) el.textContent = `${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}`;
  }, 1000);
}
function _stopElapsedTimer() { clearInterval(_elapsedInterval); }

function updateProgressUI(d) {
  const pct = d.progress || 0;
  $('prog-fill').style.width = pct + '%';
  $('prog-pct').textContent = pct + '%';
  $('prog-step').textContent = d.step || '';
  if (d.log) appendLog(d.log);
  updateTimeline(d.steps_done || [], pct);
  updateSidebarStatus(d.status);
  if (d.status === 'done' && d.output_file) { _sse?.close(); _stopElapsedTimer(); showResult(d.output_file); }
  else if (d.status === 'error') { _sse?.close(); _stopElapsedTimer(); showError(d.error || 'Unknown error'); }
}
function updateTimeline(done, pct) {
  const map = {voice:'pt-voice',lipsync:'pt-lipsync',background:'pt-background',subtitles:'pt-subtitles',done:'pt-done'};
  const active = pct<28?'voice':pct<70?'lipsync':pct<85?'background':pct<98?'subtitles':'done';
  Object.entries(map).forEach(([k,id])=>{
    const el=$(id);if(!el)return; el.classList.remove('active','done');
    if(done.includes(k))el.classList.add('done'); else if(k===active)el.classList.add('active');
  });
}
function appendLog(msg) {
  const log=$('prog-log');const p=document.createElement('p');
  p.className='log-line '+(msg.startsWith('ERROR')?'log-err':msg.includes('✓')?'log-ok':'');
  p.textContent=msg;log.appendChild(p);log.scrollTop=log.scrollHeight;
  while(log.children.length>50)log.removeChild(log.firstChild);
}
function pollStatus() {
  const id=setInterval(async()=>{
    try{const d=await fetch('/status').then(r=>r.json());
      if(d.status==='done'){clearInterval(id);showResult(d.output_file);}
      else if(d.status==='error'){clearInterval(id);showError(d.error);}
    }catch{clearInterval(id);}
  },3000);
}

// ── Result/Error ──────────────────────────────────────────────────────────
function showProgress(on){$('progress-overlay').classList.toggle('hidden',!on);$('result-overlay').classList.add('hidden');$('error-overlay').classList.add('hidden');}
function showResult(url){setGenerating(false);$('progress-overlay').classList.add('hidden');$('result-overlay').classList.remove('hidden');
  $('result-video').src=url;$('result-video').load();$('btn-download').href=url;$('btn-download').download=url.split('/').pop();
  updateSidebarStatus('done');toast('Video ready!','ok');}
function showError(msg){setGenerating(false);$('progress-overlay').classList.add('hidden');$('error-overlay').classList.remove('hidden');
  $('error-msg').textContent=msg;updateSidebarStatus('error');toast('Failed','err');}
function setGenerating(on){$('btn-generate').disabled=on;$('gen-label').textContent=on?'Generating...':'Generate Video';}
function updateSidebarStatus(s){$('status-dot').className='status-dot '+s;
  $('status-label').textContent=s==='running'?'Generating...':s==='done'?'Done ✓':s==='error'?'Error':'Ready';}
function initResultActions(){
  $('btn-new-video').addEventListener('click',()=>{$('result-overlay').classList.add('hidden');resetProgress();});
  $('btn-retry').addEventListener('click',()=>{$('error-overlay').classList.add('hidden');resetProgress();});
}
function resetProgress(){$('prog-fill').style.width='0%';$('prog-pct').textContent='0%';$('prog-step').textContent='Starting...';
  $('prog-log').innerHTML='<p class="log-line">Initialising...</p>';
  const el=$('prog-elapsed');if(el)el.textContent='00:00';_stopElapsedTimer();
  ['pt-voice','pt-lipsync','pt-background','pt-subtitles','pt-done'].forEach(id=>{const e=$(id);if(e)e.classList.remove('active','done');});
  setGenerating(false);updateSidebarStatus('idle');}

async function cancelGeneration(){
  if(!confirm('Cancel?'))return;
  try{await fetch('/cancel',{method:'POST'});_sse?.close();_stopElapsedTimer();
    showProgress(false);setGenerating(false);updateSidebarStatus('idle');toast('Cancelled','warn');
  }catch(e){toast('Cancel failed','err');}
}

// ── Drop zones ────────────────────────────────────────────────────────────
function initDropZones(){
  setupDrop('drop-voice-upload','input-voice-upload',async f=>{
    const name=$('upload-voice-name').value.trim()||f.name.replace(/\.[^.]+$/,'');
    const fd=new FormData();fd.append('file',f);fd.append('name',name);
    const r=await fetch('/voices/upload',{method:'POST',body:fd});const d=await r.json();
    if(d.error){toast(d.error,'err');return;}toast(`Voice "${d.voice.name}" saved`,'ok');loadVoices();loadStudioPickers();
  });
  setupDrop('drop-avatar','input-avatar',async f=>{
    const name=$('avatar-name-input').value.trim()||'My Avatar';
    const fd=new FormData();fd.append('file',f);fd.append('name',name);
    const r=await fetch('/avatars/upload',{method:'POST',body:fd});const d=await r.json();
    if(d.error){toast(d.error,'err');return;}toast(`Avatar added`,'ok');loadAvatars();loadStudioPickers();
  });
  setupDrop('drop-bg','input-bg',async f=>{
    const fd=new FormData();fd.append('file',f);
    const r=await fetch('/backgrounds/upload',{method:'POST',body:fd});const d=await r.json();
    if(d.error){toast(d.error,'err');return;}S.selectedBgFile=d.file;
    toast('Background uploaded','ok');loadStudioPickers();
  });
}
function setupDrop(zoneId,inputId,handler){
  const zone=$(zoneId),input=$(inputId);if(!zone||!input)return;
  zone.addEventListener('click',()=>input.click());
  input.addEventListener('change',()=>{if(input.files[0])handler(input.files[0]);});
  zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('over');});
  zone.addEventListener('dragleave',()=>zone.classList.remove('over'));
  zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('over');if(e.dataTransfer.files[0])handler(e.dataTransfer.files[0]);});
}

// ── Voice/Avatar lists ────────────────────────────────────────────────────
async function loadVoices(){const r=await fetch('/voices/list');const d=await r.json();renderVoiceGrid(d.voices||[]);}
function renderVoiceGrid(voices){
  const grid=$('voice-grid');
  if(!voices.length){grid.innerHTML='<div class="empty-state"><span>🎙️</span><p>No voices yet</p></div>';return;}
  grid.innerHTML=voices.map(v=>`<div class="voice-card" id="vc-${v.id}">
    <div class="vc-header"><span class="vc-icon">🎵</span><span class="vc-name">${v.name}</span><span class="vc-dur">${v.duration||'?'}s</span></div>
    <div class="vc-audio"><audio controls src="${v.url}"></audio></div>
    <div class="vc-actions"><button class="btn-use" onclick="selectVoice('${v.id}','${v.name}')">✓ Use</button>
    <button class="btn-del" onclick="deleteVoice('${v.id}')">🗑</button></div></div>`).join('');
}
function selectVoice(id,name){S.selectedVoiceId=id;$$('.voice-card').forEach(c=>c.classList.remove('selected'));
  const c=$(`vc-${id}`);if(c)c.classList.add('selected');toast(`Voice "${name}" selected`,'ok');loadStudioPickers();}
async function deleteVoice(id){if(!confirm('Delete?'))return;await fetch(`/voices/${id}`,{method:'DELETE'});
  if(S.selectedVoiceId===id)S.selectedVoiceId=null;loadVoices();loadStudioPickers();}
$('btn-refresh-voices').addEventListener('click',loadVoices);

async function loadAvatars(){const r=await fetch('/avatars/list');const d=await r.json();renderAvatarGrid(d.avatars||[]);}
function renderAvatarGrid(avatars){
  const grid=$('avatar-grid');
  if(!avatars.length){grid.innerHTML='<div class="empty-state"><span>🧑‍💼</span><p>No avatars yet</p></div>';return;}
  grid.innerHTML=avatars.map(a=>`<div class="avatar-card" id="av-${a.id}" onclick="selectAvatar('${a.id}','${a.name}','${a.url}')">
    <img src="${a.url}" alt="${a.name}" loading="lazy"/><div class="avatar-check">✓</div>
    <div class="avatar-card-info"><span class="avatar-card-name">${a.name}</span>
    <button class="avatar-del" onclick="event.stopPropagation();deleteAvatar('${a.id}')">🗑</button></div></div>`).join('');
  if(S.selectedAvatarId){const el=$(`av-${S.selectedAvatarId}`);if(el)el.classList.add('selected');}
}
function selectAvatar(id,name,url){S.selectedAvatarId=id;$$('.avatar-card').forEach(c=>c.classList.remove('selected'));
  const c=$(`av-${id}`);if(c)c.classList.add('selected');toast(`Avatar "${name}" selected`,'ok');loadStudioPickers();
  pickAvatar(id,url);}
async function deleteAvatar(id){if(!confirm('Delete?'))return;await fetch(`/avatars/${id}`,{method:'DELETE'});
  if(S.selectedAvatarId===id)S.selectedAvatarId=null;loadAvatars();loadStudioPickers();}
$('btn-refresh-avatars').addEventListener('click',loadAvatars);

// ── Library ───────────────────────────────────────────────────────────────
async function loadLibrary(){const r=await fetch('/videos');const d=await r.json();const grid=$('library-grid');const vids=d.videos||[];
  if(!vids.length){grid.innerHTML='<div class="empty-state full"><span>🎬</span><p>No videos yet</p></div>';return;}
  grid.innerHTML=vids.map(v=>`<div class="lib-card"><video src="${v.url}" muted playsinline preload="metadata"
    onmouseenter="this.play()" onmouseleave="this.pause();this.currentTime=0"></video>
    <div class="lib-card-info"><p class="lib-card-name">${v.filename}</p>
    <div class="lib-card-meta"><span>${v.created}</span><span>${v.size_mb}MB</span></div></div>
    <div class="lib-card-actions"><a href="${v.url}" download="${v.filename}">⬇ Download</a>
    <button onclick="deleteLibVideo('${v.filename}')">🗑</button></div></div>`).join('');}
async function deleteLibVideo(name){if(!confirm(`Delete ${name}?`))return;await fetch(`/videos/${name}`,{method:'DELETE'});loadLibrary();}
$('btn-refresh-lib').addEventListener('click',loadLibrary);

// ── Recorder ──────────────────────────────────────────────────────────────
function initRecorder(){
  $('btn-record').addEventListener('click',startRecording);$('btn-stop').addEventListener('click',stopRecording);
  $('btn-playback').addEventListener('click',playback);$('btn-save-recording').addEventListener('click',saveRecording);
  $('btn-discard-recording').addEventListener('click',discardRecording);
}
async function startRecording(){try{
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});S.recordedChunks=[];S.recordingBlob=null;
  const ctx=new AudioContext();const src=ctx.createMediaStreamSource(stream);S.analyser=ctx.createAnalyser();S.analyser.fftSize=256;src.connect(S.analyser);drawWaveform();
  S.mediaRecorder=new MediaRecorder(stream,{mimeType:'audio/webm'});
  S.mediaRecorder.ondataavailable=e=>{if(e.data.size>0)S.recordedChunks.push(e.data);};
  S.mediaRecorder.onstop=onRecorderStop;S.mediaRecorder.start(100);
  S.recordingSeconds=0;updateTimer();S.recordingTimer=setInterval(()=>{S.recordingSeconds++;updateTimer();},1000);
  $('btn-record').classList.add('hidden');$('btn-stop').classList.remove('hidden');$('waveform-idle').style.display='none';
}catch(e){toast('Mic denied: '+e.message,'err');}}
function stopRecording(){if(S.mediaRecorder&&S.mediaRecorder.state!=='inactive'){S.mediaRecorder.stop();S.mediaRecorder.stream.getTracks().forEach(t=>t.stop());}
  clearInterval(S.recordingTimer);cancelAnimationFrame(S.animFrame);}
function onRecorderStop(){S.recordingBlob=new Blob(S.recordedChunks,{type:'audio/webm'});$('playback-audio').src=URL.createObjectURL(S.recordingBlob);
  $('btn-stop').classList.add('hidden');$('btn-playback').classList.remove('hidden');$('btn-save-recording').classList.remove('hidden');$('btn-discard-recording').classList.remove('hidden');}
function playback(){const a=$('playback-audio');if(a.paused){a.play();$('btn-playback').textContent='⏸ Pause';}else{a.pause();$('btn-playback').textContent='▶ Play';}}
async function saveRecording(){if(!S.recordingBlob)return;const name=$('voice-name-input').value.trim()||'My Voice';
  const fd=new FormData();fd.append('audio',S.recordingBlob,'recording.webm');fd.append('name',name);
  try{const r=await fetch('/voices/save',{method:'POST',body:fd});const d=await r.json();
    if(d.error){toast(d.error,'err');return;}toast(`Voice "${name}" saved!`,'ok');discardRecording();loadVoices();loadStudioPickers();
  }catch(e){toast('Save failed','err');}}
function discardRecording(){S.recordingBlob=null;S.recordedChunks=[];
  $('btn-record').classList.remove('hidden');$('btn-stop').classList.add('hidden');$('btn-playback').classList.add('hidden');
  $('btn-save-recording').classList.add('hidden');$('btn-discard-recording').classList.add('hidden');
  $('btn-playback').textContent='▶ Play';$('record-timer').textContent='00:00';clearWaveform();$('waveform-idle').style.display='';}
function updateTimer(){const m=String(Math.floor(S.recordingSeconds/60)).padStart(2,'0');const s=String(S.recordingSeconds%60).padStart(2,'0');$('record-timer').textContent=`${m}:${s}`;}
function drawWaveform(){const canvas=$('waveform-canvas');const ctx2=canvas.getContext('2d');const W=canvas.width,H=canvas.height;const buf=new Uint8Array(S.analyser.frequencyBinCount);
  function render(){S.animFrame=requestAnimationFrame(render);S.analyser.getByteTimeDomainData(buf);ctx2.clearRect(0,0,W,H);
    ctx2.beginPath();ctx2.strokeStyle='#6c5ce7';ctx2.lineWidth=2;const sl=W/buf.length;let x=0;
    for(let i=0;i<buf.length;i++){const y=(buf[i]/128.0)*(H/2);i===0?ctx2.moveTo(x,y):ctx2.lineTo(x,y);x+=sl;}ctx2.stroke();}render();}
function clearWaveform(){$('waveform-canvas').getContext('2d').clearRect(0,0,600,80);}

// ── Toast ─────────────────────────────────────────────────────────────────
function toast(msg,type='ok'){const c=$('toasts');const el=document.createElement('div');
  el.className=`toast ${type}`;el.innerHTML=`<span>${type==='ok'?'✓':type==='err'?'✗':'⚠'}</span><span>${msg}</span>`;
  c.appendChild(el);setTimeout(()=>{el.style.opacity='0';el.style.transform='translateX(12px)';el.style.transition='.3s';setTimeout(()=>el.remove(),300);},3000);}
