"""
=============================================================================
Veri Seti Yönetimi
Dataset Management Module
=============================================================================
Tüm grup klasörlerini tarar, Excel metadata dosyalarını birleştirir ve
ses dosyalarını güvenli şekilde yükler.

Scans all group folders, merges Excel metadata files, and safely loads
audio files from the dataset structure.
=============================================================================
"""

import os
import glob
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# BÖLÜM 1: METADATA YÜKLEME / METADATA LOADING
# =============================================================================

def load_all_metadata(dataset_root: str) -> pd.DataFrame:
    """
    Dataset/ klasörü altındaki tüm grup Excel dosyalarını okuyup birleştirir.
    Reads and merges all group Excel files under Dataset/ folder.

    Beklenen klasör yapısı / Expected folder structure:
        Dataset/
          Grup_01/
            metadata_Grup01.xlsx   (sütunlar: Dosya_Adı, Cinsiyet, Yaş, ...)
            audio_001.wav
            audio_002.wav
          Grup_02/
            ...

    Parameters:
        dataset_root: Dataset/ klasörünün yolu

    Returns:
        pd.DataFrame: Tüm grupların birleşik metadata tablosu
    """
    all_dfs = []

    # Tüm excel dosyalarını bul / Find all excel files
    excel_patterns = [
        os.path.join(dataset_root, "**", "*.xlsx"),
        os.path.join(dataset_root, "**", "*.xls"),
        os.path.join(dataset_root, "**", "*.csv"),
    ]

    found_files = []
    for pattern in excel_patterns:
        found_files.extend(glob.glob(pattern, recursive=True))

    if not found_files:
        print(f"[WARNING] No metadata files found in {dataset_root}")
        print("          Creating synthetic dataset for demonstration...")
        return _create_synthetic_metadata(dataset_root)

    for excel_path in found_files:
        try:
            if excel_path.endswith(".csv"):
                df = pd.read_csv(excel_path)
            else:
                df = pd.read_excel(excel_path)

            # Grup bilgisini klasör adından çıkar / Extract group info from folder
            group_folder = os.path.basename(os.path.dirname(excel_path))
            df["Grup"] = group_folder

            # Dosya yolunu mutlak yola çevir / Resolve file paths to absolute
            folder = os.path.dirname(excel_path)
            df = _resolve_file_paths(df, folder)

            all_dfs.append(df)
            print(f"[OK] Loaded metadata: {excel_path} ({len(df)} records)")

        except Exception as e:
            print(f"[ERROR] Could not read {excel_path}: {e}")

    if not all_dfs:
        return _create_synthetic_metadata(dataset_root)

    # Tüm dataframe'leri birleştir / Concatenate all dataframes
    master_df = pd.concat(all_dfs, ignore_index=True)

    # Sütun isimlerini normalize et / Normalize column names
    master_df = _normalize_columns(master_df)

    print(f"\n[DATASET] Total records found: {len(master_df)}")
    print(f"[DATASET] Columns: {list(master_df.columns)}")

    return master_df


