// ==== Khusus halaman index.html ====

// hero pipeline nodes
const pipe = [["Citra Asli","IMG"],["Watermark + Key","WM+K"],["DCT","DCT"],["Penyisipan","EMB"],["Ter-watermark","OUT"]];
const ph = $('#heroPipeline');
if(ph){
  pipe.forEach((p,i)=>{
    const n=document.createElement('div'); n.className='pnode';
    n.innerHTML=`<div class="box"><svg width="26" height="26" viewBox="0 0 8 8">${Array.from({length:16},(_,k)=>`<rect x="${(k%4)*2}" y="${Math.floor(k/4)*2}" width="1.6" height="1.6" fill="#2F6FEF" opacity="${(Math.sin(i+k)+1.2)/2}"/>`).join('')}</svg></div><span>${p[0]}</span>`;
    ph.appendChild(n);
    if(i<pipe.length-1){const a=document.createElement('div');a.className='parrow';ph.appendChild(a);}
  });
}

// ---- EDUKASI accordion ----
const terms=[
 ["Apa itu Digital Watermarking?","Teknik menyisipkan informasi kepemilikan ke dalam data citra sehingga dapat digunakan untuk membuktikan siapa pembuat aslinya."],
 ["Apa itu Blind Watermarking?","Proses ekstraksi watermark yang tidak membutuhkan citra asli — hanya citra yang diperiksa dan secret key."],
 ["Apa itu DCT?","Discrete Cosine Transform, transformasi yang mengubah citra dari domain piksel ke domain frekuensi agar watermark bisa disisipkan secara halus."],
 ["Mengapa menggunakan frekuensi menengah?","Frekuensi menengah menjadi titik seimbang: cukup stabil untuk bertahan dari kompresi, namun tidak mengganggu detail visual seperti frekuensi rendah."],
 ["Apa itu Secret Key?","Kunci rahasia yang menentukan posisi penyisipan watermark, sehingga hanya pemilik key yang dapat mengekstraksinya kembali."],
 ["Apa itu Pseudo-noise?","Barisan angka semu-acak yang dihasilkan dari secret key, digunakan untuk menyebarkan bit watermark ke seluruh citra."],
 ["Apa itu Imperceptibility?","Ukuran seberapa tidak terlihatnya watermark — semakin tinggi, semakin mirip citra asli dan citra ter-watermark."],
 ["Apa itu Robustness?","Ketahanan watermark terhadap manipulasi seperti kompresi, resize, atau cropping tanpa kehilangan informasi."],
 ["Apa itu Security?","Jaminan bahwa watermark hanya bisa diekstraksi oleh pihak yang memiliki secret key yang benar."],
 ["Apa itu PSNR?","Ukuran kualitas visual yang membandingkan citra asli dengan citra ter-watermark — makin tinggi nilainya, makin kecil perbedaannya."],
 ["Apa itu SSIM?","Ukuran kemiripan struktur visual dua citra, dengan nilai 0–1; makin dekat ke 1, makin mirip strukturnya."],
 ["Apa itu NC?","Normalized Correlation, mengukur kemiripan antara watermark asli dan watermark hasil ekstraksi setelah citra diserang. Makin dekat ke 1, makin berhasil watermark bertahan."],
 ["Apa itu BER?","Bit Error Rate, persentase bit watermark yang salah terbaca saat ekstraksi. Makin rendah nilainya, makin akurat watermark yang dipulihkan."],
];
const accWrap=$('#accWrap');
if(accWrap){
  terms.forEach((t)=>{
    const item=document.createElement('div'); item.className='acc-item';
    item.innerHTML=`<button class="acc-btn">${t[0]}<span class="plus">+</span></button><div class="acc-panel"><p>${t[1]}</p></div>`;
    accWrap.appendChild(item);
    const btn=item.querySelector('.acc-btn'), panel=item.querySelector('.acc-panel');
    btn.addEventListener('click',()=>{
      const open=panel.style.maxHeight;
      $$('.acc-panel').forEach(p=>p.style.maxHeight=null);
      $$('.acc-btn .plus').forEach(p=>p.textContent='+');
      if(!open){ panel.style.maxHeight=panel.scrollHeight+'px'; btn.querySelector('.plus').textContent='–'; }
    });
  });
}
