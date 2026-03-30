"""
=============================================================================
Kural Tabanlı Cinsiyet Sınıflandırıcı
Rule-Based Gender Classifier
=============================================================================
F0 (temel frekans), ZCR ve enerji özniteliklerini kullanarak
Erkek / Kadın / Çocuk sınıflandırması yapar.

Performs Male / Female / Child classification using F0, ZCR, and energy.

Eşik değerleri (Hz) — literatür tabanlı:
  Erkek  : 85–180 Hz (ortalama ~120 Hz)
  Kadın  : 165–255 Hz (ortalama ~210 Hz)
  Çocuk  : 250–400 Hz (ortalama ~300 Hz)

Kaynaklar / References:
  Titze, I.R. (1994). Principles of Voice Production. Prentice Hall.
  Hollien, H. & Shipp, T. (1972). J. Speech Hear. Res.
=============================================================================
"""

import numpy as np
from typing import Dict, List, Tuple


# =============================================================================
# BÖLÜM 1: EŞİK DEĞERLERİ (KOLAY DEĞİŞTİRİLEBİLİR)
# SECTION 1: THRESHOLD VALUES (EASY TO MODIFY)
# =============================================================================

# Bu değerler literatüre dayalıdır ve kolayca ayarlanabilir.
# These values are literature-based and can be easily tuned.
THRESHOLDS = {
    # F0 sınır değerleri (Hz)
    # F0 boundary values (Hz)
    "f0_male_max"   : 180.0,   # Erkek maksimum F0 / Male max F0
    "f0_female_min" : 155.0,   # Kadın minimum F0 / Female min F0
    "f0_female_max" : 260.0,   # Kadın maksimum F0 / Female max F0
    "f0_child_min"  : 240.0,   # Çocuk minimum F0 / Child min F0

    # Çakışma bölgesi için ek öznitelikler / Additional features for overlap zones
    "zcr_child_min" : 2500.0,  # Çocuk seslerinde ZCR genellikle daha yüksek
    "zcr_male_max"  : 3500.0,  # Erkek seslerinde ZCR genellikle daha düşük

    # Güven eşiği / Confidence threshold
    "min_f0_for_classification": 50.0,  # Bu değerin altındaki F0'lar güvenilmez
}


# =============================================================================
# BÖLÜM 2: TEMEL SINIFLANDIRICI / CORE CLASSIFIER
# =============================================================================

def classify_gender(features: dict) -> Tuple[str, float, str]:
    """
    Özniteliklere dayalı kural tabanlı cinsiyet sınıflandırması.
    Rule-based gender classification based on extracted features.

    Karar ağacı / Decision tree:
    1. F0 bilgisi güvenilir mi?
    2. F0 < 180 Hz → Erkek (Çakışmayı ZCR ile kır)
    3. F0 > 240 Hz → Çocuk (Çakışmayı ZCR ile kır)
    4. 155-260 Hz → Kadın (F0 + ZCR kombinasyonu)
    5. Belirsiz bölge → Enerji ve ZCR'ye göre karar ver

    Parameters:
        features (dict): extract_features() fonksiyonundan dönen sözlük

    Returns:
        (predicted_class, confidence, reasoning)
        predicted_class: "Erkek" | "Kadın" | "Çocuk"
        confidence     : 0.0 – 1.0 arası güven skoru
        reasoning      : Kararın açıklaması (hata analizi için)
    """
    f0   = features.get("f0_mean", 0.0)
    zcr  = features.get("zcr_mean", 0.0)

    T = THRESHOLDS  # Kısaltma için / Shorthand

    # Güvenilmez F0 kontrolü
    if f0 < T["min_f0_for_classification"]:
        # F0 tespit edilemedi; ZCR ve enerjiye göre yedek karar ver
        if zcr > T["zcr_child_min"]:
            return "Çocuk", 0.40, "F0 unreliable; high ZCR suggests child voice"
        elif zcr < T["zcr_male_max"]:
            return "Erkek", 0.40, "F0 unreliable; low ZCR suggests male voice"
        else:
            return "Kadın", 0.35, "F0 unreliable; medium ZCR suggests female voice"

    # -----------------------------------------------------------------------
    # ANA KARAR KURALLARI / MAIN DECISION RULES
    # -----------------------------------------------------------------------

    # Kural 1: Kesin Erkek bölgesi (F0 < female_min)
    if f0 < T["f0_female_min"]:
        if f0 < T["f0_male_max"]:
            confidence = 0.90 - (f0 / T["f0_male_max"]) * 0.20
            return "Erkek", round(confidence, 2), \
                   f"F0={f0:.1f}Hz < {T['f0_male_max']}Hz (male threshold); high confidence"
        else:
            # 180-155 Hz arası çakışma bölgesi — Erkek ve Kadın örtüşür
            if zcr < T["zcr_male_max"]:
                return "Erkek", 0.65, \
                       f"F0={f0:.1f}Hz in overlap zone; low ZCR={zcr:.0f} supports male"
            else:
                return "Kadın", 0.60, \
                       f"F0={f0:.1f}Hz in overlap zone; higher ZCR={zcr:.0f} supports female"

    # Kural 2: Kesin Çocuk bölgesi (F0 > child_min)
    if f0 > T["f0_child_min"]:
        confidence = min(0.95, 0.75 + (f0 - T["f0_child_min"]) / 200.0)
        return "Çocuk", round(confidence, 2), \
               f"F0={f0:.1f}Hz > {T['f0_child_min']}Hz (child threshold)"

    # Kural 3: Kadın bölgesi (female_min – female_max) — çakışmaları ZCR ile kır
    if T["f0_female_min"] <= f0 <= T["f0_female_max"]:
        # 240-260 Hz arası: Kadın veya Çocuk çakışması
        if f0 > 230.0:
            if zcr > T["zcr_child_min"]:
                return "Çocuk", 0.65, \
                       f"F0={f0:.1f}Hz in female/child overlap; high ZCR={zcr:.0f} supports child"
            else:
                return "Kadın", 0.65, \
                       f"F0={f0:.1f}Hz in female/child overlap; ZCR={zcr:.0f} supports female"
        confidence = 0.80
        return "Kadın", confidence, \
               f"F0={f0:.1f}Hz in core female range ({T['f0_female_min']}-{T['f0_female_max']}Hz)"

    # Kural 4: Yukarı çakışma bölgesi (female_max – child_min arası)
    # 260-240 Hz paradoksu (female_max > child_min olduğundan bu aralık yok)
    # Ek güvenlik: beklenmedik değerler
    return "Kadın", 0.45, f"F0={f0:.1f}Hz in ambiguous region; defaulting to female"


