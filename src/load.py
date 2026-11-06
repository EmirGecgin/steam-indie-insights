"""Ham veri yükleme fonksiyonları."""
from pathlib import Path

import pandas as pd


def load_raw_games(json_path: Path) -> pd.DataFrame:
    """Steam games JSON dump'ını DataFrame'e yükler.

    CSV versiyonunda header/veri kayması bulunduğu için (bkz. 01_veri_inceleme.ipynb,
    Bölüm 1) JSON versiyonu kullanılır. JSON'da her oyun, app_id'yi anahtar olarak
    kullanan bir sözlük girdisi şeklinde tutulur; bu fonksiyon app_id'yi normal bir
    kolona çevirir.
    """
    df = pd.read_json(json_path, orient="index")
    df.index.name = "app_id"
    return df.reset_index()
