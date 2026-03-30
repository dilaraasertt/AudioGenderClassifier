"""
=============================================================================
Görselleştirme Modülü
Visualization Module
=============================================================================
Dalga formu, enerji, ZCR, otokorelasyon, FFT spektrumu ve
karışıklık matrisi grafiklerini üretir.

Produces waveform, energy, ZCR, autocorrelation, FFT spectrum,
and confusion matrix plots.
=============================================================================
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend (Streamlit/server uyumlu)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import seaborn as sns
from typing import Optional
import os

# Stil ayarları / Style settings
plt.rcParams.update({
    "font.family"     : "DejaVu Sans",
    "axes.spines.top" : False,
    "axes.spines.right": False,
    "axes.grid"       : True,
    "grid.alpha"      : 0.3,
    "figure.dpi"      : 100,
})

COLOR_MALE   = "#2196F3"   # Mavi / Blue
COLOR_FEMALE = "#E91E63"   # Pembe / Pink
COLOR_CHILD  = "#4CAF50"   # Yeşil / Green
COLOR_VOICED = "#FF9800"   # Turuncu / Orange

CLASS_COLORS = {"Erkek": COLOR_MALE, "Kadın": COLOR_FEMALE, "Çocuk": COLOR_CHILD}


# =============================================================================
# BÖLÜM 1: TEK DOSYA ANALİZ PANELİ / SINGLE FILE ANALYSIS PANEL
# =============================================================================

def plot_full_analysis(audio: np.ndarray, sr: int,
                       energy: np.ndarray, zcr: np.ndarray,
                       voiced_mask: np.ndarray,
                       frames: np.ndarray,
                       hop_length: int,
                       title: str = "Audio Analysis",
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Bir ses dosyası için tam analiz paneli oluşturur (4 alt grafik).
    Creates a full analysis panel for one audio file (4 subplots).
    """
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # Zaman ekseni (ses)
    t_audio = np.linspace(0, len(audio) / sr, len(audio))

    # Çerçeve zaman ekseni
    t_frames = np.arange(len(energy)) * hop_length / sr

    # ----------------------------------------------------------------
    # 1. Dalga Formu / Waveform
    # ----------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t_audio, audio, color="#37474F", linewidth=0.5, alpha=0.85)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Waveform (Dalga Formu)")

    # Sesli bölgeleri vurgula / Highlight voiced regions
    voiced_indices = np.where(voiced_mask)[0]
    if len(voiced_indices) > 0:
        for idx in voiced_indices:
            t_start = idx * hop_length / sr
            t_end   = t_start + hop_length / sr
            ax1.axvspan(t_start, t_end, color=COLOR_VOICED, alpha=0.15)

    ax1.set_xlim([0, t_audio[-1]])

    # ----------------------------------------------------------------
    # 2. Kısa Süreli Enerji / Short-Time Energy
    # ----------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.fill_between(t_frames, energy, color="#FF5722", alpha=0.7, label="STE")
    energy_thresh = np.max(energy) * 0.05
    ax2.axhline(energy_thresh, color="red", linestyle="--", linewidth=1.2,
                label=f"Threshold={energy_thresh:.2e}")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Energy")
    ax2.set_title("Short-Time Energy (Kısa Süreli Enerji)")
    ax2.legend(fontsize=8)

    # ----------------------------------------------------------------
    # 3. Sıfır Geçiş Oranı / Zero Crossing Rate
    # ----------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(t_frames, zcr, color="#9C27B0", linewidth=1.0, label="ZCR")
    ax3.axhline(3000, color="green", linestyle="--", linewidth=1.2,
                label="Voice threshold (3000 Hz)")
    ax3.fill_between(t_frames, zcr,
                     where=voiced_mask[:len(t_frames)],
                     alpha=0.3, color=COLOR_VOICED, label="Voiced")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("ZCR (crossings/sec)")
    ax3.set_title("Zero Crossing Rate (Sıfır Geçiş Oranı)")
    ax3.legend(fontsize=8)

    # ----------------------------------------------------------------
    # 4. Sesli Bölge Oranı Bar Grafik / Voiced Frame Statistics
    # ----------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    voiced_ratio = np.sum(voiced_mask) / len(voiced_mask) * 100
    unvoiced_ratio = 100 - voiced_ratio
    bars = ax4.bar(["Voiced", "Unvoiced"],
                   [voiced_ratio, unvoiced_ratio],
                   color=[COLOR_VOICED, "#90A4AE"],
                   edgecolor="white", linewidth=1.5, width=0.5)
    for bar, val in zip(bars, [voiced_ratio, unvoiced_ratio]):
        ax4.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1,
                 f"{val:.1f}%",
                 ha="center", fontsize=11, fontweight="bold")
    ax4.set_ylabel("Frame Percentage (%)")
    ax4.set_title("Voiced / Unvoiced Frame Distribution")
    ax4.set_ylim([0, 120])
    ax4.grid(False)

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


