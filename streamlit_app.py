"""
=============================================================================
Streamlit Web Arayüzü
Streamlit Web Interface
=============================================================================
Kullanıcının:
1. Tek bir .wav dosyası yükleyip tahmin görmesini
2. Ses özelliklerini (F0, ZCR, enerji) görselleştirmesini
3. Tüm veri seti üzerindeki başarıyı incelemesini sağlar.

Çalıştırma / Run:
    streamlit run app/streamlit_app.py
=============================================================================
"""

import os
import sys
import io
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Streamlit — gerekli kütüphane
try:
    import streamlit as st
except ImportError:
    print("streamlit not installed. Run: pip install streamlit")
    sys.exit(1)

# Proje modüllerini import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.feature_extraction import (
    load_audio, frame_signal,
    compute_short_time_energy, compute_zcr,
    detect_voiced_frames,
    estimate_f0_autocorrelation, estimate_f0_fft,
    compute_autocorrelation_fast, extract_features
)
from src.classifier  import classify_gender, compute_metrics
from src.visualizer  import (
    plot_full_analysis, plot_autocorrelation_vs_fft,
    plot_confusion_matrix
)

# ======================================================================
# SAYFA KONFİGÜRASYONU / PAGE CONFIGURATION
# ======================================================================
st.set_page_config(
    page_title="🎙️ Ses Cinsiyet Sınıflandırıcı",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================================
# YARDIMCI FONKSİYONLAR / HELPER FUNCTIONS
# ======================================================================

def fig_to_bytes(fig: plt.Figure) -> bytes:
    """Matplotlib figürünü PNG bytes'a dönüştürür."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf.read()


@st.cache_data(show_spinner=False)
def analyze_audio_bytes(audio_bytes: bytes, sr: int = 16000) -> dict:
    """Yüklenen ses dosyasını analiz eder (cache'li)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        features = extract_features(tmp_path, sr=sr)
        features["tmp_path"] = tmp_path
        return features
    finally:
        pass  # tmp dosyayı analiz sonrası tutuyoruz


def gender_emoji(gender: str) -> str:
    emojis = {"Erkek": "👨", "Kadın": "👩", "Çocuk": "🧒"}
    return emojis.get(gender, "❓")


def confidence_color(conf: float) -> str:
    if conf >= 0.80: return "green"
    if conf >= 0.60: return "orange"
    return "red"


# ======================================================================
# ANA UYGULAMA / MAIN APP
# ======================================================================

def main():

    # ---- SIDEBAR ----
    with st.sidebar:
        st.image("https://img.icons8.com/nolan/96/microphone.png", width=80)
        st.title("⚙️ Ayarlar / Settings")

        sr = st.selectbox(
            "Örnekleme Hızı / Sample Rate",
            options=[8000, 16000, 22050, 44100],
            index=1
        )

        st.markdown("---")
        st.subheader("📊 F0 Eşik Değerleri / Thresholds")
        male_max  = st.slider("Erkek maks. F0 (Hz)", 100, 220, 180)
        child_min = st.slider("Çocuk min. F0 (Hz)",  180, 400, 240)
        st.caption(f"Kadın bölgesi: {male_max}–{child_min} Hz arası")

        st.markdown("---")
        st.markdown(
            "**Proje:** Dönemiçi Proje  \n"
            "**Ders:** Ses İşleme  \n"
            "**Dönem:** 2025-2026 Bahar"
        )

    # ---- BAŞLIK / HEADER ----
    st.markdown(
        "<h1 style='text-align:center; color:#1565C0;'>"
        "🎙️ Ses Cinsiyet Sınıflandırıcı</h1>"
        "<p style='text-align:center; color:#555;'>"
        "Otokorelasyon tabanlı F0 analizi ile Erkek / Kadın / Çocuk tespiti</p>"
        "<hr>",
        unsafe_allow_html=True
    )

    # ---- SEKME YAPISI / TABS ----
    tab1, tab2, tab3 = st.tabs([
        "🎵 Tekil Analiz / Single File",
        "📊 Veri Seti Analizi / Dataset",
        "ℹ️ Yöntem / Methodology"
    ])

    # ==================================================================
    # SEKME 1: TEKİL DOSYA ANALİZİ
    # ==================================================================
    with tab1:
        st.subheader("Ses Dosyası Yükle / Upload Audio File")

        uploaded = st.file_uploader(
            "Bir .wav dosyası seçin / Select a .wav file",
            type=["wav"],
            help="WAV formatında ses dosyası yükleyin (mono veya stereo)"
        )

        if uploaded is not None:
            audio_bytes = uploaded.read()
            st.audio(audio_bytes, format="audio/wav")

            with st.spinner("🔍 Analiz ediliyor / Analyzing..."):
                features = analyze_audio_bytes(audio_bytes, sr=sr)

            if "error" in features and features.get("f0_mean", 0) == 0:
                st.error(f"❌ Analiz hatası: {features.get('error')}")
            else:
                # Özel eşiklerle sınıflandır
                from src.classifier import THRESHOLDS
                orig_male_max  = THRESHOLDS["f0_male_max"]
                orig_child_min = THRESHOLDS["f0_child_min"]
                THRESHOLDS["f0_male_max"]   = float(male_max)
                THRESHOLDS["f0_child_min"]  = float(child_min)
                THRESHOLDS["f0_female_min"] = float(male_max) - 25
                THRESHOLDS["f0_female_max"] = float(child_min) + 20

                pred, conf, reason = classify_gender(features)

                THRESHOLDS["f0_male_max"]  = orig_male_max
                THRESHOLDS["f0_child_min"] = orig_child_min

                # ---- SONUÇ KARTI / RESULT CARD ----
                col1, col2, col3 = st.columns([1.5, 1, 1])

                with col1:
                    st.markdown(
                        f"<div style='background:#E3F2FD;border-radius:12px;"
                        f"padding:20px;text-align:center;'>"
                        f"<h2>{gender_emoji(pred)}</h2>"
                        f"<h1 style='color:#1565C0;'>{pred}</h1>"
                        f"<p style='color:{confidence_color(conf)};font-size:18px;'>"
                        f"Güven / Confidence: <b>{conf*100:.0f}%</b></p>"
                        f"<p style='font-size:12px;color:#666;'>{reason}</p>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                with col2:
                    st.metric("🎵 Ortalama F0",
                              f"{features.get('f0_mean', 0):.1f} Hz",
                              delta=None)
                    st.metric("📊 F0 Std Dev",
                              f"{features.get('f0_std', 0):.1f} Hz")
                    st.metric("⏱️ Süre / Duration",
                              f"{features.get('duration', 0):.2f} s")

                with col3:
                    st.metric("〰️ ZCR Ortalama",
                              f"{features.get('zcr_mean', 0):.0f} Hz")
                    st.metric("⚡ Enerji Ort.",
                              f"{features.get('energy_mean', 0):.4f}")
                    voiced_pct = features.get("voiced_ratio", 0) * 100
                    st.metric("🔊 Sesli Oran",
                              f"{voiced_pct:.1f}%")

                st.markdown("---")

                # ---- GRAFİKLER / PLOTS ----
                if os.path.exists(features.get("tmp_path", "")):
                    try:
                        audio, sr_loaded = load_audio(features["tmp_path"], sr)
                        frames, fl, hl = frame_signal(audio, sr_loaded)
                        ste   = compute_short_time_energy(frames)
                        zcr_v = compute_zcr(frames, sr_loaded)
                        voiced= detect_voiced_frames(ste, zcr_v)

                        col_plot1, col_plot2 = st.columns(2)

                        with col_plot1:
                            st.subheader("📈 Sinyal Analizi")
                            fig = plot_full_analysis(
                                audio=audio, sr=sr_loaded,
                                energy=ste, zcr=zcr_v,
                                voiced_mask=voiced,
                                frames=frames, hop_length=hl,
                                title=f"Signal Analysis — {uploaded.name}"
                            )
                            st.image(fig_to_bytes(fig))

                        with col_plot2:
                            st.subheader("📉 Otokorelasyon vs FFT")
                            # En sesli çerçeveyi bul
                            if np.sum(voiced) > 0:
                                vi = np.where(voiced)[0]
                                bf = vi[np.argmax(ste[vi])]
                                sample_frame = frames[bf]
                            else:
                                sample_frame = frames[np.argmax(ste)]

                            acf = compute_autocorrelation_fast(sample_frame)
                            f0_acr = estimate_f0_autocorrelation(sample_frame, sr_loaded)
                            f0_fft = estimate_f0_fft(sample_frame, sr_loaded)

                            fig2 = plot_autocorrelation_vs_fft(
                                frame=sample_frame, sr=sr_loaded,
                                acf=acf, f0_autocorr=f0_acr, f0_fft=f0_fft,
                                title="Autocorrelation vs FFT"
                            )
                            st.image(fig_to_bytes(fig2))

                        st.info(
                            f"**Otokorelasyon F0:** {f0_acr:.1f} Hz  |  "
                            f"**FFT F0:** {f0_fft:.1f} Hz  |  "
                            f"**Fark / Diff:** {abs(f0_acr-f0_fft):.1f} Hz"
                        )

                    except Exception as e:
                        st.warning(f"Plot oluşturulamadı / Plot failed: {e}")

    # ==================================================================
    # SEKME 2: VERİ SETİ ANALİZİ
    # ==================================================================
    with tab2:
        st.subheader("📂 Veri Seti Yükle / Load Dataset")
        dataset_path = st.text_input(
            "Dataset klasör yolu / Dataset folder path",
            value="Dataset",
            help="Tüm Grup_XX klasörlerinin bulunduğu ana dizin"
        )

        if st.button("🚀 Analizi Başlat / Run Analysis", type="primary"):
            with st.spinner("Veri seti analiz ediliyor..."):
                from src.dataset_loader import load_all_metadata
                from main import process_single_file

                df = load_all_metadata(dataset_path)
                results = []
                prog = st.progress(0)
                for i, (_, row) in enumerate(df.iterrows()):
                    results.append(process_single_file(row, sr=sr))
                    prog.progress((i + 1) / len(df))

                df_res = pd.DataFrame(results)
                st.session_state["df_results"] = df_res

        if "df_results" in st.session_state:
            df_res = st.session_state["df_results"]

            valid = df_res[
                (df_res["Cinsiyet"].isin(["Erkek","Kadın","Çocuk"])) &
                (df_res["prediction"] != "Unknown")
            ]

            if len(valid) > 0:
                metrics = compute_metrics(
                    valid["prediction"].tolist(),
                    valid["Cinsiyet"].tolist()
                )

                # Özet metrikler
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🎯 Doğruluk / Accuracy",
                          f"{metrics['overall_accuracy']*100:.1f}%")
                c2.metric("📁 Toplam Kayıt", len(df_res))
                c3.metric("✅ Doğru Tahmin", valid["correct"].sum())
                c4.metric("❌ Yanlış Tahmin",
                          len(valid) - valid["correct"].sum())

                # Detaylı tablo
                st.subheader("📊 Sınıf Bazlı Sonuçlar")
                class_data = []
                for cls in ["Erkek", "Kadın", "Çocuk"]:
                    pc = metrics["per_class"].get(cls, {})
                    subset = valid[valid["Cinsiyet"] == cls]
                    class_data.append({
                        "Sınıf": cls,
                        "Örnek Sayısı": pc.get("support", 0),
                        "Ort. F0 (Hz)": f"{subset['f0_mean'].mean():.1f}" if "f0_mean" in subset else "N/A",
                        "Std F0": f"{subset['f0_mean'].std():.1f}" if "f0_mean" in subset else "N/A",
                        "Başarı (%)": f"{pc.get('recall',0)*100:.1f}%",
                        "Precision": f"{pc.get('precision',0)*100:.1f}%",
                        "F1": f"{pc.get('f1_score',0):.3f}",
                    })
                st.dataframe(pd.DataFrame(class_data), use_container_width=True)

                # Karışıklık matrisi
                st.subheader("🔢 Karışıklık Matrisi / Confusion Matrix")
                fig_cm = plot_confusion_matrix(
                    metrics["confusion_matrix"],
                    metrics["class_labels"],
                    metrics["overall_accuracy"]
                )
                st.image(fig_to_bytes(fig_cm))

                # Ham sonuçlar
                with st.expander("📋 Tüm Tahminler / All Predictions"):
                    display_cols = ["Dosya_Path", "Cinsiyet", "prediction",
                                    "confidence", "f0_mean", "zcr_mean", "correct"]
                    available = [c for c in display_cols if c in df_res.columns]
                    st.dataframe(df_res[available], use_container_width=True)

    # ==================================================================
    # SEKME 3: YÖNTEMBİLGİSİ
    # ==================================================================
    with tab3:
        st.subheader("📚 Yöntem / Methodology")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
### 🔊 İşlem Akışı

1. **Ses Yükleme** — WAV → mono float32, 16 kHz
2. **Pencereleme** — 25 ms Hann pencere, 10 ms atlama
3. **Kısa Süreli Enerji** — `E[n] = Σ x²[m]`
4. **Sıfır Geçiş Oranı** — `ZCR = crossings / duration`
5. **Sesli/Sessiz Ayrımı** — Enerji + ZCR eşiği
6. **Otokorelasyon** — `R[τ] = Σ x[n] · x[n-τ]`
7. **F0 Tespiti** — R(τ)'da tepe → `f0 = sr / τ`
8. **Kural Tabanlı Sınıflandırma** — F0 eşikleri
            """)

        with col2:
            st.markdown("""
### 📏 F0 Eşikleri (Varsayılan)

| Sınıf | F0 Aralığı | Tipik Ort. |
|-------|-----------|------------|
| **Erkek** | 60 – 180 Hz | ~120 Hz |
| **Kadın** | 155 – 260 Hz | ~210 Hz |
| **Çocuk** | 240 – 500 Hz | ~300 Hz |

### 📖 Referanslar

- Titze (1994). *Principles of Voice Production*
- Hollien & Shipp (1972). *J. Speech Hear. Res.*
- Rabiner & Schafer (2010). *Theory and Applications of DSP*
            """)

        st.markdown("---")
        st.markdown("""
### 🧮 Otokorelasyon Formülü

$$R[\\tau] = \\sum_{n=0}^{N-\\tau-1} x[n] \\cdot x[n-\\tau]$$

Periyodik bir sinyalde, $\\tau = T$ (periyot) değerinde maksimum oluşur.
Temel frekans: $F_0 = \\frac{f_s}{\\tau_{peak}}$

### ⚡ Hızlı Hesaplama (FFT tabanlı)

$$R[\\tau] = \\mathcal{F}^{-1}\\{|X(f)|^2\\}$$
        """)


if __name__ == "__main__":
    main()
