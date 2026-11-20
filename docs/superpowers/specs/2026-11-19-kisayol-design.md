# KısaYol — Tasarım Belgesi

Tarih: 2026-11-19 · Durum: taslak (onay bekliyor)

> Bu belge şimdilik OtoTık reposunda duruyor; KısaYol reposu oluşturulunca ilk commit ile oraya (`docs/superpowers/specs/`) taşınacak.

## 1. Amaç ve neden

KısaYol, Windows için **ücretsiz ve açık kaynak (MIT) bir metin genişletici**. Kullanıcı `;adr` gibi kısa bir tetikleyici yazdığında KısaYol onu siler ve yerine kayıtlı metni (adres, imza, hazır cevap…) koyar.

Neden: OtoTık ile aynı geliştirici, aynı çizgide (ücretsiz, açık kaynak, tek exe, 7 dil, temalı) ikinci bir yardımcı araç yayımlamak istiyor. Pazar araştırması, bu kategoride ciddi talep olduğunu (espanso ~14.8k★) ama öne çıkan ücretsiz aracın **arayüzsüz, YAML ile ayarlanan** bir araç olduğunu gösterdi. KısaYol'un farkı: **kurulumsuz tek exe + kullanımı kolay arayüz + Türkçe karakterlerde sorunsuz çalışma.**

Başarı ölçütü: GitHub Releases'ten indirilen exe, Türkçe Windows'ta Not Defteri, tarayıcı, Word ve Outlook'ta Türkçe karakterli kalıpları sorunsuz genişletiyor; teknik bilgisi olmayan biri ilk kalıbını 1 dakikada ekleyebiliyor.

## 2. Hedefler, hedef dışı olanlar, başarısızlık sayılacaklar

**Hedefler (v1.0)**
- Tetikleyici yazınca genişletme (yapıştırma ya da harf harf yazma).
- Arayüzden kalıp ekleme / düzenleme / silme / arama; kalıpları **gruplara** ayırma.
- Basit değişkenler: tarih, saat, pano içeriği, imleç konumu.
- Arama penceresi: global kısayolla açılan küçük pencereden kalıp bulup ekleme.
- Sistem tepsisinde arka planda çalışma; duraklat/devam.
- Kalıpları JSON olarak içe/dışa aktarma.
- OtoTık'tan gelen 12 tema, dil altyapısı, otomatik kayıt, tek örnek (single instance), tek exe derleme.

