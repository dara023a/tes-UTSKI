// ==== Halaman Evaluation ====
function attackLabel(type, v){
  if(!type) return 'Tanpa attack';
  const map = {
    jpeg: 'JPEG Q=' + v, resize: 'Resize ' + v + '%', crop: 'Crop ' + v + '%',
    noise: 'Noise σ=' + v, brightness: 'Brightness ' + (v>0?'+':'') + v + '%',
    contrast: 'Contrast ' + (v>0?'+':'') + v + '%'
  };
  return map[type] || type;
}

function render(){
  const history = SpectraStore.getHistory();
  const tbody = $('#evalBody');
  const emptyState = $('#emptyState');
  const tableWrap = $('#tableWrap');
  const chartCard = $('#chartCard');
  const toolbar = $('#tableToolbar');

  if(!history.length){
    emptyState.style.display = 'block';
    tableWrap.style.display = 'none';
    chartCard.style.display = 'none';
    toolbar.style.display = 'none';
    return;
  }
  emptyState.style.display = 'none';
  tableWrap.style.display = 'block';
  chartCard.style.display = 'block';
  toolbar.style.display = 'flex';

  tbody.innerHTML = '';
  history.slice().reverse().forEach(r => {
    const tr = document.createElement('tr');
    const pillClass = r.status==='ok' ? 'ok' : r.status==='warn' ? 'warn' : 'err';
    const pillText = r.status==='ok' ? 'Terdeteksi' : r.status==='warn' ? 'Melemah' : 'Key salah';
    tr.innerHTML = `
      <td>${fmtTime(r.timestamp)}</td>
      <td>${attackLabel(r.attackType, r.attackParam)}</td>
      <td>${r.psnr!=null ? r.psnr.toFixed(2)+' dB' : '—'}</td>
      <td>${r.ssim!=null ? r.ssim.toFixed(3) : '—'}</td>
      <td>${r.nc.toFixed(3)}</td>
      <td>${r.ber.toFixed(1)}%</td>
      <td>${r.identity}</td>
      <td><span class="status-pill ${pillClass}">${pillText}</span></td>`;
    tbody.appendChild(tr);
  });

  drawChart(history);
}

function drawChart(history){
  const canvas = $('#evalChart');
  const dpr = window.devicePixelRatio || 1;
  const rows = history.length;
  const rowH = 34;
  const wCss = Math.max(560, $('.chart-wrap').clientWidth);
  const hCss = Math.max(120, rows*rowH + 40);
  canvas.width = wCss*dpr; canvas.height = hCss*dpr;
  canvas.style.width = wCss+'px'; canvas.style.height = hCss+'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr,dpr);
  ctx.clearRect(0,0,wCss,hCss);

  const labelW = 168, barAreaW = wCss - labelW - 90, barH = 10, gap = 6;
  ctx.font = '11px IBM Plex Mono, monospace';

  history.forEach((r, i) => {
    const y = 16 + i*rowH;
    const label = attackLabel(r.attackType, r.attackParam);
    ctx.fillStyle = '#5B6472';
    ctx.textAlign = 'left';
    ctx.fillText(label.length>22 ? label.slice(0,21)+'…' : label, 0, y+9);

    // NC bar (skala 0-1)
    ctx.fillStyle = '#DCD9CF';
    ctx.fillRect(labelW, y, barAreaW, barH);
    ctx.fillStyle = '#2F6FEF';
    ctx.fillRect(labelW, y, barAreaW*Math.max(0,Math.min(1,r.nc)), barH);
    ctx.fillStyle = '#101521';
    ctx.textAlign = 'left';
    ctx.fillText(r.nc.toFixed(2), labelW+barAreaW+8, y+9);

    // BER bar (skala 0-50%)
    const y2 = y + barH + gap;
    ctx.fillStyle = '#DCD9CF';
    ctx.fillRect(labelW, y2, barAreaW, barH);
    ctx.fillStyle = '#B5732A';
    ctx.fillRect(labelW, y2, barAreaW*Math.max(0,Math.min(1,r.ber/50)), barH);
    ctx.fillStyle = '#101521';
    ctx.fillText(r.ber.toFixed(1)+'%', labelW+barAreaW+8, y2+9);
  });
}

$('#clearHistoryBtn').addEventListener('click', () => {
  if(confirm('Hapus semua riwayat hasil evaluasi di browser ini?')){
    SpectraStore.clearHistory();
    render();
  }
});

$('#exportCsvBtn').addEventListener('click', () => {
  const history = SpectraStore.getHistory();
  const header = ['waktu','attack','parameter','psnr_db','ssim','nc','ber_persen','identitas_terbaca','key_cocok','status'];
  const rows = history.map(r => [
    new Date(r.timestamp).toISOString(), r.attackType||'none', r.attackParam ?? '',
    r.psnr ?? '', r.ssim ?? '', r.nc, r.ber, r.identity, r.keyMatch, r.status
  ]);
  const csv = [header.join(','), ...rows.map(row => row.map(v => `"${String(v).replace(/"/g,'""')}"`).join(','))].join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  downloadDataURL('hasil-evaluasi-spectra.csv', url);
  URL.revokeObjectURL(url);
});

window.addEventListener('resize', () => { if(SpectraStore.getHistory().length) drawChart(SpectraStore.getHistory()); });

render();
