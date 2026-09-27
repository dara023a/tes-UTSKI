// ==== Halaman Attack / Manipulation ====
let srcImg = null; // Image object dari citra yang akan diserang
let srcMeta = { filename: 'citra.png' };

const embedAsset = SpectraStore.getEmbed();
const useEmbedBtn = $('#useEmbedBtn');
const embedCard = $('#embedAssetCard');
const embedEmpty = $('#embedAssetEmpty');

if(embedAsset && embedAsset.watermarkedDataURL){
  embedEmpty.style.display = 'none';
  embedCard.style.display = 'flex';
  $('#embedThumb').src = embedAsset.watermarkedDataURL;
  $('#embedInfo').textContent = `${embedAsset.filename} · ${embedAsset.width}×${embedAsset.height} · PSNR ${embedAsset.psnr}dB`;
  useEmbedBtn.addEventListener('click', () => {
    const img = new Image();
    img.onload = () => {
      srcImg = img;
      srcMeta = { filename: embedAsset.filename, fromEmbedding: true };
      onSourceReady();
    };
    img.src = embedAsset.watermarkedDataURL;
  });
} else {
  embedCard.style.display = 'none';
  embedEmpty.style.display = 'block';
}

const dropZoneR = $('#dropZoneR');
setupDropZone(dropZoneR, null, (file) => {
  fileToImage(file).then(({img, file}) => {
    srcImg = img;
    srcMeta = { filename: file.name, fromEmbedding: false };
    dropZoneR.querySelector('p').textContent = file.name;
    onSourceReady();
  });
});

function onSourceReady(){
  $('#sourceStatus').textContent = 'Citra siap diserang: ' + srcMeta.filename;
  $('#attackPanel').style.display = 'block';
  $('#runAttackBtn').disabled = false;
  $('#robViewer').style.display = 'none';
  $('#saveAttackBtn').style.display = 'none';
  $('#nextBanner').style.display = 'none';
  updateAtkNode();
}

const atkParam = $('#atkParam');
let atkMode = 'jpeg';
let lastAttackedDataURL = null;

function updateAtkNode(){
  const v = atkParam.value;
  const map = {
    jpeg: ['Kompresi JPEG Q=' + v, 'Q = ' + v],
    resize: ['Resize ke ' + v + '%', 'Skala = ' + v + '%'],
    crop: ['Crop ' + v + '% area', 'Area dipotong = ' + v + '%'],
    noise: ['Gaussian Noise σ=' + v, 'Sigma = ' + v],
    brightness: ['Brightness ' + (v>0?'+':'') + v + '%', 'Perubahan = ' + (v>0?'+':'') + v + '%'],
    contrast: ['Contrast ' + (v>0?'+':'') + v + '%', 'Perubahan = ' + (v>0?'+':'') + v + '%']
  };
  $('#atkNode').textContent = map[atkMode][0];
  $('#atkParamVal').textContent = map[atkMode][1];
}

$$('.tabbtn').forEach(b => b.addEventListener('click', () => {
  $$('.tabbtn').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  atkMode = b.dataset.atk;
  const ranges = {
    jpeg: [10,95,70,'Kualitas JPEG'],
    resize: [10,100,50,'Skala Resize (%)'],
    crop: [5,60,20,'Area Crop (%)'],
    noise: [1,50,10,'Sigma Gaussian Noise'],
    brightness: [-60,60,20,'Perubahan Brightness (%)'],
    contrast: [-60,60,20,'Perubahan Contrast (%)']
  };
  const [min,max,val,label] = ranges[atkMode];
  atkParam.min = min; atkParam.max = max; atkParam.value = val;
  $('#atkParamWrap label').textContent = label;
  updateAtkNode();
  $('#robViewer').style.display = 'none';
  $('#saveAttackBtn').style.display = 'none';
  $('#nextBanner').style.display = 'none';
}));
atkParam.addEventListener('input', updateAtkNode);
updateAtkNode();