**Hedef dışı (v1.0'da yok, sonra düşünülebilir)**
- Uygulamaya göre kalıp kapsamı / hariç tutulan uygulamalar listesi.
- espanso YAML içe aktarma.
- Form alanlı (doldurmalı) şablonlar, betik/komut çalıştıran kalıplar.
- Bulut senkronu, ekip paylaşımı, lisans/ödeme.
- Kod imzalama sertifikası.
- Windows dışı platformlar.

**Başarısızlık sayılacaklar (çalışsa bile)**
- Yazılan herhangi bir metnin diske, loga ya da ağa gitmesi. Tuş tamponu **yalnızca bellekte** ve son birkaç karakterle sınırlı tutulur. KısaYol hiçbir ağ bağlantısı kurmaz.
- Kullanıcının panosundaki içeriği kaybetmesi (yapıştırma sonrası geri yüklenmeli).
- Yanlış yerde genişletme (ör. tetikleyicinin bir kelimenin ortasında yanlışlıkla eşleşmesi kullanıcıyı sürekli rahatsız ediyorsa).
- Genişletme sırasında takılan modifier tuşları (Ctrl/Shift "basılı kalmış" gibi davranması).

## 3. Kısıtlar

- Python 3.9+, Windows 10/11. Tek dosyalık exe, PyInstaller `--onefile --windowed` (OtoTık'taki `build.bat` deseni).
- Bağımlılıklar: `customtkinter`, `keyboard`, `mouse`, `pillow`, `pystray` (tepsi simgesi — OtoTık'ta yok, yeni). Pano için ek paket yok; `ctypes` ile Win32 (`OpenClipboard`, `GetClipboardData(CF_UNICODETEXT)`…).
- Lisans: MIT, telif "furkibayashi" (OtoTık ile aynı).
- Ayarlar `%APPDATA%\KisaYol\` altında: `settings.json` (uygulama ayarları), `snippets.json` (kalıplar).
- Yönetici olarak çalışan pencerelere, KısaYol yönetici değilse yazamaz (Windows UIPI). OtoTık'taki "yönetici olarak yeniden başlat" düğmesi taşınır.

## 4. Yaklaşımlar

| | Yaklaşım | Artısı | Eksisi |
|---|---|---|---|
| **A (seçildi)** | Ayrı repo; OtoTık'tan gereken modüller kopyalanıp uyarlanır | İki uygulama bağımsız; OtoTık'a dokunulmaz; ayrı sürüm ve Releases; "oto tıklayıcı" algısı ve antivirüs geçmişi taşınmaz | Tema/dil kodundaki bir düzeltme iki yerde yapılır |
| B | Aynı repoda ortak paket | Kod tekrarı yok | Çalışan OtoTık'ı yeniden düzenlemek gerekir; sürüm yönetimi karışır |
| C | OtoTık'a yeni sekme | En az iş | Ayrı uygulama olmaz; hedef kitle (ofis) oto tıklayıcı indirmek istemez |

Kullanıcı **A**'yı seçti. Gerekçe: kopyalanacak kod ~600 satır ve iki uygulama zamanla farklı yönlere gidecek; ortak paket ancak üçüncü bir uygulama çıkarsa değer.

## 5. Kullanıcının verdiği kararlar

- Açık kaynak proje olacak.
- Yaklaşım A: ayrı repo.
- **Karma tetikleyici kuralı:** sembolle başlayanlar anında, sembolsüzler kelime başında yazılıp bitiş karakteri gelince genişler (bkz. 6.2, 6.3).
- Varsayılan genişletme yöntemi **yapıştırma** (pano + Ctrl+V, ardından pano geri yüklenir); her kalıpta "harf harf yaz" seçeneği. *(Bu benim önerimdi; onay sırasında teyit edilecek.)*

## 6. Tasarım

### 6.1 Repo yapısı
`C:\Users\Pc\Desktop\kisayol\` (OtoTık klasörünün kardeşi), yeni git reposu:

```
KisaYol.pyw            # giriş noktası
kisayol/
  __init__.py, __main__.py
  app.py               # CustomTkinter arayüzü (OtoTık app.py'deki yardımcılar: card/row/switch/seg/field, NavItem, osd, ensure_single_instance)
  config.py            # OtoTık Config'in uyarlaması (_merge, atomik save, save_later); profiller yerine gruplar
  snippets.py          # kalıp modeli, snippets.json okuma/yazma, içe/dışa aktarma, doğrulama
  matcher.py           # tuş tamponu + tetikleyici eşleştirme (saf Python, test edilebilir)
  expander.py          # silme + yapıştırma/yazma + pano yedekleme + değişken çözümleme
  hook.py              # klavye/fare kancası (OtoTık InputHub'ın sadeleştirilmiş hali + tampon besleme)
  clipboard.py         # ctypes ile Win32 pano
  tray.py              # pystray tepsi simgesi
  themes.py            # OtoTık'tan aynen
  i18n.py              # OtoTık altyapısı, KısaYol metinleri
tests/                 # pytest: matcher, değişkenler, snippets, config
assets/icon.ico, icon.png
build.bat, requirements.txt, README.md, LICENSE
```

### 6.2 Kalıp modeli
```json
{
  "version": 1,
  "groups": ["Genel"],
  "snippets": [
    {"id": "uuid", "trigger": ";adr", "text": "Atatürk Cad. No:1\nİstanbul",
     "group": "Genel", "method": "paste", "enabled": true}
  ]
}
```
- `method`: `paste` | `type`.
- Tetikleyici kuralları: boş olamaz, boşluk/satır sonu içeremez, en az 2 karakter, benzersiz.
- **İki tür tetikleyici (kullanıcı kararı: karma kural):**
  - **Sembollü**: ilk karakteri harf ya da rakam olmayan (`;adr`, `/imza`, `!tel`). Yazılır yazılmaz genişler.
  - **Sembolsüz** (`slm`, `adr`): yalnızca **kelime başında** yazılıp ardından bir **bitiş karakteri** gelince genişler. Kelimenin içinde ("Paslm…") asla tetiklenmez.
- Tetikleyiciler büyük/küçük harfe duyarlıdır *(benim kararım)*.
- **Ulaşılamayan çiftler engellenir** *(benim kararım)*: anında genişletmede `;a` varken `;ad` hiç yazılamaz (`;a` önce tetiklenir). Bu yüzden bir sembollü tetikleyici başka bir etkin sembollü tetikleyicinin **başlangıcıysa** arayüz (sembolsüzlerde bu sorun yok: `sl` ve `slm` kelime bittiğinde tam eşleşmeyle ayrışır) kaydetmeye izin vermez ve hangi kalıpla çakıştığını gösterir. İçe aktarmada böyle çakışan kalıplar devre dışı (`enabled: false`) olarak alınır ve kullanıcıya listelenir.
- Bir tetikleyici diğerinin **sonu** ise (`dr` ve `;adr`) ikisi de geçerlidir; eşleşmede en uzun kazanır (bkz. 6.3).
- İlk açılışta örnek 3 kalıp eklenir (`;tarih`, `;mail` örneği, `;imza`) — kullanıcı silebilir.

### 6.3 Eşleştirme (matcher)
- Kanca her tuş basışını tampona ekler; tampon son 64 karakterle sınırlı, yalnızca bellekte.
- Yazılabilir karakterler eklenir; `backspace` son karakteri siler.
- Tamponu **sıfırlayanlar**: Enter, Esc, Tab, ok tuşları, Home/End/PgUp/PgDn, Delete, herhangi bir fare tıklaması, Ctrl/Alt/Win ile yapılan kombinasyonlar, ön plandaki pencerenin değişmesi.
- **Sembollü tetikleyiciler:** her eklemeden sonra tampon etkin bir sembollü tetikleyiciyle **bitiyorsa** anında genişlet. Birden fazla eşleşirse en uzunu.
- **Sembolsüz tetikleyiciler:** eklenen karakter bir **bitiş karakteri** ise (boşluk ve `. , ! ? : ; ) ] } " '`), ondan önceki kelimeye bakılır. Bu kelime tam olarak bir sembolsüz tetikleyiciyse **ve** kelime başındaysa (kelimeden önce tampon başı ya da boşluk/noktalama varsa) genişlet. Genişletmede tetikleyici + bitiş karakteri silinir, metin eklenir, bitiş karakteri yeniden yazılır (`slm,` → `Selamlar,`). Enter ve Tab bitiş karakteri **değildir** (tuş zaten uygulamaya ulaşmış ve mesaj gönderilmiş olabilir); bunlar tamponu sıfırlar.
- Tampon sıfırlandıktan hemen sonra yazılan kelime "kelime başında" sayılır (ör. yeni bir alana tıklayıp `slm ` yazmak).
- Not: sembollü bir tetikleyicinin içinde geçen bitiş karakteri (ör. `;` ile başlayan) sembolsüz eşleşmeyi tetiklemez; sembolsüz kontrol yalnızca harf/rakamdan oluşan son kelimeye bakar.
- Karakter tespiti: `keyboard` kütüphanesinin `event.name` değeri Türkçe Q/F klavyede `ş`, `ğ`, `ı` gibi harfleri doğru veriyor mu, uygulama sırasında **doğrulanacak**. Vermiyorsa `ToUnicodeEx` ile tuş kodundan karakter üretilir. (Uygulayıcı kararı; bkz. §7.)