def _resolve_file_paths(df: pd.DataFrame, folder: str) -> pd.DataFrame:
    """
    Excel'deki dosya adlarını mutlak yollara çevirir.
    Converts filenames in Excel to absolute paths.
    """
    # Dosya yolu sütununu bul / Find file path column
    path_cols = [c for c in df.columns if any(
        kw in c.lower() for kw in ["dosya", "path", "file", "wav", "audio"]
    )]

    if path_cols:
        col = path_cols[0]
        df["Dosya_Path"] = df[col].apply(
            lambda x: os.path.join(folder, str(x)) if pd.notna(x) else None
        )
    else:
        # Klasördeki tüm .wav dosyalarını otomatik tespit et
        wav_files = glob.glob(os.path.join(folder, "*.wav"))
        df["Dosya_Path"] = wav_files[:len(df)]

    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Farklı gruplardaki sütun isimlerini standart hale getirir.
    Normalizes column names across different groups.

    Standart sütunlar: Dosya_Path, Cinsiyet, Yas, Grup
    """
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ["cinsiyet", "gender", "sex", "cins"]):
            rename_map[col] = "Cinsiyet"
        elif any(k in col_lower for k in ["yaş", "yas", "age"]):
            rename_map[col] = "Yas"
        elif any(k in col_lower for k in ["ad", "isim", "name", "subject"]):
            rename_map[col] = "Denek_Adi"

    df = df.rename(columns=rename_map)

    # Cinsiyet değerlerini normalize et / Normalize gender values
    if "Cinsiyet" in df.columns:
        gender_map = {
            "e": "Erkek", "erkek": "Erkek", "m": "Erkek", "male": "Erkek",
            "k": "Kadın",  "kadin": "Kadın",  "kadın": "Kadın", "f": "Kadın",
            "female": "Kadın", "woman": "Kadın",
            "ç": "Çocuk", "cocuk": "Çocuk", "çocuk": "Çocuk", "child": "Çocuk",
            "kid": "Çocuk", "boy": "Çocuk", "girl": "Çocuk"
        }
        df["Cinsiyet"] = df["Cinsiyet"].apply(
            lambda x: gender_map.get(str(x).lower().strip(), str(x))
        )

    return df


# =============================================================================
# BÖLÜM 2: SENTETİK VERİ SETİ (DEMO İÇİN)
# SECTION 2: SYNTHETIC DATASET (FOR DEMO PURPOSES)
# =============================================================================

def _create_synthetic_metadata(dataset_root: str) -> pd.DataFrame:
    """
    Dataset bulunamadığında sentetik metadata oluşturur.
    Creates synthetic metadata when no real dataset is found.

    NOT: Gerçek çalıştırma sırasında Dataset/ klasörü var olmalıdır.
    NOTE: In real usage, the Dataset/ folder must exist.
    """
    print("[INFO] Generating synthetic metadata for demonstration...")

    records = []
    groups = ["Grup_01", "Grup_02", "Grup_03"]

    for g_idx, grup in enumerate(groups):
        grup_folder = os.path.join(dataset_root, grup)
        os.makedirs(grup_folder, exist_ok=True)

        # Her grup için: 2 Erkek, 2 Kadın, 2 Çocuk kayıt
        subjects = [
            ("Erkek_01", "Erkek", 28), ("Erkek_02", "Erkek", 35),
            ("Kadin_01", "Kadın",  26), ("Kadin_02", "Kadın",  31),
            ("Cocuk_01", "Çocuk",  8), ("Cocuk_02", "Çocuk",  10),
        ]

        for s_idx, (name, gender, age) in enumerate(subjects):
            filename = f"{gender[0]}{g_idx+1}{s_idx+1:02d}.wav"
            filepath = os.path.join(grup_folder, filename)

            # Sentetik WAV dosyası oluştur
            _create_synthetic_wav(filepath, gender, duration=3.0)

            records.append({
                "Dosya_Path": filepath,
                "Dosya_Adı" : filename,
                "Cinsiyet"  : gender,
                "Yas"       : age,
                "Denek_Adi" : name,
                "Grup"      : grup,
            })

    df = pd.DataFrame(records)
    print(f"[INFO] Created {len(df)} synthetic records across {len(groups)} groups")
    return df


def _create_synthetic_wav(filepath: str, gender: str, duration: float = 3.0):
    """
    Belirtilen cinsiyet için gerçekçi F0 ile sentetik ses oluşturur.
    Creates synthetic audio with realistic F0 for the specified gender.
    """
    import scipy.io.wavfile as wav_write

    sr = 16000
    t = np.linspace(0, duration, int(sr * duration))

    # Cinsiyete göre F0 belirle / Set F0 by gender
    if gender == "Erkek":
        f0 = np.random.uniform(100, 160)   # Erkek: 85–180 Hz
    elif gender == "Kadın":
        f0 = np.random.uniform(180, 240)   # Kadın: 165–255 Hz
    else:  # Çocuk
        f0 = np.random.uniform(260, 380)   # Çocuk: 250–400 Hz

    # Harmonikler ekleyerek daha gerçekçi ses / Add harmonics for realism
    signal = np.zeros_like(t)
    for harmonic in range(1, 6):
        amplitude = 1.0 / harmonic
        signal += amplitude * np.sin(2 * np.pi * f0 * harmonic * t)

    # Hafif titreme (jitter) ekle / Add slight jitter
    jitter = 0.03 * np.random.randn(len(t))
    signal = signal + jitter

    # Normalize ve int16'ya dönüştür
    signal = signal / np.max(np.abs(signal)) * 0.8
    signal_int16 = (signal * 32767).astype(np.int16)

    wav_write.write(filepath, sr, signal_int16)


# =============================================================================
# BÖLÜM 3: VERİ SETİ İSTATİSTİKLERİ / DATASET STATISTICS
# =============================================================================

def print_dataset_summary(df: pd.DataFrame):
    """Veri seti özetini yazdırır / Prints dataset summary."""
    print("\n" + "="*60)
    print("VERİ SETİ ÖZETİ / DATASET SUMMARY")
    print("="*60)
    print(f"Toplam kayıt / Total records: {len(df)}")

    if "Cinsiyet" in df.columns:
        print("\nCinsiyet dağılımı / Gender distribution:")
        print(df["Cinsiyet"].value_counts().to_string())

    if "Grup" in df.columns:
        print("\nGrup dağılımı / Group distribution:")
        print(df["Grup"].value_counts().to_string())

    if "Yas" in df.columns:
        print(f"\nYaş aralığı / Age range: {df['Yas'].min()} – {df['Yas'].max()}")

    # Var olan dosya sayısını kontrol et
    if "Dosya_Path" in df.columns:
        existing = df["Dosya_Path"].apply(
            lambda x: os.path.exists(str(x)) if pd.notna(x) else False
        )
        print(f"\nVar olan ses dosyaları / Existing audio files: "
              f"{existing.sum()} / {len(df)}")
    print("="*60 + "\n")
