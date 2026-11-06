# Steam Oyunları — Kapsamlı Veri Analizi Projesi

> Bu dosya Claude Code için proje talimatıdır. Projeyi aşağıdaki fazlara göre, **her fazı bitirip bana özet verdikten sonra** bir sonrakine geçerek yap. Her fazın sonunda ne yaptığını, ne bulduğunu ve karşılaştığın sorunları kısaca anlat.

## 1. Proje Özeti

**Amaç:** Steam'de yayınlanmış ~125.000 oyunun verisini kullanarak oyun pazarını uçtan uca analiz etmek. Özellikle şu ana soruya cevap aranıyor:

> **"Steam'de bir oyunun (özellikle bir indie oyunun) başarılı olmasını hangi faktörler belirliyor?"**

**Veri seti:** [Steam Games Dataset — FronkonGames (Kaggle)](https://www.kaggle.com/datasets/fronkongames/steam-games-dataset)

**Çıktılar:**
- Temiz, tekrar çalıştırılabilir Jupyter notebook'lar
- Temizlenmiş veri (parquet)
- Grafikler (`reports/figures/`)
- Bulguları anlatan bir rapor (`reports/RAPOR.md`)
- Basit bir başarı tahmin modeli
- Portfolyoda gösterilebilecek düzgün bir `README.md`

## 2. Teknoloji

- Python 3.11+
- `pandas`, `numpy`
- `matplotlib`, `seaborn`, `plotly` (interaktif grafikler için)
- `scikit-learn`, `xgboost` veya `lightgbm`
- `shap` (model yorumlama)
- `scipy` (istatistiksel testler)
- `wordcloud` (opsiyonel, metin görselleştirme)
- `jupyter`
- `kaggle` CLI (veri indirmek için)

Sanal ortam kullan (`python -m venv .venv`) ve tüm bağımlılıkları `requirements.txt` dosyasına yaz.

## 3. Klasör Yapısı

```
steam-analysis/
├── data/
│   ├── raw/            # Kaggle'dan inen orijinal dosyalar (git'e eklenmez)
│   └── processed/      # Temizlenmiş veri (games_clean.parquet)
├── notebooks/
│   ├── 01_veri_inceleme.ipynb
│   ├── 02_veri_temizleme.ipynb
│   ├── 03_kesifsel_analiz.ipynb
│   ├── 04_derin_analizler.ipynb
│   └── 05_modelleme.ipynb
├── src/
│   ├── __init__.py
│   ├── load.py         # veri yükleme fonksiyonları
│   ├── clean.py        # temizleme fonksiyonları
│   ├── features.py     # özellik mühendisliği
│   └── plots.py        # ortak grafik fonksiyonları ve stil
├── reports/
│   ├── figures/        # tüm grafikler PNG olarak
│   └── RAPOR.md
├── requirements.txt
├── .gitignore
└── README.md
```

Tekrar eden kodları notebook'lara kopyalama; `src/` altına fonksiyon olarak yaz ve notebook'lardan import et.

## 4. Fazlar

### Faz 0 — Kurulum ve Veri İndirme

1. Klasör yapısını ve sanal ortamı oluştur, `requirements.txt` ve `.gitignore` yaz (`data/raw/`, `.venv/`, `.ipynb_checkpoints/` ignore edilsin).
2. Veriyi Kaggle CLI ile indir:
   ```bash
   kaggle datasets download -d fronkongames/steam-games-dataset -p data/raw --unzip
   ```
   Kaggle API anahtarım (`~/.kaggle/kaggle.json`) yoksa dur ve bana nasıl alacağımı söyle; ya da veriyi elle indirip `data/raw/` içine koymamı iste.
3. İnen dosyaları listele (CSV ve JSON versiyonları olabilir).

### Faz 1 — Veri İnceleme (`01_veri_inceleme.ipynb`)

**Önemli:** Kolon isimlerini ve yapısını varsayma, önce gerçekten dosyayı incele.

- Veriyi yükle; satır/kolon sayısını, kolon isimlerini, veri tiplerini göster.
- **Bilinen bir sorun:** Bu veri setinin CSV versiyonunda bazı başlıkların kayması/birleşmesi (örneğin `DiscountDLC count` gibi) nedeniyle kolonların bir sağa veya sola kaymış olabileceği biliniyor. Kontrol et: ilk birkaç satırda değerlerin kolon isimleriyle uyuşup uyuşmadığına bak. Sorun varsa JSON versiyonunu kullan veya başlıkları düzelt. Hangisini seçtiğini ve nedenini notebook'ta yaz.
- Her kolon için: eksik değer oranı, benzersiz değer sayısı, örnek değerler.
- Beklenen önemli kolonlar (gerçek isimleri dosyadan teyit et): uygulama ID'si, isim, çıkış tarihi, tahmini sahip sayısı (aralık olarak, örn. `"0 - 20000"`), eş zamanlı oyuncu zirvesi (Peak CCU), fiyat, DLC sayısı, desteklenen diller, Windows/Mac/Linux desteği, Metacritic puanı, kullanıcı puanı, olumlu/olumsuz review sayısı, başarım sayısı, ortalama/medyan oynama süresi, geliştirici, yayıncı, kategoriler, türler, etiketler.
- Sonunda bir "veri sözlüğü" tablosu oluştur: kolon adı, tipi, açıklaması, eksik oranı.

### Faz 2 — Veri Temizleme (`02_veri_temizleme.ipynb` + `src/clean.py`)

- Kolon isimlerini `snake_case` yap.
- Çıkış tarihini `datetime`'a çevir; `release_year`, `release_month`, `release_weekday` kolonlarını türet. Gelecek tarihli veya parse edilemeyen tarihleri işaretle.
- Tahmini sahip sayısı aralığını (`"20000 - 50000"`) sayısal hale getir: `owners_min`, `owners_max`, `owners_mid` (orta nokta).
- Virgülle ayrılmış alanları (türler, kategoriler, etiketler, diller, geliştirici, yayıncı) listeye çevir. Analiz için en sık görülen türleri/etiketleri one-hot (multi-hot) kolonlara dönüştüren bir fonksiyon yaz.
- Tekrarlayan kayıtları (aynı App ID) temizle.
- Türet:
  - `total_reviews = positive + negative`
  - `positive_ratio = positive / total_reviews` (review yoksa NaN)
  - `is_free` (fiyat 0)
  - `num_languages`, `num_platforms`, `num_genres`, `num_tags`
  - `is_indie` (türler/etiketler içinde "Indie" var mı)
  - `description_length` (oyun açıklamasının uzunluğu)
  - Steam'in review etiket mantığına benzer bir sınıf: örneğin ≥%80 olumlu ve yeterli review → "Very Positive" vb. Kullandığın eşikleri açıkça yaz.
- **Önemli filtre kararı:** Çok sayıda oyunun hiç review'u ve oyuncusu yok. Analizi iki seviyede yap: (1) tüm veri, (2) en az 10 (veya mantıklı bir eşik) review'u olan oyunlar. Eşiği gerekçelendir.
- Uç değerleri (outlier) incele ama silme; gerekirse log dönüşümü kullan (sahip sayısı, review sayısı, oynama süresi çok çarpık dağılır).
- Temiz veriyi `data/processed/games_clean.parquet` olarak kaydet.
- Temizlemenin her adımında kaç satırın etkilendiğini yazdır.

### Faz 3 — Keşifsel Veri Analizi (`03_kesifsel_analiz.ipynb`)

Her grafiğin altına 1–3 cümlelik Türkçe yorum yaz. Grafikleri `reports/figures/` altına numaralı isimle kaydet (`03_01_yillara_gore_cikis.png` gibi).

**3.1 Zaman**
- Yıllara göre çıkan oyun sayısı (Steam'in büyümesi).
- Aylara ve haftanın günlerine göre çıkış dağılımı.
- Yıllara göre ortalama fiyat ve ücretsiz oyun oranı.

**3.2 Fiyat**
- Fiyat dağılımı (histogram + log ölçek).
- En yaygın fiyat noktaları (ör. 4.99, 9.99, 19.99).
- Ücretsiz vs ücretli oyunların review sayısı, olumlu oranı ve sahip sayısı karşılaştırması.

**3.3 Tür ve Etiketler**
- En yaygın 20 tür ve 30 etiket.
- Türlere göre ortalama olumlu oran, medyan sahip sayısı, medyan fiyat.
- Yıllara göre türlerin payının değişimi (hangi türler yükselişte?).
- Etiketlerin birlikte görülme (co-occurrence) ısı haritası (en yaygın 20 etiket).

**3.4 Başarı Metrikleri**
- Olumlu oran, review sayısı, sahip sayısı ve Peak CCU dağılımları.
- Bu metriklerin birbirleriyle korelasyonu.
- Metacritic puanı ile kullanıcı olumlu oranı arasındaki ilişki (sadece puanı olanlar).

**3.5 Platform ve Dil**
- Windows / Mac / Linux desteği oranları ve zamanla değişimi.
- Desteklenen dil sayısı ile başarı arasındaki ilişki.
- En çok desteklenen diller; **Türkçe destekleyen oyunların** oranı ve zamanla değişimi.

**3.6 Geliştirici ve Yayıncı**
- En çok oyun çıkaran geliştiriciler ve yayıncılar.
- Kendi oyununu kendi yayınlayan (developer == publisher) oyunlar ile yayıncılı oyunların başarı karşılaştırması.
- Oyun sayısı çok olan "shovelware" tarzı geliştiricileri tespit et ve ortalama kalitelerine bak.

### Faz 4 — Derin Analizler (`04_derin_analizler.ipynb`)

Ana soruya odaklan: **başarıyı ne belirliyor?**

**4.1 Başarı tanımı:** Başarıyı birden fazla şekilde tanımla ve karşılaştır:
- Kalite: `positive_ratio` yüksek
- Popülerlik: `owners_mid` veya `total_reviews` yüksek
- İkisi birden

**4.2 İndie odaklı analiz:**
- İndie oyunların pazardaki payı ve zamanla değişimi.
- İndie oyunlarda başarılı olanlar (ör. en üst %10) ile diğerlerini karşılaştır: fiyat, tür, etiket sayısı, dil sayısı, platform, başarım sayısı, açıklama uzunluğu, çıkış ayı.
- "Fırsat haritası": her tür/etiket için **oyun sayısı (rekabet)** vs **medyan başarı (talep)** dağılım grafiği. Az rekabetli ama yüksek talep gören nişleri bul.

**4.3 İstatistiksel testler:**
- Ücretsiz vs ücretli, indie vs indie olmayan gibi karşılaştırmalarda uygun testi kullan (dağılımlar normal değilse Mann-Whitney U). p-değerlerini ve etki büyüklüğünü raporla.
- Korelasyonları Spearman ile hesapla.

**4.4 Fiyat-kalite ilişkisi:**
- Fiyat aralıklarına göre (ücretsiz, <5$, 5–10$, 10–20$, 20–40$, 40$+) olumlu oran ve sahip sayısı.

**4.5 Oynama süresi:**
- Türlere göre medyan oynama süresi.
- Oynama süresi ile olumlu oran arasındaki ilişki.

**4.6 Metin analizi (opsiyonel):**
- Başarılı ve başarısız oyunların açıklamalarında en çok geçen kelimeler (TF-IDF ile ayırt edici kelimeler).

### Faz 5 — Modelleme (`05_modelleme.ipynb` + `src/features.py`)

**Görev:** Bir oyunun çıkış öncesi bilinebilecek özelliklerinden, "iyi karşılanıp karşılanmayacağını" tahmin et.

- **Hedef:** Yeterli review'a sahip oyunlarda `positive_ratio >= 0.8` → 1, değilse 0 (eşiği ve sınıf dengesini raporla).
- **Veri sızıntısına (data leakage) çok dikkat et:** Sadece çıkıştan **önce** bilinebilecek özellikleri kullan: fiyat, türler, etiketler, kategoriler, diller, platformlar, başarım sayısı, DLC sayısı, açıklama uzunluğu, çıkış ayı/yılı, yaş sınırı, yayıncılı olup olmaması. Review sayıları, sahip sayısı, oynama süresi, Peak CCU, Metacritic gibi çıkış sonrası metrikleri **kullanma**. Kullanılan ve dışlanan özellikleri tablo halinde yaz.
- Train/test ayrımını tercihen zamana göre yap (eski oyunlarla eğit, yenilerle test et) ve rastgele ayrımla karşılaştır.
- Modeller:
  1. Baseline (her zaman çoğunluk sınıfını tahmin eden)
  2. Logistic Regression
  3. Random Forest
  4. XGBoost veya LightGBM
- Metrikler: accuracy, precision, recall, F1, ROC-AUC; confusion matrix ve ROC eğrisi.
- En iyi model için SHAP ile özellik önemleri: hangi özellikler başarıyı artırıyor/azaltıyor?
- Sonuçları gerçekçi yorumla: model düşük performans gösterirse bu da bir bulgudur ("çıkış öncesi özellikler başarıyı sınırlı ölçüde açıklıyor" gibi).

### Faz 6 — Rapor ve README

**`reports/RAPOR.md`:**
- Özet (5–7 maddelik en önemli bulgular)
- Veri ve yöntem
- Her analiz bölümünün bulguları + ilgili grafikler (göreli yollarla gömülü)
- Model sonuçları
- **"Bir indie geliştiriciye öneriler"** bölümü: bulgulara dayanan somut, uygulanabilir tavsiyeler
- Sınırlılıklar (sahip sayısının tahmini aralık olması, review'u olmayan oyunlar, korelasyon ≠ nedensellik, verinin belirli bir tarihte alınmış olması vb.)

**`README.md`:** Proje amacı, öne çıkan 3–4 grafik, ana bulgular, kurulum ve çalıştırma adımları, klasör yapısı. Portfolyoda/GitHub'da şık dursun.

## 5. Kurallar

- Kolon isimlerini, değer formatlarını ve veri boyutunu **asla varsayma**; her zaman önce veriye bakarak doğrula.
- Notebook'lar baştan sona hatasız çalışmalı (`Restart & Run All`). Bir faz bitince bunu kontrol et.
- Grafiklerde: başlık, eksen isimleri ve birimler Türkçe olsun; tutarlı bir stil ve renk paleti kullan (`src/plots.py` içinde tanımla); çarpık verilerde log ölçek kullan.
- Her grafiğin ve önemli tablonun altında kısa bir yorum olsun. Sadece kod değil, **hikâye** anlat.
- Rastgelelik içeren her işlemde `random_state=42` kullan.
- Veri büyük olabilir; bellek kullanımına dikkat et (gereksiz kolonları at, uygun dtype'lar kullan, metin kolonlarını sadece gerektiğinde yükle).
- Kodda yorumlar ve markdown açıklamaları Türkçe olabilir; değişken ve fonksiyon isimleri İngilizce olsun.
- Bir karar verirken (eşik, filtre, yöntem) kısaca gerekçesini yaz.
- Emin olmadığın veya benim tercihimi gerektiren bir konu olursa tahmin etmek yerine bana sor.