### 6.4 Genişletme (expander)
1. Kancayı genişletme süresince "kendi girdisini yok say" moduna al (yoksa KısaYol kendi yazdığını tampona ekler).
2. Basılı modifier tuşlarını bekle/bırak (takılı Shift/Ctrl önlemi).
3. `len(trigger)` kez Backspace (sembolsüz tetikleyicide +1, bitiş karakteri için; o karakter en sonda yeniden yazılır).
4. Değişkenleri çözümle (6.5).
5. `paste`: panodaki **tüm biçimleri** yedekle → metni panoya koy → Ctrl+V → ~150 ms bekle → yedeği geri koy. *(Benim kararım.)* Word, Outlook ve tarayıcıdan kopyalanan içerik her zaman düz metnin yanında HTML/RTF gibi biçimler de taşıdığı için yalnızca düz metni yedeklemek biçimlendirmeyi sessizce kaybettirir. Bu yüzden `EnumClipboardFormats` ile gezilen ve `HGLOBAL` olan her biçim (metin, HTML, RTF, `CF_DIB` resim, `CF_HDROP` dosya listesi, özel biçimler) kopyalanıp geri yüklenir. `HGLOBAL` olmayan GDI tutamaçlı biçimler (`CF_BITMAP`, `CF_ENHMETAFILE`, `CF_PALETTE`) atlanır; Windows bunları `CF_DIB`'den yeniden üretir. Yedekleme herhangi bir nedenle başarısız olursa (pano başka uygulamada kilitli vb.) o genişletme **harf harf yazmaya düşer**; pano asla boşaltılmış hâlde bırakılmaz.
   `type`: `keyboard.write` ile, karakter arası gecikme ayarlanabilir (varsayılan 0–5 ms). Satır sonu **Shift+Enter** olarak gönderilir *(benim kararım)*: düz Enter Discord, Teams, WhatsApp Web gibi sohbet uygulamalarında mesajı erken gönderir; Not Defteri ve Word'de Shift+Enter de yeni satır açar. Kalıp başına "satır sonunda Enter kullan" seçeneği v1'de yok.
6. `{imleç}` varsa: imleçten sonraki karakter sayısı kadar Sol ok.
7. Tamponu sıfırla, sayaç/istatistiği artır (yalnızca sayı; metin değil).

