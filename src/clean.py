"""Steam oyun verisi temizleme ve özellik türetme fonksiyonları.

Her fonksiyon bir DataFrame alır, değiştirilmiş bir kopyasını döndürür ve
etkilenen satır sayısını stdout'a yazdırır (notebook'ta takip edilebilsin diye).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Faz 1'de incelenen ama analiz için gereksiz olan (URL, görsel, ham metin vb.) kolonlar.
UNUSED_COLUMNS = [
    "detailed_description",
    "short_description",
    "header_image",
    "website",
    "support_url",
    "support_email",
    "screenshots",
    "movies",
    "metacritic_url",
    "score_rank",
    "notes",
    "packages",
    "full_audio_languages",
    "discount",
]

# Faz 2 kararı: en az bu kadar review'u olan oyunlar "yeterli veri" sayılır.
# Steam'in kendi "Need More Reviews" eşiği de 10'dur; tutarlılık için aynısını kullanıyoruz.
MIN_REVIEWS_THRESHOLD = 10

_OWNERS_RANGE_RE = re.compile(r"([\d,]+)\s*-\s*([\d,]+)")


def drop_duplicate_apps(df: pd.DataFrame) -> pd.DataFrame:
    """Aynı app_id'ye sahip tekrarlı satırları temizler (ilkini tutar)."""
    before = len(df)
    out = df.drop_duplicates(subset="app_id", keep="first").reset_index(drop=True)
    removed = before - len(out)
    print(f"drop_duplicate_apps: {removed:,} tekrarlı satır silindi ({before:,} -> {len(out):,})")
    return out


def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Analiz için kullanılmayacak ağır/ilgisiz kolonları atar (bellek tasarrufu)."""
    existing = [c for c in UNUSED_COLUMNS if c in df.columns]
    out = df.drop(columns=existing)
    print(f"drop_unused_columns: {len(existing)} kolon atıldı -> {existing}")
    return out


def parse_release_date(df: pd.DataFrame) -> pd.DataFrame:
    """`release_date` metnini datetime'a çevirir; yıl/ay/gün ve gelecek-tarih bayrağı türetir."""
    out = df.copy()
    parsed = pd.to_datetime(out["release_date"], format="%b %d, %Y", errors="coerce")

    n_failed = int(parsed.isna().sum() - out["release_date"].isna().sum())
    print(f"parse_release_date: {n_failed:,} tarih parse edilemedi (release_date_parsed = NaT)")

    out["release_date_parsed"] = parsed
    out["release_year"] = parsed.dt.year.astype("Int64")
    out["release_month"] = parsed.dt.month.astype("Int64")
    out["release_weekday"] = parsed.dt.day_name()

    today = pd.Timestamp.today().normalize()
    out["is_future_release"] = parsed > today
    n_future = int(out["is_future_release"].sum())
    print(f"parse_release_date: {n_future:,} oyun gelecek tarihli (henüz çıkmamış/duyurulmuş)")
    return out


def parse_estimated_owners(df: pd.DataFrame) -> pd.DataFrame:
    """`"20000 - 50000"` formatındaki aralığı owners_min/owners_max/owners_mid'e çevirir."""
    out = df.copy()
    extracted = out["estimated_owners"].str.extract(_OWNERS_RANGE_RE)
    owners_min = extracted[0].str.replace(",", "", regex=False).astype(float)
    owners_max = extracted[1].str.replace(",", "", regex=False).astype(float)

    n_failed = int(owners_min.isna().sum())
    print(f"parse_estimated_owners: {n_failed:,} satırda aralık parse edilemedi")

    out["owners_min"] = owners_min
    out["owners_max"] = owners_max
    out["owners_mid"] = (owners_min + owners_max) / 2
    return out


def add_list_features(df: pd.DataFrame) -> pd.DataFrame:
    """Liste/sözlük tipi alanlardan sayısal özellikler türetir.

    `tags` diğer alanlardan farklı olarak bir sözlüktür (etiket -> oy sayısı);
    burada sadece etiket adları (`tags_list`) tutulur, oy sayıları atılır.
    """
    out = df.copy()
    out["tags_list"] = out["tags"].apply(lambda d: list(d.keys()) if isinstance(d, dict) else [])
    out = out.drop(columns=["tags"])

    out["num_languages"] = out["supported_languages"].apply(len)
    out["num_genres"] = out["genres"].apply(len)
    out["num_tags"] = out["tags_list"].apply(len)
    out["num_categories"] = out["categories"].apply(len)
    out["num_platforms"] = out[["windows", "mac", "linux"]].sum(axis=1)
    return out


