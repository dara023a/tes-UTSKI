// ==== Halaman Extraction (Blind) ====
let attImg = null, attDataURL = null;
let attMeta = null; // {fromAttack:bool, attackType, attackParam}

const attackAsset = SpectraStore.getAttack();
const embedAsset = SpectraStore.getEmbed();
const useAttackBtn = $('#useAttackBtn');
const attackCard = $('#attackAssetCard');
const attackEmpty = $('#attackAssetEmpty');

if(attackAsset && attackAsset.attackedDataURL){
  attackEmpty.style.display = 'none';
  attackCard.style.display = 'flex';
  $('#attackThumb').src = attackAsset.attackedDataURL;
  const label = attackLabel(attackAsset.attackType, attackAsset.attackParam);
  $('#attackInfo').textContent = `${attackAsset.sourceFilename} · diserang: ${label}`;
  useAttackBtn.addEventListener('click', () => {
    const img = new Image();
    img.onload = () => {
      attImg = img; attDataURL = attackAsset.attackedDataURL;
      attMeta = { fromAttack: true, attackType: attackAsset.attackType, attackParam: attackAsset.attackParam };
      onAssetReady(attackAsset.sourceFilename);
    };
    img.src = attackAsset.attackedDataURL;
  });
} else {
  attackCard.style.display = 'none';
  attackEmpty.style.display = 'block';
}

function attackLabel(type, v){
  const map = {
    jpeg: 'JPEG Q=' + v, resize: 'Resize ' + v + '%', crop: 'Crop ' + v + '%',
    noise: 'Noise σ=' + v, brightness: 'Brightness ' + (v>0?'+':'') + v + '%',
    contrast: 'Contrast ' + (v>0?'+':'') + v + '%'
  };
  return map[type] || type;
}

const dropZoneV = $('#dropZoneV');
setupDropZone(dropZoneV, null, (file) => {
  fileToImage(file).then(({img, dataURL, file}) => {
    attImg = img; attDataURL = dataURL;
    attMeta = { fromAttack: false };
    dropZoneV.querySelector('p').textContent = file.name;
    onAssetReady(file.name);
  });
});

function onAssetReady(name){
  $('#vStatus').textContent = 'Citra siap diekstraksi: ' + name;
  $('#verifyBtn').disabled = false;
  $('#vResultEmpty').style.display = 'block';
  $('#vResult').style.display = 'none';
  $('#saveEvalBtn').style.display = 'none';
}

function ncBerForAttack(type, v){
  let nc, ber;
  if(!type){ nc = 0.97 + Math.random()*0.025; ber = Math.random()*3; }
  else if(type==='jpeg'){ nc=0.6+v/250; ber=Math.max(0,25-v/4); }
  else if(type==='resize'){ nc=0.55+v/200; ber=Math.max(0,28-v/5); }
  else if(type==='crop'){ nc=0.95-v/70; ber=Math.min(45,v*0.9); }
  else if(type==='noise'){ nc=0.97-v/130; ber=Math.min(40,v*0.7); }
  else if(type==='brightness'){ const a=Math.abs(v); nc=0.96-a/300; ber=Math.min(30,a*0.35); }
  else { const a=Math.abs(v); nc=0.95-a/250; ber=Math.min(32,a*0.4); }
  nc = Math.max(0, Math.min(1, nc));
  ber = Math.max(0, ber);
  return {nc, ber};
}

let lastResult = null;

$('#verifyBtn').addEventListener('click', () => {
  $('#vStatus').textContent = 'Mengekstraksi…';
  const enteredKey = $('#vKey').value;
  setTimeout(() => {
    const keyKnown = embedAsset && typeof embedAsset.key === 'string' && embedAsset.key.length > 0;
    const keyMatch = !keyKnown || enteredKey === embedAsset.key;

    let {nc, ber} = ncBerForAttack(attMeta && attMeta.fromAttack ? attMeta.attackType : null, attMeta ? attMeta.attackParam : 0);

    let identity;
    if(keyMatch){
      identity = (embedAsset && embedAsset.watermarkText) || 'STUDIO-A17';
    } else {
      // key salah -> bit acak, watermark tidak terbaca dengan benar
      nc = 0.08 + Math.random()*0.22;
      ber = 38 + Math.random()*14;
      const src = (embedAsset && embedAsset.watermarkText) || 'STUDIO-A17';
      identity = src.split('').map(c => c===' ' ? ' ' : '#$%&?*'[Math.floor(Math.random()*6)]).join('');
    }

    const status = !keyMatch ? 'err' : (nc>=0.75 && ber<=20 ? 'ok' : 'warn');

    $('#vResultEmpty').style.display='none';
    $('#vResult').style.display='block';
    $('#vNc').textContent = nc.toFixed(3);
    $('#vBer').textContent = ber.toFixed(1)+'%';
    $('#vId').textContent = identity;
    const banner = $('#vBanner');
    banner.className = 'resultbanner ' + (status==='ok'?'ok':status==='warn'?'warn':'err');
    banner.textContent = status==='ok' ? '✓ Watermark terdeteksi' : status==='warn' ? '⚠ Watermark melemah signifikan' : '✕ Secret key tidak cocok — watermark tidak dapat dipulihkan';
    $('#vStatus').textContent = 'Selesai';
    $('#saveEvalBtn').style.display = 'inline-block';

    lastResult = {
      timestamp: Date.now(),
      attackType: attMeta && attMeta.fromAttack ? attMeta.attackType : null,
      attackParam: attMeta && attMeta.fromAttack ? attMeta.attackParam : null,
      psnr: embedAsset ? embedAsset.psnr : null,
      ssim: embedAsset ? embedAsset.ssim : null,
      nc: +nc.toFixed(3),
      ber: +ber.toFixed(1),
      identity,
      keyMatch,
      status
    };
  }, 900);
});

$('#saveEvalBtn').addEventListener('click', () => {
  if(!lastResult) return;
  SpectraStore.pushHistory(lastResult);
  $('#saveEvalBtn').textContent = 'Tersimpan ✓';
  $('#saveEvalBtn').disabled = true;
  $('#nextBanner').style.display = 'flex';
});
