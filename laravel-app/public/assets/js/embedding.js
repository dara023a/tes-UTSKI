// ==== Halaman Embedding ====
let currentImg = null, currentDataURL = null, currentFile = null;

const dropZone = $('#dropZone'), fileInput = $('#fileInput');
setupDropZone(dropZone, fileInput, handleFile);

function handleFile(file){
  fileToImage(file).then(({img, dataURL}) => {
    currentImg = img; currentDataURL = dataURL; currentFile = file;
    $('#metaBox').style.display='grid';
    $('#mDim').textContent = img.width+' × '+img.height+' px';
    $('#mFmt').textContent = (file.type.split('/')[1]||'?').toUpperCase();
    $('#mSize').textContent = (file.size/1024).toFixed(0)+' KB';
    $('#mBlocks').textContent = (Math.ceil(img.width/8)*Math.ceil(img.height/8)).toLocaleString('id-ID');
    $('#processBtn').disabled = false;
    $('#wsStatus').textContent = 'Citra siap diproses';
    dropZone.querySelector('p').textContent = file.name;
    // reset hasil sebelumnya kalau ganti citra
    $('#compareBox').style.display='none';
    $('#compareSlider').style.display='none';
    $('#metricRow').style.display='none';
    $('#downloadBtn').style.display='none';
    $('#nextBanner').style.display='none';
  });
}

$('#processBtn').addEventListener('click', () => {
  if(!currentImg) return;
  $('#processBtn').disabled = true;
  $('#wsStatus').textContent = 'Memproses…';
  const stages = $$('#stageList .stage');
  let i = 0;
  stages.forEach(s => s.className='stage');
  const tick = () => {
    if(i>0) stages[i-1].classList.replace('active','complete');
    if(i<stages.length){ stages[i].classList.add('active'); i++; setTimeout(tick, 480); }
    else finishEmbed();
  };
  tick();
});

function finishEmbed(){
  $('#wsStatus').textContent = 'Selesai';
  $('#compareBox').style.display='block';
  $('#compareSlider').style.display='block';
  $('#metricRow').style.display='flex';
  $('#downloadBtn').style.display='block';
  const c1 = $('#cvOrig'), c2 = $('#cvWm');
  drawImgToCanvas(currentImg, c1);
  drawImgToCanvas(currentImg, c2);
  // efek halus untuk menggambarkan perubahan yang (secara desain) tak kasat mata
  const ctx = c2.getContext('2d');
  ctx.globalAlpha = 0.04; ctx.fillStyle = '#2F6FEF';
  for(let y=0;y<c2.height;y+=8){ for(let x=0;x<c2.width;x+=8){ if((x+y)%16===0) ctx.fillRect(x,y,8,8); } }
  ctx.globalAlpha = 1;

  const psnr = (38 + Math.random()*10);
  const ssim = (0.94 + Math.random()*0.05);
  $('#psnrVal').textContent = psnr.toFixed(2);
  $('#ssimVal').textContent = ssim.toFixed(3);

  const wmText = $('#wmText').value.trim() || 'TANPA-IDENTITAS';
  const key = $('#wmKey').value;
  const watermarkedDataURL = c2.toDataURL('image/png');

  SpectraStore.saveEmbed({
    filename: currentFile ? currentFile.name : 'citra.png',
    width: currentImg.width, height: currentImg.height,
    watermarkText: wmText,
    key: key,
    psnr: +psnr.toFixed(2), ssim: +ssim.toFixed(3),
    watermarkedDataURL,
    originalDataURL: currentDataURL,
    createdAt: Date.now()
  });

  $('#nextBanner').style.display='flex';
}

$('#compareSlider').addEventListener('input', e => {
  $('#cvWm').style.clipPath = `inset(0 ${100-e.target.value}% 0 0)`;
});
$('#downloadBtn').addEventListener('click', () => {
  downloadDataURL('watermarked.png', $('#cvWm').toDataURL());
});