def add_review_features(df: pd.DataFrame) -> pd.DataFrame:
    """total_reviews, positive_ratio ve yeterli-review bayrağını türetir."""
    out = df.copy()
    out["total_reviews"] = out["positive"] + out["negative"]
    out["positive_ratio"] = np.where(
        out["total_reviews"] > 0, out["positive"] / out["total_reviews"], np.nan
    )
    out["has_enough_reviews"] = out["total_reviews"] >= MIN_REVIEWS_THRESHOLD

    n_no_reviews = int((out["total_reviews"] == 0).sum())
    print(f"add_review_features: {n_no_reviews:,} oyunun hiç review'u yok")
    return out


def classify_review_label(df: pd.DataFrame) -> pd.DataFrame:
    """Steam'in review özet mantığına benzer, basitleştirilmiş bir sınıflandırma.

    Kullanılan eşikler (Steam'in resmi algoritmasının basitleştirilmiş hali, kendi kararımız):
      - total_reviews == 0     -> "No Reviews"
      - total_reviews < 10     -> "Not Enough Reviews"
      - positive_ratio >= 0.95 -> "Overwhelmingly Positive"
      - positive_ratio >= 0.80 -> "Very Positive"
      - positive_ratio >= 0.70 -> "Positive"
      - positive_ratio >= 0.40 -> "Mixed"
      - positive_ratio >= 0.20 -> "Negative"
      - aksi halde            -> "Overwhelmingly Negative"
    """
    out = df.copy()
    total = out["total_reviews"]
    ratio = out["positive_ratio"]

    conditions = [
        total == 0,
        total < MIN_REVIEWS_THRESHOLD,
        ratio >= 0.95,
        ratio >= 0.80,
        ratio >= 0.70,
        ratio >= 0.40,
        ratio >= 0.20,
    ]
    choices = [
        "No Reviews",
        "Not Enough Reviews",
        "Overwhelmingly Positive",
        "Very Positive",
        "Positive",
        "Mixed",
        "Negative",
    ]
    out["review_label"] = np.select(conditions, choices, default="Overwhelmingly Negative")
    print("classify_review_label:", out["review_label"].value_counts().to_dict())
    return out


def add_success_features(df: pd.DataFrame) -> pd.DataFrame:
    """is_free, is_indie, is_self_published, description_length ve log1p dönüşümlerini ekler.

    `is_indie` kararı: `genres` alanı (Steam/geliştirici tarafından atanan resmi tür) kullanılır,
    `tags` kullanılmaz. Sebep (bkz. 01_veri_inceleme.ipynb Bölüm 6): `tags` topluluk tarafından
    oy verilerek oluşuyor ve çoğu düşük-review'lu oyunda hiç yok (63.963 oyunda boş); bu da
    tag-bazlı tanımı tam olarak incelemek istediğimiz "az bilinen indie oyunlar" grubunda
    sistematik olarak eksik/yanlış bırakır. `genres` ise listeleme anında atanır ve her oyunda var.
    """
    out = df.copy()
    out["is_free"] = out["price"] == 0
    out["is_indie"] = out["genres"].apply(lambda g: "Indie" in g if isinstance(g, list) else False)
    out["is_self_published"] = out.apply(
        lambda r: bool(r["developers"])
        and bool(r["publishers"])
        and set(r["developers"]) == set(r["publishers"]),
        axis=1,
    )
    out["description_length"] = out["about_the_game"].fillna("").str.len()

    for col in ["owners_mid", "total_reviews", "average_playtime_forever"]:
        out[f"log1p_{col}"] = np.log1p(out[col].clip(lower=0))

    print(f"add_success_features: is_indie oranı = {out['is_indie'].mean():.1%}")
    print(f"add_success_features: is_free oranı   = {out['is_free'].mean():.1%}")
    return out


def clean_games(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm temizleme/özellik-türetme adımlarını sırayla uygular."""
    df = drop_duplicate_apps(df)
    df = drop_unused_columns(df)
    df = parse_release_date(df)
    df = parse_estimated_owners(df)
    df = add_list_features(df)
    df = add_review_features(df)
    df = classify_review_label(df)
    df = add_success_features(df)
    return df