function applyAttackVisual(mode, v, cvBefore, cvAfter){
  if(!srcImg) return;
  drawImgToCanvas(srcImg, cvBefore);
  const ctxA = cvAfter.getContext('2d');
  const w = cvAfter.clientWidth, h = cvAfter.clientHeight;
  cvAfter.width = w; cvAfter.height = h;
  if(mode==='jpeg'){
    const tmp=document.createElement('canvas'); tmp.width=w; tmp.height=h;
    drawImgToCanvas(srcImg,tmp);
    const q=Math.max(0.05,v/100);
    const im=new Image();
    im.onload=()=>{ ctxA.drawImage(im,0,0,w,h); lastAttackedDataURL = cvAfter.toDataURL('image/png'); };
    im.src=tmp.toDataURL('image/jpeg',q);
  } else if(mode==='resize'){
    const scale=Math.max(0.06,v/100);
    const sw=Math.max(1,Math.round(w*scale)), sh=Math.max(1,Math.round(h*scale));
    const tmp=document.createElement('canvas'); tmp.width=sw; tmp.height=sh;
    drawImgToCanvas(srcImg,tmp);
    ctxA.imageSmoothingEnabled=true;
    ctxA.clearRect(0,0,w,h);
    ctxA.drawImage(tmp,0,0,sw,sh,0,0,w,h);
    lastAttackedDataURL = cvAfter.toDataURL('image/png');
  } else if(mode==='crop'){
    drawImgToCanvas(srcImg,cvAfter);
    const frac=Math.min(0.45,Math.sqrt(v/100)/2);
    const cx=w*frac, cy=h*frac;
    ctxA.fillStyle='#000';
    ctxA.fillRect(0,0,w,cy); ctxA.fillRect(0,h-cy,w,cy);
    ctxA.fillRect(0,0,cx,h); ctxA.fillRect(w-cx,0,cx,h);
    lastAttackedDataURL = cvAfter.toDataURL('image/png');
  } else if(mode==='noise'){
    drawImgToCanvas(srcImg,cvAfter);
    const imgData=ctxA.getImageData(0,0,w,h); const d=imgData.data; const sigma=v;
    for(let i=0;i<d.length;i+=4){ const n=(Math.random()-0.5)*2*sigma; d[i]=clamp255(d[i]+n); d[i+1]=clamp255(d[i+1]+n); d[i+2]=clamp255(d[i+2]+n); }
    ctxA.putImageData(imgData,0,0);
    lastAttackedDataURL = cvAfter.toDataURL('image/png');
  } else if(mode==='brightness'||mode==='contrast'){
    ctxA.clearRect(0,0,w,h);
    const pct=100+v;
    ctxA.filter = mode==='brightness' ? `brightness(${pct}%)` : `contrast(${pct}%)`;
    drawImgToCanvas(srcImg,cvAfter);
    ctxA.filter='none';
    lastAttackedDataURL = cvAfter.toDataURL('image/png');
  }
}

$('#runAttackBtn').addEventListener('click', () => {
  if(!srcImg) return;
  const v = +atkParam.value;
  $('#robViewer').style.display = 'block';
  applyAttackVisual(atkMode, v, $('#cvRobBefore'), $('#cvRobAfter'));
  setTimeout(() => {
    $('#saveAttackBtn').style.display = 'inline-block';
    $('#downloadAttackBtn').style.display = 'inline-block';
    $('#nextBanner').style.display = 'none';
  }, 80);
});

$('#downloadAttackBtn').addEventListener('click', () => {
  if(lastAttackedDataURL) downloadDataURL('attacked.png', lastAttackedDataURL);
});

$('#saveAttackBtn').addEventListener('click', () => {
  if(!lastAttackedDataURL) return;
  SpectraStore.saveAttack({
    sourceFilename: srcMeta.filename,
    fromEmbedding: !!srcMeta.fromEmbedding,
    attackType: atkMode,
    attackParam: +atkParam.value,
    attackedDataURL: lastAttackedDataURL,
    createdAt: Date.now()
  });
  $('#nextBanner').style.display = 'flex';
});
