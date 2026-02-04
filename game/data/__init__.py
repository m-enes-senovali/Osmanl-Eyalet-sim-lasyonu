# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Oyun Verileri
"""

from game.data.territories import (
    TERRITORIES,
    PLAYABLE_TERRITORIES,
    ALL_TERRITORY_NAMES,
    Territory,
    TerritoryType,
    Region,
    get_territory,
    get_neighbors_with_direction,
    get_all_neighbors,
    get_territories_by_type,
    get_territories_by_region
)

__all__ = [
    'TERRITORIES',
    'PLAYABLE_TERRITORIES',
    'ALL_TERRITORY_NAMES',
    'Territory',
    'TerritoryType',
    'Region',
    'get_territory',
    'get_neighbors_with_direction',
    'get_all_neighbors',
    'get_territories_by_type',
    'get_territories_by_region'
]
