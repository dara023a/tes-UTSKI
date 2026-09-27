// ==== Lapisan penyimpanan sementara (browser localStorage) ====
// CATATAN UNTUK TIM:
// Prototipe UI ini masih tahap simulasi front-end (belum terhubung ke
// Python engine / Laravel). Supaya data bisa "mengalir" dari halaman
// Embedding -> Attack -> Extraction -> Evaluation tanpa backend dulu,
// hasil sementara disimpan di localStorage browser (per perangkat/browser,
// tidak terkirim ke server mana pun). Saat Tahap 6 (integrasi Laravel)
// selesai, ganti pemanggilan di bawah ini dengan request ke API Laravel
// yang menyimpan hasil ke database, cukup di titik ini saja.

const SP_KEYS = {
  EMBED: 'spectra_embed_asset',
  ATTACK: 'spectra_attack_asset',
  HISTORY: 'spectra_eval_history'
};

const SpectraStore = {
  saveEmbed(data){
    localStorage.setItem(SP_KEYS.EMBED, JSON.stringify(data));
  },
  getEmbed(){
    try { return JSON.parse(localStorage.getItem(SP_KEYS.EMBED)); } catch(e){ return null; }
  },
  saveAttack(data){
    localStorage.setItem(SP_KEYS.ATTACK, JSON.stringify(data));
  },
  getAttack(){
    try { return JSON.parse(localStorage.getItem(SP_KEYS.ATTACK)); } catch(e){ return null; }
  },
  getHistory(){
    try { return JSON.parse(localStorage.getItem(SP_KEYS.HISTORY)) || []; } catch(e){ return []; }
  },
  pushHistory(record){
    const h = this.getHistory();
    h.push(record);
    localStorage.setItem(SP_KEYS.HISTORY, JSON.stringify(h));
    return h;
  },
  clearHistory(){
    localStorage.removeItem(SP_KEYS.HISTORY);
  }
};