### 6.5 Değişkenler
- `{tarih}` → `19.11.2026` (biçim ayarlardan, varsayılan `%d.%m.%Y`), `{tarih:%Y-%m-%d}` gibi özel biçim desteklenir.
- `{saat}` → `14:05` (aynı şekilde `{saat:%H:%M:%S}`).
- `{pano}` → yedeklenen pano metni.
- `{imleç}` → genişletme sonrası imlecin duracağı yer (en fazla bir tane).
- `{{` ve `}}` → düz `{` `}`. Tanınmayan `{...}` olduğu gibi bırakılır.
- Değişken adlarının İngilizce eşleri de kabul edilir (`{date}`, `{time}`, `{clipboard}`, `{cursor}`).

### 6.6 Arayüz
Sol menülü tek pencere (OtoTık düzeni):

```
┌──────────┬──────────────────────────────────────────┐
│ KısaYol  │ [Ara…            ] [Grup: Tümü ▾] [+ Yeni]│
│          │ ┌──────────────┬───────────────────────┐ │
│ ▸ Kalıplar│ │ ;adr  Adres  │ Tetikleyici: [;adr   ]│ │
│   Ayarlar │ │ ;imza İmza   │ Grup: [Genel ▾]       │ │
│   Hakkında│ │ ;tarih …     │ Metin:                │ │
│          │ │              │ ┌───────────────────┐ │ │
│ ● Etkin  │ │              │ │ Atatürk Cad. …    │ │ │
│ [Duraklat]│ │              │ └───────────────────┘ │ │
│          │ │              │ Yöntem: (Yapıştır|Yaz)│ │
│          │ │              │ [Değişken ekle ▾] [Sil]│ │
│          │ └──────────────┴───────────────────────┘ │
└──────────┴──────────────────────────────────────────┘
```
- Değişiklikler otomatik kaydedilir (OtoTık'taki `save_later`).
- **Ayarlar**: dil, tema/vurgu, duraklat kısayolu (varsayılan `ctrl+alt+p`), arama penceresi kısayolu (varsayılan `ctrl+alt+space`), tarih/saat biçimi, yazma gecikmesi, Windows ile başlat, genişletme sesi/OSD, içe/dışa aktar, yönetici olarak yeniden başlat.
- **Pencereyi kapatmak** uygulamayı tepsiye gizler; çıkış tepsi menüsünden. Tepsi menüsü: Aç · Duraklat/Devam · Çıkış.
- **Arama penceresi**: kısayolla imlecin yakınında küçük, her zaman üstte bir pencere; yazdıkça tetikleyici + metin içinde arar; Enter ile seçileni önceki pencereye ekler (pencere kapanır, odak geri döner, sonra genişletme yapılır).
- Duraklatılmışken tepsi simgesi soluk görünür.

### 6.7 Dil
- Dil altyapısı OtoTık'tan; metinler KısaYol'a özel. v1'de **Türkçe ve İngilizce eksiksiz**; diğer 5 dil (de, es, fr, pt, ru) aynı anahtarlarla çevrilir — eksik kalan anahtar İngilizceye düşer (mevcut davranış).

### 6.8 Gizlilik ve güven (README'de açıkça yazılacak)
- Kanca neden var, neyi tutar (son 64 karakter, bellekte), neyi asla yapmaz (diske yazma, ağ).
- Antivirüs yanlış alarmı olabileceği ve kaynaktan derleme talimatı.

### 6.9 Test
- `pytest`: matcher (ekleme, backspace, sıfırlama, en uzun eşleşme, Türkçe karakter, sembolsüz tetikleyicide kelime başı/bitiş karakteri ve kelime içinde tetiklenmeme, ulaşılamayan çift doğrulaması), değişken çözümleme, snippets doğrulama ve içe/dışa aktarma, config birleştirme.
- Elle test listesi (README/CONTRIBUTING'de): Not Defteri, Chrome, Word, Outlook, Discord; Türkçe Q klavye; pano geri yükleme; takılı modifier; yönetici penceresi.

## 7. Uygulayıcıya bırakılanlar
- `keyboard` olay adlarının Türkçe karakterleri doğru verip vermediği ve gerekiyorsa `ToUnicodeEx` yolu.
- Pano geri yükleme bekleme süresinin (≈150 ms) hedef uygulamalarda yeterli olup olmadığı; gerekirse ayarlanabilir yapmak.
- Ön plan pencere değişimini algılama yöntemi (`GetForegroundWindow` yoklaması ya da olay kancası).
- Simge tasarımı (OtoTık'taki `tools/make_icon.py` yaklaşımı kullanılabilir).
- Arama penceresinde odağın önceki pencereye güvenilir biçimde geri verilmesi.
