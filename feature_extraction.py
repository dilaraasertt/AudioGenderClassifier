"""
=============================================================================
Ses İşareti Analizi - Öznitelik Çıkarım Modülü
Audio Signal Analysis - Feature Extraction Module
=============================================================================
Bu modül; pencereleme, kısa süreli enerji, ZCR ve otokorelasyon tabanlı
F0 (temel frekans) çıkarımı işlemlerini gerçekleştirir.

This module handles windowing, short-time energy, ZCR, and autocorrelation-
based F0 (fundamental frequency) extraction.
=============================================================================
"""

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal
import os
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# BÖLÜM 1: SES DOSYASI YÜKLEME / AUDIO LOADING
# =============================================================================

def load_audio(filepath: str, target_sr: int = 16000) -> tuple:
    """
    WAV dosyasını yükler ve gerekirse mono ve hedef örnekleme hızına dönüştürür.
    Loads a WAV file and converts to mono at the target sample rate if needed.

    Parameters:
        filepath (str): .wav dosyasının yolu / path to .wav file
        target_sr (int): Hedef örnekleme hızı (Hz) / target sample rate in Hz

    Returns:
        tuple: (audio_array, sample_rate) — float32 numpy dizisi ve örnekleme hızı
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    sr, audio = wav.read(filepath)

    # Çok kanallıysa mono'ya dönüştür / Convert multi-channel to mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # int16 / int32 → float32 normalize et / Normalize int to float32
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Örnekleme hızı farklıysa yeniden örnekle / Resample if needed
    if sr != target_sr:
        num_samples = int(len(audio) * target_sr / sr)
        audio = signal.resample(audio, num_samples)
        sr = target_sr

    return audio, sr


# =============================================================================
# BÖLÜM 2: PENCERE FONKSİYONU / WINDOWING
# =============================================================================

def frame_signal(audio: np.ndarray, sr: int,
                 frame_ms: float = 25.0,
                 hop_ms: float = 10.0) -> tuple:
    """
    Sinyali örtüşen çerçevelere böler (20-30 ms).
    Segments the signal into overlapping frames (20-30 ms).

    Parameters:
        audio     : Ham sinyal / raw audio array
        sr        : Örnekleme hızı / sample rate
        frame_ms  : Çerçeve süresi milisaniye cinsinden (default 25 ms)
        hop_ms    : Çerçeveler arası atlama süresi (default 10 ms)

    Returns:
        frames (np.ndarray): [num_frames × frame_length]
        frame_length (int) : Örnek sayısı cinsinden çerçeve uzunluğu
        hop_length (int)   : Atlama adımı (örnek)
    """
    frame_length = int(sr * frame_ms / 1000.0)
    hop_length   = int(sr * hop_ms  / 1000.0)

    # Hann penceresi uygula / Apply Hann window
    window = np.hanning(frame_length)

    num_frames = 1 + (len(audio) - frame_length) // hop_length
    frames = np.zeros((num_frames, frame_length), dtype=np.float32)

    for i in range(num_frames):
        start = i * hop_length
        frames[i] = audio[start: start + frame_length] * window

    return frames, frame_length, hop_length


# =============================================================================
# BÖLÜM 3: KISA SÜRELİ ENERJİ / SHORT-TIME ENERGY
# =============================================================================

def compute_short_time_energy(frames: np.ndarray) -> np.ndarray:
    """
    Her çerçeve için kısa süreli enerji hesaplar: E[n] = Σ x²[m]
    Computes short-time energy for each frame: E[n] = sum(x^2)

    Parameters:
        frames: [num_frames × frame_length]

    Returns:
        energy: [num_frames] — her çerçevenin enerji değeri
    """
    return np.sum(frames ** 2, axis=1)


# =============================================================================
# BÖLÜM 4: SIFIR GEÇİŞ ORANI / ZERO CROSSING RATE
# =============================================================================

def compute_zcr(frames: np.ndarray, sr: int) -> np.ndarray:
    """
    Her çerçeve için Sıfır Geçiş Oranı (ZCR) hesaplar.
    Computes Zero Crossing Rate (ZCR) for each frame.

    ZCR = (1 / 2T) * Σ |sgn(x[n]) - sgn(x[n-1])|
    Burada T = çerçeve süresi (saniye cinsinden)

    Parameters:
        frames: [num_frames × frame_length]
        sr    : Örnekleme hızı (saniyedeki geçiş sayısına normalize etmek için)

    Returns:
        zcr: [num_frames] — saniyedeki sıfır geçiş sayısı
    """
    signs = np.sign(frames)
    crossings = np.sum(np.abs(np.diff(signs, axis=1)), axis=1) / 2.0
    # Saniyedeki geçiş sayısına normalize et / Normalize to crossings per second
    frame_duration = frames.shape[1] / sr
    return crossings / frame_duration


# =============================================================================
# BÖLÜM 5: SESLİ/SESSİZ BÖLGE TESPİTİ / VOICED/UNVOICED DETECTION
# =============================================================================

def detect_voiced_frames(energy: np.ndarray,
                          zcr: np.ndarray,
                          energy_threshold_factor: float = 0.05,
                          zcr_threshold: float = 3000.0) -> np.ndarray:
    """
    Enerji ve ZCR kullanarak sesli (voiced) çerçeveleri tespit eder.
    Detects voiced frames using energy and ZCR criteria.

    Sesli bölge kriterleri:
    - Enerji > toplam maksimumun %5'i (gürültülü çerçeveleri eler)
    - ZCR < eşik (yüksek ZCR genellikle sessiz/gürültülü bölgeleri gösterir)

    Parameters:
        energy                 : Her çerçeve için enerji değerleri
        zcr                    : Her çerçeve için ZCR değerleri
        energy_threshold_factor: Enerji eşiği = max_enerji × bu faktör
        zcr_threshold          : Maksimum ZCR (Hz) sesli bölgeler için

    Returns:
        voiced_mask: bool dizisi, True = sesli çerçeve
    """
    energy_threshold = np.max(energy) * energy_threshold_factor
    energy_mask = energy > energy_threshold
    zcr_mask    = zcr < zcr_threshold

    return energy_mask & zcr_mask


# =============================================================================
# BÖLÜM 6: OTOKORELASYONla F0 TESPİTİ / F0 VIA AUTOCORRELATION
# =============================================================================

def compute_autocorrelation(frame: np.ndarray) -> np.ndarray:
    """
    Tek bir çerçeve için otokorelasyon fonksiyonunu hesaplar.
    Computes the autocorrelation function for a single frame.

    R[τ] = Σ x[n] * x[n - τ]   (Unnormalized autocorrelation)

    NOT: Kütüphane fonksiyonu kullanılmamış; sıfırdan implement edilmiştir.
    NOTE: No library pitch function used; implemented from scratch.

    Parameters:
        frame: tek çerçevenin sinyal değerleri

    Returns:
        acf: otokorelasyon fonksiyonu değerleri [0..N-1]
    """
    n = len(frame)
    acf = np.zeros(n)
    for tau in range(n):
        acf[tau] = np.sum(frame[:n - tau] * frame[tau:])
    return acf


def compute_autocorrelation_fast(frame: np.ndarray) -> np.ndarray:
    """
    FFT tabanlı hızlı otokorelasyon hesabı (büyük veri setleri için).
    FFT-based fast autocorrelation (for large datasets).

    Aynı matematiksel sonucu üretir: R[τ] = IFFT(|FFT(x)|²)
    """
    n = len(frame)
    # Dairesel korelasyonu önlemek için sıfır doldur / Zero-pad to avoid circular correlation
    nfft = 2 * n
    X = np.fft.rfft(frame, n=nfft)
    acf = np.fft.irfft(X * np.conj(X))
    return acf[:n]


def estimate_f0_autocorrelation(frame: np.ndarray, sr: int,
                                 f0_min: float = 60.0,
                                 f0_max: float = 500.0) -> float:
    """
    Otokorelasyon yöntemiyle temel frekansı (F0 / pitch) tahmin eder.
    Estimates F0 (fundamental frequency / pitch) via autocorrelation.

    Yöntem:
    1. Çerçeveye otokorelasyon uygula
    2. F0 aralığına karşılık gelen gecikme (lag) aralığını belirle
    3. Bu aralıkta maksimum tepe noktasını bul → periyot T
    4. F0 = 1 / T = sr / lag_at_peak

    Parameters:
        frame : tek çerçeve sinyali
        sr    : örnekleme hızı
        f0_min: minimum F0 (Erkek: ~60 Hz)
        f0_max: maksimum F0 (Çocuk: ~500 Hz)

    Returns:
        f0 (float): tahmin edilen temel frekans (Hz), bulunamazsa 0.0
    """
    acf = compute_autocorrelation_fast(frame)

    # F0 aralığına karşılık gelen lag sınırlarını hesapla
    # lag_min = sr / f0_max,  lag_max = sr / f0_min
    lag_min = int(sr / f0_max)
    lag_max = int(sr / f0_min)
    lag_max = min(lag_max, len(acf) - 1)

    if lag_min >= lag_max:
        return 0.0

    # Gecikme aralığındaki maksimum tepe noktasını bul
    search_acf = acf[lag_min:lag_max]
    if len(search_acf) == 0:
        return 0.0

    peak_idx = np.argmax(search_acf) + lag_min

    # Tepe noktasının normallenmiş gücü yeterli mi kontrol et
    if acf[0] > 0 and (acf[peak_idx] / acf[0]) < 0.3:
        return 0.0  # Sinyal yeterince periyodik değil / Not periodic enough

    f0 = sr / peak_idx
    return float(f0)


# =============================================================================
# BÖLÜM 7: FFT SPEKTRUMU / FFT SPECTRUM (Karşılaştırma için)
# =============================================================================

def compute_fft_spectrum(frame: np.ndarray, sr: int) -> tuple:
    """
    Bir çerçeve için FFT büyüklük spektrumunu hesaplar.
    Computes the FFT magnitude spectrum for a frame.

    Returns:
        freqs : frekans ekseni (Hz)
        magnitude: büyüklük spektrumu |X(f)|
    """
    n = len(frame)
    X = np.fft.rfft(frame * np.hanning(n))
    magnitude = np.abs(X)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    return freqs, magnitude


def estimate_f0_fft(frame: np.ndarray, sr: int,
                    f0_min: float = 60.0, f0_max: float = 500.0) -> float:
    """
    FFT spektrumundaki ilk baskın harmonik tepe noktasını bularak F0 tahmin eder.
    Estimates F0 from the first dominant harmonic peak in the FFT spectrum.
    """
    freqs, magnitude = compute_fft_spectrum(frame, sr)
    # F0 aralığına göre filtrele
    mask = (freqs >= f0_min) & (freqs <= f0_max)
    if not np.any(mask):
        return 0.0
    peak_idx = np.argmax(magnitude[mask])
    return float(freqs[mask][peak_idx])


# =============================================================================
# BÖLÜM 8: TAM DOSYA ÖZNİTELİK ÇIKARIMI / FULL FILE FEATURE EXTRACTION
# =============================================================================

def extract_features(filepath: str, sr: int = 16000) -> dict:
    """
    Bir .wav dosyasından tüm öznitelikleri çıkarır.
    Extracts all features from a single .wav file.

    İşlem akışı:
    1. Ses yükle → 2. Çerçevele → 3. STE + ZCR hesapla →
    4. Sesli çerçeveleri bul → 5. Her sesli çerçeve için F0 hesapla (Otokorelasyon)
    6. İstatistiksel özetleri döndür

    Returns:
        dict with keys:
            f0_mean, f0_std, f0_median     : F0 istatistikleri (Hz)
            zcr_mean, zcr_std              : ZCR istatistikleri
            energy_mean, energy_std        : Enerji istatistikleri
            voiced_ratio                   : Sesli çerçeve oranı
            duration                       : Ses süresi (saniye)
    """
    try:
        audio, sr = load_audio(filepath, target_sr=sr)
    except Exception as e:
        return {"error": str(e)}

    # Çerçevele (25 ms çerçeve, 10 ms atlama)
    frames, frame_len, hop_len = frame_signal(audio, sr, frame_ms=25.0, hop_ms=10.0)

    # Kısa süreli enerji ve ZCR
    energy = compute_short_time_energy(frames)
    zcr    = compute_zcr(frames, sr)

    # Sesli/sessiz ayrımı
    voiced_mask = detect_voiced_frames(energy, zcr)
    voiced_frames = frames[voiced_mask]
    voiced_energy = energy[voiced_mask]
    voiced_zcr    = zcr[voiced_mask]

    # Yeterli sesli çerçeve yoksa varsayılan döndür
    if len(voiced_frames) < 5:
        return {
            "f0_mean": 0.0, "f0_std": 0.0, "f0_median": 0.0,
            "zcr_mean": float(np.mean(zcr)), "zcr_std": float(np.std(zcr)),
            "energy_mean": float(np.mean(energy)),
            "energy_std": float(np.std(energy)),
            "voiced_ratio": 0.0,
            "duration": len(audio) / sr,
            "warning": "Insufficient voiced frames"
        }

    # Sesli çerçevelerden F0 hesapla (otokorelasyon)
    f0_values = []
    for frame in voiced_frames:
        f0 = estimate_f0_autocorrelation(frame, sr, f0_min=60.0, f0_max=500.0)
        if f0 > 0:
            f0_values.append(f0)

    f0_arr = np.array(f0_values) if f0_values else np.array([0.0])

    return {
        "f0_mean"     : float(np.mean(f0_arr)),
        "f0_std"      : float(np.std(f0_arr)),
        "f0_median"   : float(np.median(f0_arr)),
        "zcr_mean"    : float(np.mean(voiced_zcr)),
        "zcr_std"     : float(np.std(voiced_zcr)),
        "energy_mean" : float(np.mean(voiced_energy)),
        "energy_std"  : float(np.std(voiced_energy)),
        "voiced_ratio": float(np.sum(voiced_mask) / len(frames)),
        "duration"    : float(len(audio) / sr),
        "num_voiced_frames": int(np.sum(voiced_mask)),
        "raw_f0_values": f0_arr.tolist()
    }
