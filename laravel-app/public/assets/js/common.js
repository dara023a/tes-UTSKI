// ==== Helper umum dipakai di semua halaman ====
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// burger menu mobile
(function initNav(){
  const btn = $('.burger'), links = $('#navlinks');
  if(btn && links) btn.addEventListener('click', () => links.classList.toggle('open'));
})();

function clamp255(x){ return x<0?0:x>255?255:x; }

function drawImgToCanvas(img, canvas){
  const ctx = canvas.getContext('2d');
  const w = canvas.clientWidth || canvas.width, h = canvas.clientHeight || canvas.height;
  canvas.width = w; canvas.height = h;
  const r = Math.max(w/img.width, h/img.height);
  const iw = img.width*r, ih = img.height*r;
  ctx.drawImage(img, (w-iw)/2, (h-ih)/2, iw, ih);
  return ctx;
}

function fileToImage(file){
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload = () => resolve({img, dataURL: e.target.result, file});
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function downloadDataURL(filename, dataURL){
  const a = document.createElement('a');
  a.download = filename; a.href = dataURL; a.click();
}

function fmtTime(ts){
  const d = new Date(ts);
  return d.toLocaleString('id-ID', {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'});
}

function setupDropZone(zoneEl, inputEl, onFile){
  const open = () => inputEl ? inputEl.click() : triggerPicker(onFile);
  zoneEl.addEventListener('click', open);
  ['dragover','dragleave','drop'].forEach(ev => zoneEl.addEventListener(ev, e => {
    e.preventDefault();
    zoneEl.classList.toggle('drag', ev === 'dragover');
  }));
  zoneEl.addEventListener('drop', e => {
    const f = e.dataTransfer.files[0];
    if(f) onFile(f, zoneEl);
  });
  if(inputEl) inputEl.addEventListener('change', e => { if(e.target.files[0]) onFile(e.target.files[0], zoneEl); });
}

function triggerPicker(onFile){
  const inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/*';
  inp.onchange = e => { if(e.target.files[0]) onFile(e.target.files[0]); };
  inp.click();
}

function togglePasswordVisibility(inputId, btn) {
  const inp = document.getElementById(inputId);
  if (!inp) return;
  const isPass = inp.type === 'password';
  inp.type = isPass ? 'text' : 'password';
  btn.innerHTML = isPass
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
}

