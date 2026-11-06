"""Ortak grafik stili ve yardımcı fonksiyonlar.

Tüm notebook'lar grafik üretirken bu modülü kullanır; böylece renk paleti,
font ve kayıt davranışı (dosya adı, çözünürlük) tüm proje boyunca tutarlı olur.

Renk paleti, kategorik sıralama CVD (renk körlüğü) güvenliği için sabit tutulmalıdır
(bkz. `dataviz` referans paleti): kategorik renkler asla rastgele sırayla kullanılmamalı.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

FIGURES_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures"

# Kategorik palet — sabit sıra, CVD-güvenli (bkz. dataviz referans paleti).
CATEGORICAL_PALETTE = [
    "#2a78d6",  # mavi
    "#eb6834",  # turuncu
    "#1baf7a",  # deniz mavisi/yeşil
    "#eda100",  # sarı
    "#e87ba4",  # eflatun
    "#008300",  # yeşil
    "#6250d6",  # mor
    "#e34948",  # kırmızı
]

# Büyüklük (magnitude) kodlaması için tek renk, açık -> koyu mavi.
_SEQUENTIAL_BLUE_STEPS = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]
SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list("steam_sequential_blue", _SEQUENTIAL_BLUE_STEPS)

# Kutuplaşma (örn. korelasyon) için mavi <-> kırmızı, nötr gri orta nokta.
DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "steam_diverging", ["#1c5cab", "#f0efec", "#e34948"]
)

CHART_SURFACE = "#fcfcfb"
PRIMARY_INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED_INK = "#898781"
GRIDLINE = "#e1e0d9"


def set_style() -> None:
    """Tüm notebook'larda çağrılacak, tutarlı matplotlib/seaborn stilini uygular."""
    sns.set_theme(style="white")
    plt.rcParams.update(
        {
            "figure.facecolor": CHART_SURFACE,
            "axes.facecolor": CHART_SURFACE,
            "savefig.facecolor": CHART_SURFACE,
            "axes.edgecolor": GRIDLINE,
            "axes.labelcolor": PRIMARY_INK,
            "axes.titlecolor": PRIMARY_INK,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.grid": True,
            "grid.color": GRIDLINE,
            "grid.linewidth": 0.8,
            "text.color": PRIMARY_INK,
            "xtick.color": SECONDARY_INK,
            "ytick.color": SECONDARY_INK,
            "font.size": 10.5,
            "font.family": "sans-serif",
            "figure.dpi": 110,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    sns.set_palette(CATEGORICAL_PALETTE)


def turkish_thousands(x, _pos=None) -> str:
    """Eksen etiketleri için Türkçe binlik ayırıcı (nokta) biçimlendirici."""
    return f"{x:,.0f}".replace(",", ".")


def apply_turkish_axis(ax, axis: str = "y") -> None:
    """Belirtilen eksene Türkçe binlik ayırıcı formatter uygular."""
    formatter = mticker.FuncFormatter(turkish_thousands)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)


def save_fig(fig, name: str) -> Path:
    """Grafiği `reports/figures/<name>.png` olarak kaydeder ve yolunu döndürür.

    `name` örn. "03_01_yillara_gore_cikis" gibi numaralı/açıklayıcı olmalı.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / f"{name}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    return out_path
