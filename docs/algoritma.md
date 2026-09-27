3.3 Algoritma
-------------

Algoritma yang digunakan pada sistem ini terdiri atas empat bagian: penentuan blok penyisipan menggunakan secret key, algoritma embedding, algoritma extraction, dan perhitungan metrik evaluasi.

### 3.3.1 Algoritma Penentuan Blok (Secret Key → Block Selection)

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   INPUT: secret_key (string), total_blocks (N), watermark_length (L)  OUTPUT: key_sequence[] (index blok yang digunakan, unik dan berurutan)  1. seed = SHA256(secret_key)  2. rng = PRNG(seed)                          // numpy.random.default_rng(seed)  3. permutation = rng.permutation(N)          // acak seluruh N blok tanpa duplikat  4. key_sequence = permutation[0 : L]         // ambil L blok pertama  5. RETURN key_sequence   `

Setiap blok hanya digunakan tepat satu kali, dan urutan blok yang sama harus direproduksi ulang saat extraction menggunakan secret key yang identik.

### 3.3.2 Algoritma Embedding

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   INPUT: original_image (grayscale), watermark_bits[], secret_key, α (margin)  OUTPUT: watermarked_image, PSNR  1. blocks = split(original_image, 8, 8)                     // total N blok  2. key_sequence = SelectBlocks(secret_key, N, len(watermark_bits))  3. FOR i = 0 TO len(watermark_bits) - 1:       idx = key_sequence[i]       B = DCT(blocks[idx])       C1 = B[4][5]       C2 = B[5][4]       mid = (C1 + C2) / 2       bit = watermark_bits[i]       IF bit == 1:           C1' = mid + α/2           C2' = mid - α/2       ELSE:           C1' = mid - α/2           C2' = mid + α/2       B[4][5] = C1'       B[5][4] = C2'       blocks[idx] = IDCT(B)  4. watermarked_image = combine(blocks)  5. PSNR = calculate_PSNR(original_image, watermarked_image)  6. RETURN watermarked_image, PSNR   `

**Validasi kapasitas** (wajib dicek sebelum embedding dijalankan):

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   N = (width / 8) × (height / 8)  IF len(watermark_bits) > N:      REJECT — watermark melebihi kapasitas maksimum citra   `

### 3.3.3 Algoritma Extraction (Blind)

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   INPUT: attacked_image, secret_key, watermark_length  OUTPUT: extracted_watermark[]  1. blocks = split(attacked_image, 8, 8)  2. key_sequence = SelectBlocks(secret_key, N, watermark_length)  3. FOR i = 0 TO watermark_length - 1:       idx = key_sequence[i]       B = DCT(blocks[idx])       C1 = B[4][5]       C2 = B[5][4]       IF C1 >= C2:           extracted_watermark[i] = 1       ELSE:           extracted_watermark[i] = 0  4. RETURN extracted_watermark   `

Proses ini tidak memerlukan citra asli (original\_image), sehingga tergolong **blind watermarking**.

### 3.3.4 Perhitungan Metrik Evaluasi

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   PSNR(original, watermarked):      MSE = mean((original - watermarked)^2)      RETURN 10 * log10(255^2 / MSE)  NC(original_wm, extracted_wm):      RETURN sum(original_wm * extracted_wm) /             sqrt(sum(original_wm^2) * sum(extracted_wm^2))  BER(original_wm, extracted_wm):      RETURN sum(original_wm XOR extracted_wm) / length(original_wm)   `
### 3.3.5 Penanganan Citra Berwarna (Fase 2, opsional)

Algoritma pada 3.3.1-3.3.4 di atas didefinisikan untuk citra **grayscale**
dan **tidak diubah sama sekali** oleh bagian ini. Penambahan berikut hanya
berlaku sebagai pra-proses (sebelum embedding) dan pasca-proses (setelah
embedding) di level pipeline, supaya citra ilustrasi berwarna tidak perlu
kehilangan warna aslinya setelah proses watermarking -- relevan karena
objek yang dilindungi pada judul penelitian ini adalah **karya ilustrasi
digital**, yang pada praktiknya hampir selalu berwarna.

**Alasan pemilihan pendekatan:** mata manusia jauh lebih sensitif terhadap
perubahan luminance (kecerahan) dibanding krominan (warna). Karena itu,
watermark cukup ditanam pada channel luminance saja; channel warna tidak
disentuh sama sekali sehingga tidak menambah distorsi warna. Ini adalah
teknik standar pada watermarking citra berwarna di literatur, bukan
modifikasi terhadap algoritma DCT itu sendiri.

**Alur (Embedding):**

```
Citra berwarna (BGR)
    -> Konversi ke YCrCb
    -> Pisahkan channel: Y (luminance), Cr, Cb (krominan)
    -> Y masuk Algoritma Embedding (3.3.2) TANPA PERUBAHAN -> Y'
    -> Gabungkan kembali: (Y', Cr, Cb)
    -> Konversi balik ke BGR
    -> Citra watermarked berwarna
```

**Alur (Extraction, tetap blind):**

```
Citra watermarked berwarna (BGR)
    -> Konversi ke YCrCb, ambil channel Y saja
    -> Y masuk Algoritma Extraction (3.3.3) TANPA PERUBAHAN -> extracted_watermark
```

Cr dan Cb dari citra hasil embedding di-crop ke `processed_image_size`
yang sama (lihat 3.3.2) sebelum digabungkan kembali dengan Y', supaya
dimensinya konsisten dengan Y' yang sudah melalui pemotongan ke kelipatan
ukuran blok.

**Implikasi terhadap metrik evaluasi (3.3.4):** PSNR dan metrik kualitas
citra lain dihitung pada channel Y saja (dibandingkan dengan Y dari citra
asli), konsisten dengan definisi di 3.3.4 -- bukan didefinisikan ulang.
NC dan BER pada watermark tidak berubah sama sekali karena bit yang
diekstraksi berasal dari algoritma 3.3.3 yang identik.

**Catatan implementasi:** mode ini bersifat opsional (`preserve_color`
pada pipeline); ketika dinonaktifkan, seluruh proses kembali murni
grayscale sesuai 3.3.1-3.3.4 tanpa ada langkah tambahan apapun.
