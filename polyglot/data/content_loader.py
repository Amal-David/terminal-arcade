"""Aggregates all 70 language-pair modules into a single registry."""

from __future__ import annotations

from .pairs import LanguagePair

# EN → 14 original target languages
from . import (  # noqa: F401
    pair_en_es,
    pair_en_fr,
    pair_en_de,
    pair_en_it,
    pair_en_pt,
    pair_en_ja,
    pair_en_ko,
    pair_en_zh,
    pair_en_ru,
    pair_en_ar,
    pair_en_hi,
    pair_en_nl,
    pair_en_sv,
    pair_en_tr,
)

# EN → expansion (European, Nordic, Middle Eastern)
from . import (  # noqa: F401
    pair_en_pl,
    pair_en_uk,
    pair_en_cs,
    pair_en_hu,
    pair_en_ro,
    pair_en_el,
    pair_en_fi,
    pair_en_no,
    pair_en_da,
    pair_en_is,
    pair_en_he,
    pair_en_fa,
)

# EN → expansion (South Asian)
from . import (  # noqa: F401
    pair_en_ur,
    pair_en_bn,
    pair_en_ta,
    pair_en_te,
    pair_en_ml,
    pair_en_pa,
    pair_en_gu,
    pair_en_mr,
)

# EN → expansion (Southeast Asian)
from . import (  # noqa: F401
    pair_en_id,
    pair_en_ms,
    pair_en_vi,
    pair_en_th,
    pair_en_tl,
)

# EN → expansion (African)
from . import (  # noqa: F401
    pair_en_sw,
    pair_en_zu,
    pair_en_am,
    pair_en_yo,
)

# EN → expansion (Other European)
from . import (  # noqa: F401
    pair_en_bg,
    pair_en_sr,
    pair_en_hr,
    pair_en_sk,
    pair_en_ca,
    pair_en_cy,
    pair_en_ga,
)

# EN → constructed / classical
from . import (  # noqa: F401
    pair_en_la,
    pair_en_eo,
)

# XX → EN (6 original reverse pairs)
from . import (  # noqa: F401
    pair_es_en,
    pair_pt_en,
    pair_fr_en,
    pair_de_en,
    pair_ja_en,
    pair_ko_en,
)

# XX → EN (12 reverse expansion pairs)
from . import (  # noqa: F401
    pair_zh_en,
    pair_ar_en,
    pair_ru_en,
    pair_hi_en,
    pair_id_en,
    pair_vi_en,
    pair_th_en,
    pair_tr_en,
    pair_it_en,
    pair_nl_en,
    pair_fa_en,
    pair_ur_en,
)


ALL_PAIRS: tuple[LanguagePair, ...] = (
    # EN → core 14
    pair_en_es.PAIR,
    pair_en_fr.PAIR,
    pair_en_de.PAIR,
    pair_en_it.PAIR,
    pair_en_pt.PAIR,
    pair_en_ja.PAIR,
    pair_en_ko.PAIR,
    pair_en_zh.PAIR,
    pair_en_ru.PAIR,
    pair_en_ar.PAIR,
    pair_en_hi.PAIR,
    pair_en_nl.PAIR,
    pair_en_sv.PAIR,
    pair_en_tr.PAIR,
    # EN → European / Nordic / Middle East
    pair_en_pl.PAIR,
    pair_en_uk.PAIR,
    pair_en_cs.PAIR,
    pair_en_hu.PAIR,
    pair_en_ro.PAIR,
    pair_en_el.PAIR,
    pair_en_fi.PAIR,
    pair_en_no.PAIR,
    pair_en_da.PAIR,
    pair_en_is.PAIR,
    pair_en_he.PAIR,
    pair_en_fa.PAIR,
    # EN → South Asian
    pair_en_ur.PAIR,
    pair_en_bn.PAIR,
    pair_en_ta.PAIR,
    pair_en_te.PAIR,
    pair_en_ml.PAIR,
    pair_en_pa.PAIR,
    pair_en_gu.PAIR,
    pair_en_mr.PAIR,
    # EN → Southeast Asian
    pair_en_id.PAIR,
    pair_en_ms.PAIR,
    pair_en_vi.PAIR,
    pair_en_th.PAIR,
    pair_en_tl.PAIR,
    # EN → African
    pair_en_sw.PAIR,
    pair_en_zu.PAIR,
    pair_en_am.PAIR,
    pair_en_yo.PAIR,
    # EN → Other European
    pair_en_bg.PAIR,
    pair_en_sr.PAIR,
    pair_en_hr.PAIR,
    pair_en_sk.PAIR,
    pair_en_ca.PAIR,
    pair_en_cy.PAIR,
    pair_en_ga.PAIR,
    # EN → constructed / classical
    pair_en_la.PAIR,
    pair_en_eo.PAIR,
    # XX → EN core 6
    pair_es_en.PAIR,
    pair_pt_en.PAIR,
    pair_fr_en.PAIR,
    pair_de_en.PAIR,
    pair_ja_en.PAIR,
    pair_ko_en.PAIR,
    # XX → EN expansion 12
    pair_zh_en.PAIR,
    pair_ar_en.PAIR,
    pair_ru_en.PAIR,
    pair_hi_en.PAIR,
    pair_id_en.PAIR,
    pair_vi_en.PAIR,
    pair_th_en.PAIR,
    pair_tr_en.PAIR,
    pair_it_en.PAIR,
    pair_nl_en.PAIR,
    pair_fa_en.PAIR,
    pair_ur_en.PAIR,
)

_BY_ID: dict[str, LanguagePair] = {p.id: p for p in ALL_PAIRS}


def get_pair(pair_id: str) -> LanguagePair | None:
    return _BY_ID.get(pair_id)


def list_pairs() -> tuple[LanguagePair, ...]:
    return ALL_PAIRS
