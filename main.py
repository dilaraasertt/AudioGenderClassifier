"""
=============================================================================
Ana Çalıştırma Scripti — Tam Pipeline
Main Runner Script — Full Pipeline
=============================================================================
Bu script tüm veri seti üzerinde tam analizi çalıştırır:
1. Veri seti yükleme
2. Öznitelik çıkarımı (otokorelasyon)
3. Kural tabanlı sınıflandırma
4. Başarı analizi & görselleştirme

Usage:
    python main.py --dataset Dataset/ --output results/
=============================================================================
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Proje modüllerini import et / Import project modules
sys.path.insert(0, os.path.dirname(__file__))
from src.dataset_loader   import load_all_metadata, print_dataset_summary
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
    plot_f0_distributions, plot_confusion_matrix,
    plot_results_table
)


# =============================================================================
# YARDIMCI FONKSİYONLAR / HELPER FUNCTIONS
# =============================================================================

def process_single_file(row: pd.Series, sr: int = 16000) -> dict:
    """
    Tek bir satır (dosya) için tüm öznitelikleri çıkarır ve sınıflandırır.
    """
    filepath = str(row.get("Dosya_Path", ""))
    result   = {"Dosya_Path": filepath,
                "Cinsiyet"  : row.get("Cinsiyet", "Unknown"),
                "Yas"       : row.get("Yas", None),
                "Grup"      : row.get("Grup", "Unknown")}

    if not os.path.exists(filepath):
        result.update({"error": "File not found",
                        "prediction": "Unknown", "confidence": 0.0})
        return result

    # Öznitelik çıkarımı
    features = extract_features(filepath, sr=sr)
    result.update(features)

    # Sınıflandır
    pred, conf, reason = classify_gender(features)
    result["prediction"] = pred
    result["confidence"] = conf
    result["reasoning"]  = reason
    result["correct"]    = (pred == result["Cinsiyet"])

    return result


def generate_comparison_plot(df_results: pd.DataFrame,
                              output_dir: str,
                              sr: int = 16000):
    """
    Örnek bir ses kaydı için otokorelasyon vs FFT karşılaştırma grafiği üretir.
    """
    # İlk geçerli sesli dosyayı seç
    voiced_rows = df_results[df_results.get("voiced_ratio", 0) > 0.2
                             if "voiced_ratio" in df_results.columns
                             else df_results.index >= 0]

    if len(voiced_rows) == 0:
        voiced_rows = df_results

    sample_row = voiced_rows.iloc[0]
    filepath = str(sample_row.get("Dosya_Path", ""))

    if not os.path.exists(filepath):
        print("[WARNING] No valid audio file found for comparison plot.")
        return

    try:
        audio, sr = load_audio(filepath, target_sr=sr)
        frames, frame_len, hop_len = frame_signal(audio, sr)
        energy = compute_short_time_energy(frames)
        zcr    = compute_zcr(frames, sr)
        voiced = detect_voiced_frames(energy, zcr)

        # En sesli çerçeveyi al
        if np.sum(voiced) > 0:
            voiced_idx   = np.where(voiced)[0]
            best_frame_i = voiced_idx[np.argmax(energy[voiced_idx])]
            sample_frame = frames[best_frame_i]
        else:
            energy_order = np.argsort(energy)[::-1]
            sample_frame = frames[energy_order[0]]

        # Otokorelasyon & FFT hesapla
        acf          = compute_autocorrelation_fast(sample_frame)
        f0_autocorr  = estimate_f0_autocorrelation(sample_frame, sr)
        f0_fft       = estimate_f0_fft(sample_frame, sr)

        gender = sample_row.get("Cinsiyet", "?")
        fig = plot_autocorrelation_vs_fft(
            frame=sample_frame, sr=sr,
            acf=acf,
            f0_autocorr=f0_autocorr,
            f0_fft=f0_fft,
            title=f"Autocorrelation vs FFT Comparison — {gender} Voice ({os.path.basename(filepath)})"
        )
        out_path = os.path.join(output_dir, "autocorrelation_vs_fft.png")
        fig.savefig(out_path, bbox_inches="tight", dpi=120)
        import matplotlib.pyplot as plt
        plt.close(fig)
        print(f"[PLOT] Saved: {out_path}")

    except Exception as e:
        print(f"[WARNING] Could not generate comparison plot: {e}")


# =============================================================================
# ANA FONKSİYON / MAIN FUNCTION
# =============================================================================

def main(dataset_root: str = "Dataset", output_dir: str = "results",
         sr: int = 16000):

    os.makedirs(output_dir, exist_ok=True)
    print("\n" + "="*65)
    print("  SES İŞARETİ ANALİZİ VE CİNSİYET SINIFLANDIRMA")
    print("  Audio Signal Analysis & Gender Classification")
    print("="*65)

    # ----------------------------------------------------------------
    # ADIM 1: VERİ SETİ YÜKLE / STEP 1: LOAD DATASET
    # ----------------------------------------------------------------
    print("\n[STEP 1] Loading dataset metadata...")
    df = load_all_metadata(dataset_root)
    print_dataset_summary(df)

    # ----------------------------------------------------------------
    # ADIM 2: ÖZNİTELİK ÇIKARIMI / STEP 2: FEATURE EXTRACTION
    # ----------------------------------------------------------------
    print("[STEP 2] Extracting features from audio files...")
    results = []
    total = len(df)

    for idx, (_, row) in enumerate(df.iterrows()):
        print(f"  Processing [{idx+1}/{total}] {os.path.basename(str(row.get('Dosya_Path','')))} ...",
              end="")
        result = process_single_file(row, sr=sr)
        results.append(result)
        f0_str = f"F0={result.get('f0_mean',0):.1f}Hz" if "f0_mean" in result else "ERR"
        pred   = result.get("prediction", "?")
        corr   = "✓" if result.get("correct", False) else "✗"
        print(f" {f0_str}, pred={pred} {corr}")

    df_results = pd.DataFrame(results)

    # CSV olarak kaydet / Save as CSV
    csv_path = os.path.join(output_dir, "feature_results.csv")
    df_results.to_csv(csv_path, index=False)
    print(f"\n[SAVED] Feature results: {csv_path}")

    # ----------------------------------------------------------------
    # ADIM 3: BAŞARI ANALİZİ / STEP 3: PERFORMANCE ANALYSIS
    # ----------------------------------------------------------------
    print("\n[STEP 3] Computing classification metrics...")

    valid = df_results[
        (df_results["Cinsiyet"].isin(["Erkek", "Kadın", "Çocuk"])) &
        (df_results["prediction"] != "Unknown")
    ]

    if len(valid) == 0:
        print("[ERROR] No valid predictions to evaluate.")
        metrics = {"overall_accuracy": 0, "per_class": {}, "confusion_matrix": [[0,0,0]]*3}
    else:
        metrics = compute_metrics(
            predictions=valid["prediction"].tolist(),
            ground_truth=valid["Cinsiyet"].tolist()
        )

    # Sonuçları yazdır / Print results
    print(f"\n{'='*55}")
    print(f"  OVERALL ACCURACY: {metrics['overall_accuracy']*100:.2f}%")
    print(f"{'='*55}")
    print(f"\n{'Sınıf':<10} {'N':>5} {'Recall':>8} {'Precision':>10} {'F1':>8}")
    print("-"*45)
    for cls in ["Erkek", "Kadın", "Çocuk"]:
        pc = metrics["per_class"].get(cls, {})
        print(f"{cls:<10} {pc.get('support',0):>5} "
              f"{pc.get('recall',0)*100:>7.1f}% "
              f"{pc.get('precision',0)*100:>9.1f}% "
              f"{pc.get('f1_score',0):>8.3f}")

    # ----------------------------------------------------------------
    # ADIM 4: GÖRSELLEŞTİRME / STEP 4: VISUALIZATION
    # ----------------------------------------------------------------
    print("\n[STEP 4] Generating visualizations...")

    # 4a. İlk geçerli dosya için tam analiz paneli
    valid_paths = df_results[
        df_results["Dosya_Path"].apply(lambda x: os.path.exists(str(x)))
    ]
    if len(valid_paths) > 0:
        sample_path = str(valid_paths.iloc[0]["Dosya_Path"])
        sample_gender = str(valid_paths.iloc[0].get("Cinsiyet", "?"))
        try:
            import matplotlib.pyplot as plt
            audio, sr_loaded = load_audio(sample_path, sr)
            frames, fl, hl = frame_signal(audio, sr_loaded)
            ste   = compute_short_time_energy(frames)
            zcr   = compute_zcr(frames, sr_loaded)
            voiced= detect_voiced_frames(ste, zcr)

            fig = plot_full_analysis(
                audio=audio, sr=sr_loaded,
                energy=ste, zcr=zcr,
                voiced_mask=voiced,
                frames=frames,
                hop_length=hl,
                title=f"Full Signal Analysis — {sample_gender} Voice "
                      f"({os.path.basename(sample_path)})"
            )
            fig.savefig(os.path.join(output_dir, "signal_analysis.png"),
                        bbox_inches="tight", dpi=120)
            plt.close(fig)
            print(f"[PLOT] Saved: signal_analysis.png")
        except Exception as e:
            print(f"[WARNING] Signal analysis plot failed: {e}")

    # 4b. Otokorelasyon vs FFT karşılaştırma
    generate_comparison_plot(df_results, output_dir, sr)

    # 4c. F0 dağılım grafikleri
    try:
        import matplotlib.pyplot as plt
        fig = plot_f0_distributions(df_results)
        fig.savefig(os.path.join(output_dir, "f0_distributions.png"),
                    bbox_inches="tight", dpi=120)
        plt.close(fig)
        print("[PLOT] Saved: f0_distributions.png")
    except Exception as e:
        print(f"[WARNING] F0 distribution plot failed: {e}")

    # 4d. Karışıklık matrisi
    try:
        import matplotlib.pyplot as plt
        fig = plot_confusion_matrix(
            cm=metrics["confusion_matrix"],
            class_labels=metrics["class_labels"],
            accuracy=metrics["overall_accuracy"]
        )
        fig.savefig(os.path.join(output_dir, "confusion_matrix.png"),
                    bbox_inches="tight", dpi=120)
        plt.close(fig)
        print("[PLOT] Saved: confusion_matrix.png")
    except Exception as e:
        print(f"[WARNING] Confusion matrix plot failed: {e}")

    # 4e. Sonuç özet tablosu
    try:
        import matplotlib.pyplot as plt
        fig = plot_results_table(metrics)
        fig.savefig(os.path.join(output_dir, "results_table.png"),
                    bbox_inches="tight", dpi=120)
        plt.close(fig)
        print("[PLOT] Saved: results_table.png")
    except Exception as e:
        print(f"[WARNING] Results table plot failed: {e}")

    print(f"\n[DONE] All results saved to: {output_dir}/")
    print("="*65 + "\n")

    return df_results, metrics


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ses İşareti Analizi ve Cinsiyet Sınıflandırma")
    parser.add_argument("--dataset", type=str, default="Dataset",
                        help="Dataset root folder (default: Dataset/)")
    parser.add_argument("--output", type=str, default="results",
                        help="Output directory (default: results/)")
    parser.add_argument("--sr", type=int, default=16000,
                        help="Sample rate in Hz (default: 16000)")
    args = parser.parse_args()

    main(dataset_root=args.dataset, output_dir=args.output, sr=args.sr)