# =============================================================================
# BÖLÜM 3: TOPLU SINIFLANDIRMA / BATCH CLASSIFICATION
# =============================================================================

def classify_batch(feature_list: List[dict]) -> List[dict]:
    """
    Birden fazla dosya için toplu sınıflandırma yapar.
    Classifies a list of feature dictionaries.

    Parameters:
        feature_list: her eleman extract_features() çıktısı olan liste

    Returns:
        Aynı liste, her elemana 'prediction', 'confidence', 'reasoning' eklenerek
    """
    results = []
    for feat in feature_list:
        if "error" in feat:
            feat["prediction"] = "Unknown"
            feat["confidence"] = 0.0
            feat["reasoning"]  = feat["error"]
        else:
            pred, conf, reason = classify_gender(feat)
            feat["prediction"] = pred
            feat["confidence"] = conf
            feat["reasoning"]  = reason
        results.append(feat)
    return results


# =============================================================================
# BÖLÜM 4: BAŞARI METRİKLERİ / PERFORMANCE METRICS
# =============================================================================

def compute_metrics(predictions: List[str], ground_truth: List[str]) -> dict:
    """
    Sınıflandırma başarısını hesaplar.
    Computes classification performance metrics.

    Parameters:
        predictions : tahmin edilen etiketler listesi
        ground_truth: gerçek etiketler listesi

    Returns:
        dict with: overall_accuracy, per_class_metrics, confusion_matrix
    """
    classes = ["Erkek", "Kadın", "Çocuk"]

    # Genel doğruluk / Overall accuracy
    correct = sum(p == g for p, g in zip(predictions, ground_truth))
    overall_accuracy = correct / len(predictions) if predictions else 0.0

    # Sınıf bazlı metrikler / Per-class metrics
    per_class = {}
    for cls in classes:
        tp = sum(p == cls and g == cls for p, g in zip(predictions, ground_truth))
        fp = sum(p == cls and g != cls for p, g in zip(predictions, ground_truth))
        fn = sum(p != cls and g == cls for p, g in zip(predictions, ground_truth))
        tn = sum(p != cls and g != cls for p, g in zip(predictions, ground_truth))

        total_cls = sum(g == cls for g in ground_truth)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        per_class[cls] = {
            "support"  : total_cls,
            "tp"       : tp,
            "fp"       : fp,
            "fn"       : fn,
            "precision": round(precision, 4),
            "recall"   : round(recall, 4),
            "f1_score" : round(f1, 4),
            "accuracy" : round(tp / total_cls if total_cls > 0 else 0.0, 4)
        }

    # Karışıklık matrisi / Confusion matrix
    n = len(classes)
    cm = np.zeros((n, n), dtype=int)
    cls_to_idx = {c: i for i, c in enumerate(classes)}
    for p, g in zip(predictions, ground_truth):
        if p in cls_to_idx and g in cls_to_idx:
            cm[cls_to_idx[g], cls_to_idx[p]] += 1

    return {
        "overall_accuracy": round(overall_accuracy, 4),
        "per_class"       : per_class,
        "confusion_matrix": cm.tolist(),
        "class_labels"    : classes,
        "total_samples"   : len(predictions)
    }
