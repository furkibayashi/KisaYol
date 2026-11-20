<div align="center">

<img src="assets/icon.png" width="110" alt="KısaYol simgesi">

# KısaYol

**Windows için ücretsiz, açık kaynak metin genişletici.** `;adr` yaz, adresin gelsin.

Kurulumsuz tek exe · 7 dil · 12 tema · Türkçe karakterlerde sorunsuz

[**⬇ KisaYol.exe'yi indir**](../../releases/latest) · [English](#english)

</div>

---

## ✨ Ne yapar?

Sık yazdığın metinleri (adres, imza, hazır cevap, IBAN, kod parçası…) kısa bir **tetikleyiciye** bağlarsın. Herhangi bir programda tetikleyiciyi yazınca KısaYol onu siler ve yerine metni koyar.

| Özellik | Açıklama |
|---|---|
| ⚡ **Anında genişletme** | `;` `/` `!` gibi bir sembolle başlayan tetikleyiciler yazılır yazılmaz genişler. |
| 🔤 **Doğal kısaltmalar** | Sembolsüz tetikleyiciler (`slm`) yalnızca **kelime başında** yazılıp ardından boşluk ya da noktalama gelince genişler; kelimenin içinde (`Paslm`) asla tetiklenmez. `slm,` → `Selamlar,` |
| 📋 **Pano korunur** | Metin yapıştırılarak eklenir, sonra panondaki her şey (metin, biçimli metin, resim, dosya listesi) geri yüklenir. |
| ⌨ **Harf harf yaz** | Yapıştırmayı engelleyen alanlar için kalıp başına seçenek. Satır sonları Shift+Enter ile gönderilir, sohbet uygulamalarında mesaj yarıda gitmez. |
| 🧩 **Değişkenler** | Tarih, saat, pano içeriği ve imleç konumu (aşağıya bak). |
| 🔍 **Arama penceresi** | `Ctrl + Alt + Space` ile kalıplarını ara, Enter ile ekle. |
| 🗂 **Gruplar** | Kalıplarını gruplara ayır; içe/dışa aktar (JSON). |
| ⏸ **Duraklat** | `Ctrl + Alt + P` ya da tepsi menüsünden. |
| 🪟 **Tepside çalışır** | Pencereyi kapatınca arka planda çalışmaya devam eder; istersen Windows ile başlar. |

## 🧩 Değişkenler

| Yaz | Sonuç (örnek) |
|---|---|
| `{tarih}` / `{date}` | `20.11.2026` (biçim Ayarlar'dan) |
| `{saat}` / `{time}` | `14:05` |
| `{tarih:%Y-%m-%d}` | `2026-11-20` — istediğin `strftime` biçimi |
| `{saat:%H:%M:%S}` | `14:05:09` |
| `{pano}` / `{clipboard}` | Panodaki metin |
| `{imleç}` / `{cursor}` | Genişletmeden sonra imleç buraya gelir |
| `{{` `}}` | Düz `{` `}` |

Örnek imza kalıbı: `Saygılarımla,\n{imleç}` → imza yazılır, imleç alt satırda bekler.

## 🔤 Tetikleyici kuralları

- En az 2 karakter, boşluk içermez, büyük/küçük harfe duyarlı.
- **Sembolle başlayan** (`;adr`, `/imza`, `!tel`): yazılır yazılmaz genişler. Biri diğerinin başı olan iki sembollü tetikleyici (`;a` ve `;ad`) birlikte kullanılamaz, çünkü uzun olan hiç yazılamaz; arayüz bunu engeller.
- **Sembolsüz** (`slm`, `adr`): yalnızca harf ve rakam içerir; kelime başında yazılıp **boşluk ya da `. , ! ? : ; ) ] } " '`** gelince genişler. Enter ve Tab genişletmez.

## ⌨ Varsayılan kısayollar

| Tuş | Eylem |
|---|---|
| `Ctrl + Alt + Space` | Arama penceresi |
| `Ctrl + Alt + P` | Duraklat / devam et |

İkisi de **Ayarlar → Kısayol tuşları** bölümünden değiştirilebilir. Kısayollar Windows'a kaydedilir; bastığında öndeki uygulamaya ulaşmaz.

## 🔒 Gizlilik

Tetikleyicileri fark edebilmek için KısaYol klavyeyi dinler. Bunu açıkça yazıyoruz, çünkü klavye dinleyen her programdan şüphelenmekte haklısın:

- Yalnızca **son 64 karakteri**, yalnızca **bellekte** tutar. Enter, Tab, ok tuşları, fare tıklaması ve pencere değişimi bu tamponu siler.
- Yazdıklarını **asla diske yazmaz, kaydetmez, internete göndermez.** KısaYol hiçbir ağ bağlantısı kurmaz.
- Diske yazılan tek şey senin kalıpların (`%APPDATA%\KisaYol\snippets.json`) ve ayarların (`settings.json`); istatistik olarak yalnızca genişletme **sayısı** tutulur.
- Kodun tamamı bu depoda: `kisayol/hook.py` ve `kisayol/matcher.py` dosyalarına bakabilirsin.

## 🚀 Kurulum

### Seçenek 1: Hazır EXE (önerilen)
[Releases](../../releases/latest) sayfasından **`KisaYol.exe`**'yi indir ve çalıştır. Kurulum gerekmez.

> Windows SmartScreen "tanınmayan uygulama" uyarısı verebilir: **Ek bilgi → Yine de çalıştır**. Klavye dinleyen programları bazı antivirüsler yanlış pozitif olarak işaretleyebilir. Exe imzalı değildir; endişen varsa kaynaktan çalıştır ya da kendin derle.

### Seçenek 2: Kaynaktan çalıştır
```bash
git clone https://github.com/furkibayashi/KisaYol.git
cd KisaYol
pip install -r requirements.txt
python -m kisayol
```
(veya `KisaYol.pyw` dosyasına çift tıkla)

### Kendin EXE derle
```bash
build.bat
```
Çıktı: `dist\KisaYol.exe`

> **Yönetici olarak çalışan programlar:** Windows, normal bir programın yönetici programlarına yazmasına izin vermez. Böyle bir programın içinde genişletmek için **Ayarlar → Yönetici olarak yeniden başlat**.

## 🗂 Proje yapısı

```
kisayol/
├── app.py        # arayüz (CustomTkinter), arama penceresi
├── hook.py       # klavye kancası, Windows kısayol kaydı, genişletme iş parçacığı
├── matcher.py    # tetikleyici eşleştirme (karma kural) — saf Python
├── expander.py   # silme + yapıştırma/yazma + pano geri yükleme
├── variables.py  # {tarih} {saat} {pano} {imleç}
├── clipboard.py  # Win32 pano (tüm biçimleri yedekler)
├── snippets.py   # kalıp modeli, doğrulama, snippets.json
├── config.py     # ayarlar
├── search.py     # kalıp arama
├── tray.py       # sistem tepsisi
├── winutil.py    # tek örnek, yönetici, otomatik başlatma, odak
├── i18n.py       # 7 dil
└── themes.py     # 12 tema
```

Testler: `pip install -r requirements-dev.txt` → `python -m pytest`. Elle test listesi: [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Lisans

[MIT](LICENSE) © 2026 furkibayashi

---

## English

**KısaYol** is a free, open-source text expander for Windows: a single portable `.exe`, 7 languages, 12 themes, and solid support for non-ASCII text such as Turkish.

- Type a trigger anywhere and KısaYol replaces it with your text. Triggers that start with a symbol (`;addr`) expand immediately. Plain-word triggers (`brb`) expand only at the start of a word, once you type a space or punctuation, and never inside a word.
- Text is pasted and **your clipboard is restored**, all formats included. A per-snippet "type" mode is available; it sends line breaks as Shift+Enter, so chat apps don't send early.
- Variables: `{date}`, `{time}`, `{date:%Y-%m-%d}`, `{clipboard}`, `{cursor}`.
- Search window: `Ctrl+Alt+Space`. Pause: `Ctrl+Alt+P`. Runs in the tray, optionally starts with Windows.
- **Privacy:** it listens to the keyboard to notice triggers. It keeps only the last 64 characters, in memory only, and never writes them to disk, logs them or connects to the internet.

Download `KisaYol.exe` from [Releases](../../releases/latest), or run from source with `pip install -r requirements.txt` and `python -m kisayol`. MIT licensed.