# =============================================================================
# BÖLÜM 2: OTOKORELASYONla FFT KARŞILAŞTIRMASI
# =============================================================================

def plot_autocorrelation_vs_fft(frame: np.ndarray, sr: int,
                                 acf: np.ndarray,
                                 f0_autocorr: float,
                                 f0_fft: float,
                                 title: str = "Autocorrelation vs FFT",
                                 save_path: Optional[str] = None) -> plt.Figure:
    """
    Otokorelasyon grafiği ve FFT spektrumunu yan yana gösterir.
    Shows autocorrelation and FFT spectrum side by side.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(title, fontsize=13, fontweight="bold")

    n = len(frame)
    lags = np.arange(n) / sr * 1000  # milisaniye cinsinden

    # ----------------------------------------------------------------
    # Sol: Otokorelasyon Fonksiyonu
    # ----------------------------------------------------------------
    ax = axes[0]
    ax.plot(lags[:n // 2], acf[:n // 2], color="#1565C0", linewidth=1.2)
    ax.set_xlabel("Lag (ms)")
    ax.set_ylabel("Autocorrelation R(τ)")
    ax.set_title("Autocorrelation Function R(τ)\n(Otokorelasyon Fonksiyonu)")

    if f0_autocorr > 0:
        period_ms = 1000.0 / f0_autocorr
        if period_ms < lags[n // 2 - 1]:
            ax.axvline(period_ms, color="red", linestyle="--", linewidth=1.5,
                       label=f"F0 = {f0_autocorr:.1f} Hz (T={period_ms:.2f} ms)")
            ax.legend(fontsize=9)

    # ----------------------------------------------------------------
    # Sağ: FFT Spektrumu
    # ----------------------------------------------------------------
    ax = axes[1]
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    X = np.fft.rfft(frame * np.hanning(n))
    magnitude = np.abs(X)

    # Yalnızca 0-600 Hz göster / Show only 0-600 Hz
    mask_600 = freqs <= 600
    ax.plot(freqs[mask_600], magnitude[mask_600], color="#880E4F", linewidth=1.2)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("|X(f)|  Magnitude")
    ax.set_title("FFT Magnitude Spectrum |X(f)|\n(0–600 Hz region)")

    if f0_fft > 0:
        ax.axvline(f0_fft, color="red", linestyle="--", linewidth=1.5,
                   label=f"F0 (FFT) = {f0_fft:.1f} Hz")
        ax.legend(fontsize=9)

    if f0_autocorr > 0:
        ax.axvline(f0_autocorr, color="blue", linestyle=":", linewidth=1.5,
                   label=f"F0 (Autocorr) = {f0_autocorr:.1f} Hz")
        ax.legend(fontsize=9)

    fig.text(0.5, 0.01,
             f"F0 via Autocorrelation: {f0_autocorr:.1f} Hz   |   "
             f"F0 via FFT: {f0_fft:.1f} Hz   |   "
             f"Difference: {abs(f0_autocorr - f0_fft):.1f} Hz",
             ha="center", fontsize=10, color="navy",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#E3F2FD"))

    plt.tight_layout(rect=[0, 0.06, 1, 0.95])

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


# =============================================================================
# BÖLÜM 3: F0 DAĞILIM GRAFİKLERİ / F0 DISTRIBUTION PLOTS
# =============================================================================

def plot_f0_distributions(df, save_path: Optional[str] = None) -> plt.Figure:
    """
    Her cinsiyet sınıfı için F0 dağılımını gösterir (violin + box plot).
    Shows F0 distribution per gender class (violin + box plot).
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("F0 (Pitch) Distribution by Gender Class\n"
                 "Cinsiyet Sınıflarına Göre F0 Dağılımı",
                 fontsize=13, fontweight="bold")

    classes = ["Erkek", "Kadın", "Çocuk"]
    colors  = [COLOR_MALE, COLOR_FEMALE, COLOR_CHILD]

    # Veriyi hazırla / Prepare data
    data_by_class = []
    for cls in classes:
        subset = df[df["Cinsiyet"] == cls]["f0_mean"].dropna()
        subset = subset[subset > 50]  # F0 > 50 Hz filtrele
        data_by_class.append(subset.values)

    # Sol: Violin Plot
    ax = axes[0]
    parts = ax.violinplot(data_by_class, positions=[1, 2, 3],
                          showmeans=True, showmedians=True)
    for i, (pc, color) in enumerate(zip(parts["bodies"], colors)):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
    parts["cmeans"].set_color("black")
    parts["cmedians"].set_color("white")

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(classes, fontsize=11)
    ax.set_xlabel("Gender Class (Cinsiyet Sınıfı)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title("Violin Plot")

    # Eşik çizgileri / Threshold lines
    ax.axhline(180, color="gray", linestyle="--", linewidth=1, alpha=0.7,
               label="Male/Female boundary (180 Hz)")
    ax.axhline(240, color="gray", linestyle="-.", linewidth=1, alpha=0.7,
               label="Female/Child boundary (240 Hz)")
    ax.legend(fontsize=8)

    # Sağ: Box Plot
    ax = axes[1]
    bp = ax.boxplot(data_by_class, labels=classes, patch_artist=True,
                    notch=False, showfliers=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xlabel("Gender Class (Cinsiyet Sınıfı)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title("Box Plot")
    ax.axhline(180, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.axhline(240, color="gray", linestyle="-.", linewidth=1, alpha=0.7)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


# =============================================================================
# BÖLÜM 4: KARIŞIKLIK MATRİSİ / CONFUSION MATRIX
# =============================================================================

def plot_confusion_matrix(cm: list, class_labels: list,
                           accuracy: float,
                           save_path: Optional[str] = None) -> plt.Figure:
    """
    Karışıklık matrisini ısı haritası olarak çizer.
    Plots the confusion matrix as a heatmap.
    """
    cm_arr = np.array(cm)
    n = len(class_labels)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Confusion Matrix  |  Overall Accuracy: {accuracy*100:.1f}%",
                 fontsize=13, fontweight="bold")

    # Sol: Ham sayılar / Left: Raw counts
    ax = axes[0]
    sns.heatmap(cm_arr, annot=True, fmt="d", cmap="Blues",
                xticklabels=class_labels, yticklabels=class_labels,
                linewidths=0.5, linecolor="white", ax=ax)
    ax.set_xlabel("Predicted (Tahmin)", fontsize=11)
    ax.set_ylabel("Actual (Gerçek)", fontsize=11)
    ax.set_title("Count")

    # Sağ: Normalize edilmiş / Right: Normalized (row %)
    ax = axes[1]
    row_sums = cm_arr.sum(axis=1, keepdims=True)
    cm_norm  = np.where(row_sums > 0, cm_arr / row_sums, 0)
    sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Greens",
                xticklabels=class_labels, yticklabels=class_labels,
                linewidths=0.5, linecolor="white", ax=ax,
                vmin=0, vmax=1)
    ax.set_xlabel("Predicted (Tahmin)", fontsize=11)
    ax.set_ylabel("Actual (Gerçek)", fontsize=11)
    ax.set_title("Normalized (Row %)")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


# =============================================================================
# BÖLÜM 5: SONUÇ ÖZET TABLOSU / RESULTS SUMMARY TABLE
# =============================================================================

def plot_results_table(metrics: dict, save_path: Optional[str] = None) -> plt.Figure:
    """
    Sınıf bazlı başarı özet tablosunu grafik olarak gösterir.
    Displays the per-class performance summary as a table figure.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")

    classes = ["Erkek", "Kadın", "Çocuk"]
    per_class = metrics.get("per_class", {})

    headers = ["Class", "Samples", "Avg F0 (Hz)", "Std F0", "Recall (%)", "Precision (%)", "F1"]
    rows = []
    for cls in classes:
        pc = per_class.get(cls, {})
        rows.append([
            cls,
            str(pc.get("support", "N/A")),
            "–",  # F0 from separate feature dict
            "–",
            f"{pc.get('recall', 0)*100:.1f}%",
            f"{pc.get('precision', 0)*100:.1f}%",
            f"{pc.get('f1_score', 0):.3f}",
        ])

    tbl = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1]
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    # Başlık satırı rengi / Header row color
    for j in range(len(headers)):
        tbl[(0, j)].set_facecolor("#1565C0")
        tbl[(0, j)].set_text_props(color="white", fontweight="bold")

    # Sınıf renklerini uygula / Apply class colors
    for i, (row, cls) in enumerate(zip(rows, classes)):
        color = CLASS_COLORS.get(cls, "#EEEEEE")
        for j in range(len(headers)):
            tbl[(i + 1, j)].set_facecolor(color + "33")  # 33 = ~20% opacity

    ax.set_title(
        f"Classification Results Summary  |  "
        f"Overall Accuracy: {metrics.get('overall_accuracy', 0)*100:.1f}%",
        fontsize=12, fontweight="bold", pad=10
    )

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig
