# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Unvan ve Hitap Sistemi
Cinsiyete göre uygun unvan ve hitap formları
"""

from enum import Enum
from typing import Optional


class TitleContext(Enum):
    """Unvan bağlamları"""
    GOVERNOR = "governor"           # Vali unvanı
    GENERAL = "general"             # Genel hitap
    FROM_SULTAN = "from_sultan"     # Padişah'tan
    FROM_PEOPLE = "from_people"     # Halktan
    FROM_SOLDIER = "from_soldier"   # Askerden
    FROM_BEY = "from_bey"           # Beylerden
    FROM_ULEMA = "from_ulema"       # Ulemadan
    FORMAL = "formal"               # Resmi yazışma
    SELF = "self"                   # Kendinden bahsederken


# Unvan tablosu: {bağlam: {cinsiyet: unvan}}
# Tarihi doğruluk: İsim + Unvan formatı (Mehmed Paşa, Mihrimah Hatun)
TITLE_TABLE = {
    TitleContext.GOVERNOR: {
        'male': "Paşa",
        'female': "Hatun"
    },
    TitleContext.GENERAL: {
        'male': "Beyefendi",
        'female': "Hanımefendi"
    },
    TitleContext.FROM_SULTAN: {
        'male': "Paşam",
        'female': "Hatun Hazretleri"
    },
    TitleContext.FROM_PEOPLE: {
        'male': "Paşa Efendimiz",
        'female': "Hatun Efendimiz"
    },
    TitleContext.FROM_SOLDIER: {
        'male': "Komutanım",
        'female': "Hanım Komutan"
    },
    TitleContext.FROM_BEY: {
        'male': "Paşa Hazretleri",
        'female': "Hatun Hazretleri"
    },
    TitleContext.FROM_ULEMA: {
        'male': "Devletlü Paşam",
        'female': "Devletlü Hatun"
    },
    TitleContext.FORMAL: {
        'male': "Vali",
        'female': "Vali"
    },
    TitleContext.SELF: {
        'male': "Ben, Vali",
        'female': "Ben, Vali"
    },
}


# Fiil çekimleri (3. tekil şahıs hitap)
VERB_FORMS = {
    'ordered': {
        'male': "emretti",
        'female': "emretti"  # Türkçe'de cinsiyet farkı yok
    },
    'said': {
        'male': "dedi",
        'female': "dedi"
    },
    'decided': {
        'male': "karar verdi",
        'female': "karar verdi"
    },
}


# Sıfatlar ve zamirler
PRONOUNS = {
    'possessive': {
        'male': "onun",
        'female': "onun"  # Türkçe'de cinsiyet farkı yok
    },
    'subject': {
        'male': "o",
        'female': "o"
    },
    'object': {
        'male': "onu",
        'female': "onu"
    },
}


# Rol isimleri
ROLE_NAMES = {
    'ruler': {
        'male': "Yönetici",
        'female': "Yönetici"
    },
    'commander': {
        'male': "Komutan",
        'female': "Komutan"
    },
    'leader': {
        'male': "Lider",
        'female': "Lider"
    },
    'patron': {
        'male': "Hamî",
        'female': "Hamiye"
    },
    'benefactor': {
        'male': "Hayırsever",
        'female': "Hayırsever Hatun"
    },
}


def get_title(context: str, gender) -> str:
    """
    Bağlama ve cinsiyete göre unvan döndür
    
    Args:
        context: Bağlam adı (string veya TitleContext)
        gender: Cinsiyet (Gender enum veya string)
    
    Returns:
        Uygun unvan string'i
    """
    # Context'i enum'a çevir
    if isinstance(context, str):
        try:
            context = TitleContext(context)
        except ValueError:
            context = TitleContext.GENERAL
    
    # Gender'ı string'e çevir
    if hasattr(gender, 'value'):
        gender_str = gender.value
    else:
        gender_str = str(gender)
    
    # Tabloda ara
    if context in TITLE_TABLE:
        return TITLE_TABLE[context].get(gender_str, TITLE_TABLE[context]['male'])
    
    return "Efendim"


def get_role_name(role: str, gender) -> str:
    """Rol ismi döndür"""
    if hasattr(gender, 'value'):
        gender_str = gender.value
    else:
        gender_str = str(gender)
    
    if role in ROLE_NAMES:
        return ROLE_NAMES[role].get(gender_str, ROLE_NAMES[role]['male'])
    
    return role


def format_address(template: str, player_name: str, gender) -> str:
    """
    Şablon metni karaktere göre formatla
    
    Desteklenen yer tutucular:
    - {name}: Karakter ismi
    - {title}: Genel unvan
    - {governor}: Vali unvanı
    - {from_sultan}: Padişah hitabı
    - {from_people}: Halk hitabı
    - {from_soldier}: Asker hitabı
    
    Örnek:
        format_address("{name} {governor}, halkınız sizi seviyor!", "Mihrimah", Gender.FEMALE)
        -> "Mihrimah Vali Hatun, halkınız sizi seviyor!"
    """
    result = template
    
    result = result.replace("{name}", player_name)
    result = result.replace("{title}", get_title("general", gender))
    result = result.replace("{governor}", get_title("governor", gender))
    result = result.replace("{from_sultan}", get_title("from_sultan", gender))
    result = result.replace("{from_people}", get_title("from_people", gender))
    result = result.replace("{from_soldier}", get_title("from_soldier", gender))
    result = result.replace("{from_bey}", get_title("from_bey", gender))
    result = result.replace("{from_ulema}", get_title("from_ulema", gender))
    result = result.replace("{benefactor}", get_role_name("benefactor", gender))
    
    return result


# Olay metinleri için yardımcı
def get_event_greeting(gender) -> str:
    """Olay başlangıcı için selamlama"""
    if hasattr(gender, 'value'):
        gender_str = gender.value
    else:
        gender_str = str(gender)
    
    if gender_str == "female":
        return "Hatun Hazretleri,"
    return "Paşam,"


def get_respectful_address(gender) -> str:
    """Saygılı hitap"""
    if hasattr(gender, 'value'):
        gender_str = gender.value
    else:
        gender_str = str(gender)
    
    if gender_str == "female":
        return "Muhterem Hanımefendi"
    return "Muhterem Beyefendi"
