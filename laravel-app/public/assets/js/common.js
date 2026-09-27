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
