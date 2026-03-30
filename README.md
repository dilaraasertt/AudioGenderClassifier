# 🎙️ Ses İşareti Analizi ve Cinsiyet Sınıflandırma
## Audio Signal Analysis & Gender Classification
### 2025-2026 Bahar Dönemi — Dönemiçi Proje

---

## 📁 Proje Dosya Yapısı / Project Structure

```
AudioGenderClassifier/
│
├── 📂 Dataset/                    ← Ses veri seti (siz oluşturacaksınız)
│   ├── Grup_01/
│   │   ├── metadata_Grup01.xlsx   ← Dosya adı, cinsiyet, yaş
│   │   ├── E01_kayit1.wav
│   │   ├── K01_kayit1.wav
│   │   └── ...
│   ├── Grup_02/
│   └── Grup_03/
│
├── 📂 src/                        ← Çekirdek modüller / Core modules
│   ├── feature_extraction.py      ← Ses yükleme, pencereleme, STE, ZCR, F0
│   ├── classifier.py              ← Kural tabanlı sınıflandırıcı
│   ├── dataset_loader.py          ← Veri seti yönetimi, metadata birleştirme
│   └── visualizer.py              ← Grafik üretim modülü
│
├── 📂 app/
│   └── streamlit_app.py           ← Web arayüzü (Streamlit)
│
├── 📂 notebooks/
│   └── AudioAnalysis_Pipeline.ipynb  ← Jupyter Notebook (tam pipeline)
│
├── 📂 results/                    ← Otomatik oluşturulur
│   ├── feature_results.csv
│   ├── signal_analysis.png
│   ├── autocorrelation_vs_fft.png
│   ├── f0_distributions.png
│   ├── confusion_matrix.png
│   └── results_table.png
│
├── main.py                        ← Ana çalıştırma scripti
└── README.md                      ← Bu dosya
```

---

## Kurulum ve Çalıştırma / Setup & Run

### Gereksinimler / Requirements
```bash
pip install numpy scipy pandas matplotlib seaborn scikit-learn
pip install streamlit          # Web arayüzü için
pip install jupyter            # Notebook için
```

### 1. Veri Seti Hazırlama / Dataset Preparation

Her grup kendi klasörünü şu yapıyla oluşturur:
```
Dataset/
  Grup_01/
    metadata_Grup01.xlsx   (sütunlar: Dosya_Adı, Cinsiyet, Yaş)
    ses_erkek_01.wav
    ses_kadin_01.wav
    ses_cocuk_01.wav
    ...
```

Excel sütun isimleri esnek tanınır:
- Cinsiyet: `Cinsiyet`, `Gender`, `Sex`, `Cins`
- Yaş: `Yaş`, `Yas`, `Age`
- Dosya: `Dosya_Adı`, `Path`, `File`, `WAV`

### 2. Tam Pipeline Çalıştırma
```bash
cd AudioGenderClassifier
python main.py --dataset Dataset --output results
```

### 3. Web Arayüzü
```bash
streamlit run app/streamlit_app.py
```

### 4. Jupyter Notebook
```bash
jupyter notebook notebooks/AudioAnalysis_Pipeline.ipynb
```

---

## Kullanılan Yöntemler / Methods

### Pencereleme (Windowing)
- **Çerçeve süresi:** 25 ms (durağanlık varsayımı için)
- **Atlama adımı:** 10 ms (%60 örtüşme)
- **Pencere tipi:** Hann penceresi (spektral sızıntıyı azaltır)

### Kısa Süreli Enerji (STE)
```
E[n] = Σ x²[m]
```

### Sıfır Geçiş Oranı (ZCR)
```
ZCR = (1/2T) × Σ |sgn(x[n]) - sgn(x[n-1])|
```

### Otokorelasyon Tabanlı F0
```
R[τ] = Σ x[n] × x[n-τ]
F0 = sr / τ_peak
```

---

## F0 Eşik Değerleri / Thresholds

| Sınıf | F0 Aralığı | Literatür Referansı |
|-------|-----------|---------------------|
| **Erkek** | 60–180 Hz | Titze (1994) |
| **Kadın** | 155–260 Hz | Hollien & Shipp (1972) |
| **Çocuk** | 240–500 Hz | Awan (2001) |

---

## 📚 Referanslar / References

1. Titze, I.R. (1994). *Principles of Voice Production*. Prentice Hall.
2. Hollien, H. & Shipp, T. (1972). *Speaking fundamental frequency and chronological age in males*. JSHR.
3. Awan, S.N. (2001). *The Voice Diagnostic Protocol*. Aspen Publishers.
4. Rabiner, L. & Schafer, R. (2010). *Theory and Applications of Digital Speech Processing*. Pearson.
5. Huang, X. et al. (2001). *Spoken Language Processing*. Prentice Hall.
