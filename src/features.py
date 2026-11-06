"""Özellik mühendisliği yardımcı fonksiyonları."""
from __future__ import annotations

from collections import Counter

import pandas as pd


def multi_hot_encode(df: pd.DataFrame, column: str, top_n: int = 20, prefix: str | None = None):
    """Liste tipi bir kolondaki (örn. `genres`, `tags_list`) en sık görülen `top_n`
    değeri multi-hot (her değer için bool kolon) kolonlara çevirir.

    Bir oyun birden fazla türe/etikete sahip olabileceği için bu klasik one-hot değil,
    multi-hot encoding'dir (aynı anda birden fazla kolon True olabilir).

    Döndürür: (encoded_df, top_values) — `top_values`, hangi değerlerin seçildiğini
    gösterir; aynı listeyi başka bir veri kümesinde (örn. test seti) tutarlı şekilde
    tekrar kullanmak için saklanabilir.
    """
    prefix = prefix or column
    counter: Counter[str] = Counter()
    for items in df[column]:
        counter.update(items)
    top_values = [value for value, _ in counter.most_common(top_n)]

    encoded = pd.DataFrame(
        {
            f"{prefix}_{value.replace(' ', '_').lower()}": df[column].apply(lambda items, v=value: v in items)
            for value in top_values
        },
        index=df.index,
    )
    return encoded, top_values
