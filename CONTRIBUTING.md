# Katkı rehberi

## Geliştirme

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
python -m kisayol
```

- Kanca ve işçi iş parçacıkları Tk'ye asla doğrudan dokunmaz; arayüze yalnızca `post(event)` ile mesaj gönderir (`app.py` → `tick()`).
- Saf Python çekirdek (`matcher`, `variables`, `snippets`, `config`, `search`) Windows'a dokunmaz ve birim testlerle korunur. Yeni davranış = önce kırmızı test.
- Yazılan metni **hiçbir zaman** diske, loga ya da ağa göndermeyin. Hata ayıklama için bile.

## Uçtan uca kontrol

```bash
python scripts/e2e_check.py
```

Kendi küçük penceresini açar, tuşları **ayrı bir işlemden** gönderir (`keyboard` kütüphanesi kendi işleminin gönderdiği tuşları kancaya iletmez) ve sonucu doğrular. Pencere öne gelemezse bir kez tıklayın. Not: tuş adları Türkçe Q klavyeye göre yazılmıştır (`;` = Shift + virgül tuşu). Çalışırken KısaYol'un kendisini kapatın, yoksa iki kanca birden genişletir.

`python scripts/smoke.py` arayüzsüz çalışır; istediğiniz programda elle deneyebilirsiniz.

## Elle test listesi (sürüm öncesi)

Türkçe Q klavyeyle, exe sürümünde:

- [ ] Not Defteri, Chrome, Word, Outlook, Discord'da `;tarih`, `;imza` (imleç alt satırda), sembolsüz bir kalıp + virgül.
- [ ] Kelime içinde sembolsüz tetikleyici genişlemiyor (`Paslm`).
- [ ] Word'den biçimli metin kopyala → bir kalıbı genişlet → Ctrl+V ile Word'e yapıştır: biçim korunmuş.
- [ ] Panoda bir resim varken genişlet → resim hâlâ panoda.
- [ ] AltGr ile `@`, `€`, `{` yazılabiliyor (kısayollar AltGr'yi bozmamalı).
- [ ] `Ctrl+Alt+P` öndeki uygulamaya ulaşmıyor; duraklatılmışken genişletme yok.
- [ ] Arama penceresi farenin olduğu ekranda açılıyor; Enter ile seçilen kalıp önceki uygulamaya ekleniyor.
- [ ] Shift basılıyken tetikleme (`;Adr` gibi) Shift'i takılı bırakmıyor.
- [ ] Pencereyi kapat → tepsiye iniyor; exe'yi ikinci kez aç → mevcut pencere geliyor.
- [ ] Yönetici olarak çalışan bir programda: normal modda genişlemiyor, "Yönetici olarak yeniden başlat" sonrası genişliyor.
- [ ] Windows ile başlat açık/kapalı (Kayıt Defteri `HKCU\…\Run\KisaYol`).
- [ ] 7 dilin hepsinde arayüz açılıyor, 12 tema arasında geçiş çalışıyor.
