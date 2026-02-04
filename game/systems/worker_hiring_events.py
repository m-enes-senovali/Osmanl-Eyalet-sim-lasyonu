# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İşçi İstihdam Olayları
Tarihi bağlamda iş görüşmesi senaryoları
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
from game.systems.workers import WorkerType


@dataclass
class CandidateProfile:
    """Aday işçi profili"""
    id: str
    name_suggestion: str  # Önerilen isim
    worker_type: WorkerType
    title: str  # Görüşme başlığı
    description: str  # Adayın hikayesi
    skill_level: int  # 1-5
    base_cost: int  # Temel maliyet
    loyalty_modifier: int  # Sadakat bonusu (-20 ile +20 arası)
    efficiency_modifier: float  # Verimlilik çarpanı (0.8 - 1.5)
    special_trait: str  # Özel özellik
    hidden_info: str  # "Sına" seçeneğiyle ortaya çıkan bilgi
    
    # Seçenek metinleri (özelleştirilebilir)
    hire_text: str = "İşe al"
    test_text: str = "Sına, bir süre gözlemle"
    reject_text: str = "Reddet"


# ============== ÇİFTÇİ ADAYLARI ==============

FARMER_CANDIDATES = [
    CandidateProfile(
        id="farmer_young_village",
        name_suggestion="Hasan",
        worker_type=WorkerType.FARMER,
        title="Köyden Gelen Genç",
        description="20 yaşında bir delikanlı kapınıza geldi. Güneşten yanmış yüzü, "
                    "nasırlı elleri belli ki toprağa yabancı değil. 'Bey'im, babam da "
                    "çiftçiydi. Bu toprakları avucumun içi gibi bilirim. Beni alın, "
                    "sizi mahcup etmem' diyor.",
        skill_level=1,
        base_cost=60,
        loyalty_modifier=10,
        efficiency_modifier=1.0,
        special_trait="Hızlı öğrenir",
        hidden_info="Çalışkan ve sadık görünüyor. Ailesi bu köyde nesilleridir yaşıyor."
    ),
    CandidateProfile(
        id="farmer_experienced",
        name_suggestion="Mahmut",
        worker_type=WorkerType.FARMER,
        title="Tecrübeli Rençper",
        description="50'li yaşlarda, sakalları ağarmış bir adam. '30 yıldır bu "
                    "toprakları sürüyorum Bey'im. Hangi tohumun ne zaman ekilmesi "
                    "gerektiğini, yağmurun ne zaman yağacağını bilirim. Yaşlıyım ama "
                    "işimi bilirim' diyor.",
        skill_level=3,
        base_cost=120,
        loyalty_modifier=15,
        efficiency_modifier=1.3,
        special_trait="Hasat ustası",
        hidden_info="Gerçekten deneyimli. Ama yaşı ilerlemiş, en fazla 10 yıl çalışabilir."
    ),
    CandidateProfile(
        id="farmer_refugee_family",
        name_suggestion="Mustafa",
        worker_type=WorkerType.FARMER,
        title="Savaştan Kaçan Aile",
        description="Sınır bölgesinden gelen bir aile. Aile reisi 'Bey'im, savaş "
                    "topraklarımızı yok etti. Karım, 3 çocuğum var. Bize bir şans "
                    "verin, gece gündüz çalışırız. Sadece aç kalmayalım' diyor. "
                    "Gözlerinde çaresizlik var.",
        skill_level=2,
        base_cost=30,
        loyalty_modifier=-5,
        efficiency_modifier=1.1,
        special_trait="Aile bağları",
        hidden_info="Zor günler geçirmişler ama çalışkanlıkları şüphesiz. Sadakat zamanla artar.",
        hire_text="Kabul et, toprak ver",
        test_text="Bir hafta misafir et, gözlemle",
        reject_text="Yol ver, gidemezler"
    ),
    CandidateProfile(
        id="farmer_nomad",
        name_suggestion="Yörük Ali",
        worker_type=WorkerType.FARMER,
        title="Yerleşmek İsteyen Yörük",
        description="Bir Yörük ailesi yerleşik hayata geçmek istiyor. 'Bey'im, "
                    "artık çadırda yaşamaktan yorulduk. Koyunlarımızı satıp toprak "
                    "almak istiyoruz. Hayvanları da biliriz, tarla da süreriz' diyor "
                    "yaşlı aile reisi.",
        skill_level=2,
        base_cost=80,
        loyalty_modifier=5,
        efficiency_modifier=1.0,
        special_trait="Hayvancılık bilgisi",
        hidden_info="Göçebe geçmişleri var ama yerleşmeye kararlılar. Koyun yetiştirmede ustalar."
    ),
    CandidateProfile(
        id="farmer_soldier_veteran",
        name_suggestion="Kemal",
        worker_type=WorkerType.FARMER,
        title="Emekli Sipahi",
        description="Eski bir sipahi, artık savaşamayacak kadar yaşlanmış. "
                    "'Bey'im, kılıcımı toprağa gömdüm. Artık saban tutmak istiyorum. "
                    "Tımar'ım için çiftçilik yaptım, bilmez değilim. Huzur içinde "
                    "yaşlanmak istiyorum' diyor.",
        skill_level=2,
        base_cost=100,
        loyalty_modifier=20,
        efficiency_modifier=0.9,
        special_trait="Disiplinli",
        hidden_info="Sadakati çok yüksek, devlete hizmeti kanıtlanmış. Ama yaşı ilerlemiş."
    ),
    CandidateProfile(
        id="farmer_orphan",
        name_suggestion="Küçük Ahmet",
        worker_type=WorkerType.FARMER,
        title="Yetim Çocuk",
        description="12-13 yaşlarında, üstü başı perişan bir çocuk. 'Bey'im, "
                    "annem babam vebadan öldü. Sokaklarda yaşıyorum. Ne iş verirseniz "
                    "yaparım, yeter ki aç kalmayayım' diyor. Gözleri dolu dolu.",
        skill_level=1,
        base_cost=20,
        loyalty_modifier=15,
        efficiency_modifier=0.7,
        special_trait="Gelişme potansiyeli",
        hidden_info="Çok genç ama yetiştirirsen sadık bir işçi olur. Şimdilik verimli değil.",
        hire_text="Yanına al, büyüt",
        test_text="Bir hafta yemek ver, gözlemle",
        reject_text="Başka kapı göster"
    ),
]


# ============== MADENCİ ADAYLARI ==============

MINER_CANDIDATES = [
    CandidateProfile(
        id="miner_strong_youth",
        name_suggestion="Hamza",
        worker_type=WorkerType.MINER,
        title="Güçlü Delikanlı",
        description="Dev yapılı, iri yarı bir genç. Kolları kalın, elleri kocaman. "
                    "'Bey'im, dağları delebilirim! Güçlüyüm, dayanıklıyım. Maden "
                    "tehlikeli iş ama korkmam. Bana bir kazma verin, gerisini ben "
                    "hallederim' diyor özgüvenle.",
        skill_level=1,
        base_cost=100,
        loyalty_modifier=0,
        efficiency_modifier=1.2,
        special_trait="Güçlü kuvvetli",
        hidden_info="Gücü yerinde ama madencilik bilmiyor. Öğrenmesi gerekecek."
    ),
    CandidateProfile(
        id="miner_old_master",
        name_suggestion="Usta Recep",
        worker_type=WorkerType.MINER,
        title="Eski Maden Ustası",
        description="60'lı yaşlarda, yüzü kararmış, sırtı kamburlaşmış bir adam. "
                    "'Bey'im, 40 yıl maden ocağında çalıştım. Hangi taş nereye vurulur, "
                    "hangi damar zengindir bilirim. Bu yaşta bile gençlerden iyi iş "
                    "çıkarırım' diyor.",
        skill_level=4,
        base_cost=200,
        loyalty_modifier=10,
        efficiency_modifier=1.4,
        special_trait="Damar bulma",
        hidden_info="Gerçek bir usta. Ama sağlığı kötü, madencilik ciğerlerini yıpratmış."
    ),
    CandidateProfile(
        id="miner_freed_slave",
        name_suggestion="Köle Hüseyin",
        worker_type=WorkerType.MINER,
        title="Azat Edilmiş Köle",
        description="Efendisi tarafından azat edilmiş bir köle. 'Bey'im, "
                    "özgürlüğümü yeni kazandım. Maden ocağında çalıştırıldım yıllarca. "
                    "Artık özgür bir işçi olarak çalışmak istiyorum. Madenciliği iyi "
                    "bilirim' diyor.",
        skill_level=3,
        base_cost=80,
        loyalty_modifier=20,
        efficiency_modifier=1.2,
        special_trait="Dayanıklı",
        hidden_info="Zor şartlara alışık. Özgürlüğüne düşkün, iyi davranılırsa çok sadık olur."
    ),
    CandidateProfile(
        id="miner_balkan",
        name_suggestion="Yorgi",
        worker_type=WorkerType.MINER,
        title="Balkan Madencisi",
        description="Balkan dağlarından gelmiş bir Rum madenci. 'Efendim, "
                    "memleketimde gümüş madeni işlettim. Osmanlı adaletine sığındım. "
                    "Sizin madenlerinizde çalışmak isterim' diyor kırık Türkçesiyle.",
        skill_level=3,
        base_cost=150,
        loyalty_modifier=5,
        efficiency_modifier=1.3,
        special_trait="Gümüş uzmanlığı",
        hidden_info="Gerçekten bilgili. Ama yabancı olması bazı işçilerle sürtüşmeye yol açabilir."
    ),
    CandidateProfile(
        id="miner_desperate",
        name_suggestion="Mahmut",
        worker_type=WorkerType.MINER,
        title="Çaresiz Adam",
        description="Borçlu bir adam, alacaklılardan kaçıyor. 'Bey'im, beni sakla, "
                    "maden ocağında çalışayım. Kimse aramaz orada. Ne verirsen veririm, "
                    "yeter ki borçlular beni bulmasın' diyor korku içinde.",
        skill_level=1,
        base_cost=40,
        loyalty_modifier=-10,
        efficiency_modifier=0.9,
        special_trait="Gözlerden uzak",
        hidden_info="Borçları ciddi. Alacaklılar gelirse sorun çıkabilir. Ama ucuz işgücü."
    ),
]


# ============== ODUNCU ADAYLARI ==============

LUMBERJACK_CANDIDATES = [
    CandidateProfile(
        id="lumber_forest_boy",
        name_suggestion="Orman Ali",
        worker_type=WorkerType.LUMBERJACK,
        title="Orman Çocuğu",
        description="Ormanlık bölgede büyümüş bir genç. 'Bey'im, ormanda doğdum, "
                    "ormanda büyüdüm. Hangi ağaç sağlamdır, hangisi içi çürüktür bilirim. "
                    "Balta kullanmayı beşikte öğrendim' diyor gururla.",
        skill_level=2,
        base_cost=80,
        loyalty_modifier=5,
        efficiency_modifier=1.2,
        special_trait="Ağaç bilgisi",
        hidden_info="Gerçekten ormancılık biliyor. Sadık ve çalışkan görünüyor."
    ),
    CandidateProfile(
        id="lumber_ship_builder",
        name_suggestion="Kaptan Osman",
        worker_type=WorkerType.LUMBERJACK,
        title="Eski Tersane İşçisi",
        description="Tersaneden ayrılmış bir marangoz. 'Bey'im, gemi yapımında "
                    "çalıştım yıllarca. Hangi ağaç gövde için, hangisi direk için "
                    "uygun bilirim. Artık tersane değil, orman istiyorum' diyor.",
        skill_level=3,
        base_cost=180,
        loyalty_modifier=10,
        efficiency_modifier=1.3,
        special_trait="Kaliteli kereste",
        hidden_info="Kaliteli kereste seçimi konusunda uzman. Tersaneden iyi ayrılmış."
    ),
    CandidateProfile(
        id="lumber_woodcutter_family",
        name_suggestion="Baltacı Veli",
        worker_type=WorkerType.LUMBERJACK,
        title="Baltacı Ailesi",
        description="Nesiller boyu odunculuk yapan bir aile. 'Bey'im, dedem de "
                    "oduncuydu, babam da. Bu meslek kanımızda var. Ormanı koruyarak "
                    "kesmesini biliriz. Gelecek nesle de orman bırakırız' diyor.",
        skill_level=2,
        base_cost=120,
        loyalty_modifier=15,
        efficiency_modifier=1.1,
        special_trait="Sürdürülebilir kesim",
        hidden_info="Ormanı tüketmeden kullanma konusunda bilinçli. Uzun vadede faydalı."
    ),
    CandidateProfile(
        id="lumber_bandit_reformed",
        name_suggestion="Kara Murat",
        worker_type=WorkerType.LUMBERJACK,
        title="Tövbekâr Eşkıya",
        description="Dağlarda eşkıyalık yapmış, şimdi af istiyor. 'Bey'im, gençliğimde "
                    "yanlış yola saptım. Şimdi tövbe ettim, dürüst yaşamak istiyorum. "
                    "Ormanlarda yaşadım, balta kullanmayı bilirim' diyor pişmanlıkla.",
        skill_level=2,
        base_cost=50,
        loyalty_modifier=-15,
        efficiency_modifier=1.1,
        special_trait="Orman bilgisi",
        hidden_info="Gerçekten tövbe etmiş mi belli değil. Risk var ama ormancılık biliyor.",
        hire_text="Af et, işe al",
        test_text="Gözetim altında dene",
        reject_text="Kadıya teslim et"
    ),
]


# ============== ZANAATKAR ADAYLARI ==============

CRAFTSMAN_CANDIDATES = [
    CandidateProfile(
        id="craft_guild_apprentice",
        name_suggestion="Kalfa İbrahim",
        worker_type=WorkerType.CRAFTSMAN,
        title="Lonca Kalfası",
        description="Bir ustanın yanından mezun olmuş kalfa. 'Bey'im, 7 yıl "
                    "ustamın yanında çalıştım. Kalfalık icazetimi aldım. Şimdi kendi "
                    "işimi kurmak istiyorum ama sermayem yok. Sizin himayenizde "
                    "çalışabilirim' diyor.",
        skill_level=2,
        base_cost=200,
        loyalty_modifier=10,
        efficiency_modifier=1.1,
        special_trait="Lonca ağı",
        hidden_info="Lonca bağlantıları var, ticaret için faydalı olabilir. Eğitimli."
    ),
    CandidateProfile(
        id="craft_traveling_master",
        name_suggestion="Seyyah Yusuf",
        worker_type=WorkerType.CRAFTSMAN,
        title="Gezgin Usta",
        description="Her şehirde farklı ustalık öğrenmiş gezgin bir zanaatkar. "
                    "'Bey'im, İstanbul'da çinicilik, Bursa'da ipekçilik, Şam'da "
                    "kılıç dövme öğrendim. Her işten anlarım. Artık bir yere "
                    "yerleşmek istiyorum' diyor.",
        skill_level=4,
        base_cost=400,
        loyalty_modifier=5,
        efficiency_modifier=1.4,
        special_trait="Çok yönlü",
        hidden_info="Gerçekten çok yetenekli ama yerinde duramaz. Sıkılırsa gidebilir."
    ),
    CandidateProfile(
        id="craft_family_tradition",
        name_suggestion="Fuat",
        worker_type=WorkerType.CRAFTSMAN,
        title="Usta Çırağı",
        description="Babası ünlü bir demirci ustası. 'Bey'im, babam Topkapı'nın "
                    "demirlerini döven ustanın çırağıydı. Bu sanat bize miras kaldı. "
                    "Ailemizin şanını sürdürmek istiyorum' diyor.",
        skill_level=3,
        base_cost=280,
        loyalty_modifier=15,
        efficiency_modifier=1.2,
        special_trait="Demir işçiliği",
        hidden_info="Demir işlemede gerçekten usta. Ailesine bağlı, kaçmaz."
    ),
    CandidateProfile(
        id="craft_persian",
        name_suggestion="Mirza Rıza",
        worker_type=WorkerType.CRAFTSMAN,
        title="İranlı Halıcı",
        description="İran'dan kaçmış bir halı ustası. 'Efendim, Safevi sarayına "
                    "halı dokuyordum. Ama mezhep yüzünden kaçmak zorunda kaldım. "
                    "Osmanlı'ya sığındım. Sanatımı sizin için icra edebilirim' diyor.",
        skill_level=4,
        base_cost=350,
        loyalty_modifier=10,
        efficiency_modifier=1.5,
        special_trait="İran halıcılığı",
        hidden_info="Gerçekten usta bir halıcı. Mezhep meselesi sorun çıkarabilir."
    ),
    CandidateProfile(
        id="craft_woman_weaver",
        name_suggestion="Hatice Kadın",
        worker_type=WorkerType.CRAFTSMAN,
        title="Dokumacı Kadın",
        description="Kocasını kaybetmiş, dul bir kadın. 'Bey'im, kocam öldü, "
                    "çocuklarımı beslemek için çalışmalıyım. Dokumacılık bilirim, "
                    "annem öğretti. Evde çalışabilirim' diyor çekingen.",
        skill_level=2,
        base_cost=100,
        loyalty_modifier=20,
        efficiency_modifier=1.0,
        special_trait="Hassas işçilik",
        hidden_info="Çok titiz çalışıyor. Kadın olması bazı lonca kurallarıyla çelişebilir."
    ),
]


# ============== TÜCCAR ADAYLARI ==============

MERCHANT_CANDIDATES = [
    CandidateProfile(
        id="merchant_young_ambitious",
        name_suggestion="Tacir Selim",
        worker_type=WorkerType.MERCHANT,
        title="Hırslı Genç Tüccar",
        description="Zengin bir ailenin oğlu, ticarete meraklı. 'Bey'im, babam "
                    "beni okuttu ama ben ticaret istiyorum. Hesap kitap bilirim, "
                    "Arapça, Farsça, biraz Rumca konuşurum. Para kazanmak istiyorum' "
                    "diyor hevesle.",
        skill_level=2,
        base_cost=200,
        loyalty_modifier=0,
        efficiency_modifier=1.1,
        special_trait="Dil bilgisi",
        hidden_info="Eğitimli ama deneyimsiz. Hırslı, kazanç için risk alabilir."
    ),
    CandidateProfile(
        id="merchant_caravan_leader",
        name_suggestion="Kervanbaşı Halil",
        worker_type=WorkerType.MERCHANT,
        title="Kervan Başı",
        description="Yıllarca kervan yönetmiş tecrübeli bir tüccar. 'Bey'im, "
                    "İpek Yolu'nu defalarca geçtim. Hangi malın nerede değerli "
                    "olduğunu, hangi yolun güvenli olduğunu bilirim. Artık "
                    "yerleşik ticaret yapmak istiyorum' diyor.",
        skill_level=4,
        base_cost=400,
        loyalty_modifier=10,
        efficiency_modifier=1.4,
        special_trait="Ticaret yolları",
        hidden_info="Çok deneyimli ve güvenilir. Geniş bir ticaret ağı var."
    ),
    CandidateProfile(
        id="merchant_jewish",
        name_suggestion="Samuel",
        worker_type=WorkerType.MERCHANT,
        title="Yahudi Sarraf",
        description="İspanya'dan sürülmüş bir Yahudi tüccar ailesi. 'Efendim, "
                    "Sultan Bayezid bizi kabul etti. Sarraflık, bankacılık biliriz. "
                    "Avrupa'da bağlantılarımız var. Sizin için çalışabiliriz' diyor.",
        skill_level=3,
        base_cost=300,
        loyalty_modifier=15,
        efficiency_modifier=1.3,
        special_trait="Sarraflık",
        hidden_info="Finansta çok yetenekli. Avrupa bağlantıları değerli. Sadık bir topluluk."
    ),
    CandidateProfile(
        id="merchant_venetian",
        name_suggestion="Antonio",
        worker_type=WorkerType.MERCHANT,
        title="Venedikli Tüccar",
        description="Venedik'le iş yapan bir Levanten tüccar. 'Signore, ben "
                    "Venedik'le Osmanlı arasında köprüyüm. Deniz ticareti, "
                    "sigortacılık bilirim. İki tarafın da güvenini kazandım' diyor.",
        skill_level=3,
        base_cost=350,
        loyalty_modifier=-5,
        efficiency_modifier=1.3,
        special_trait="Deniz ticareti",
        hidden_info="Venedik bağlantısı değerli ama sadakati sorgulanabilir. Çift taraflı çalışabilir."
    ),
]


# ============== ELÇİ/DİPLOMAT ADAYLARI ==============

ENVOY_CANDIDATES = [
    CandidateProfile(
        id="envoy_scholar",
        name_suggestion="Müderris Cemil",
        worker_type=WorkerType.ENVOY,
        title="Medrese Müderrisi",
        description="Medreseden ayrılmış bir âlim. 'Bey'im, İslam hukuku ve "
                    "edebiyat öğrettim yıllarca. Dil bilgim kuvvetli, hitabetim "
                    "güçlü. Diplomasi için bu yeteneklerimi kullanabilirim' diyor.",
        skill_level=3,
        base_cost=350,
        loyalty_modifier=15,
        efficiency_modifier=1.2,
        special_trait="Hitabet",
        hidden_info="Eğitimli ve güvenilir. Dini meselelerde de danışılabilir."
    ),
    CandidateProfile(
        id="envoy_ex_janissary",
        name_suggestion="Mehmet Çavuş",
        worker_type=WorkerType.ENVOY,
        title="Emekli Yeniçeri Çavuşu",
        description="Ocaktan emekli bir çavuş. 'Bey'im, orduda çavuşluk yaptım. "
                    "Emirleri iletmek, müzakere etmek, habercilik benim işim. "
                    "Artık silah değil söz taşımak istiyorum' diyor.",
        skill_level=2,
        base_cost=250,
        loyalty_modifier=20,
        efficiency_modifier=1.1,
        special_trait="Disiplin",
        hidden_info="Çok sadık ve güvenilir. Askeri temaslar için ideal."
    ),
    CandidateProfile(
        id="envoy_interpreter",
        name_suggestion="Tercüman İlyas",
        worker_type=WorkerType.ENVOY,
        title="Divan Tercümanı",
        description="Divan-ı Hümayun'da tercümanlık yapmış. 'Bey'im, 7 dil "
                    "bilirim: Türkçe, Arapça, Farsça, Rumca, Latince, İtalyanca, "
                    "Slavca. Padişahın huzurunda tercümanlık yaptım. Şimdi eyalet "
                    "hizmetinde çalışmak istiyorum' diyor.",
        skill_level=4,
        base_cost=500,
        loyalty_modifier=10,
        efficiency_modifier=1.5,
        special_trait="Çok dilli",
        hidden_info="Gerçekten çok yetenekli. Ama neden saraydan ayrıldı? Belki bir mesele var."
    ),
    CandidateProfile(
        id="envoy_merchant_son",
        name_suggestion="Hasan",
        worker_type=WorkerType.ENVOY,
        title="Tüccar Oğlu",
        description="Zengin bir tüccarın eğitimli oğlu. 'Bey'im, babam beni "
                    "diplomasi için yetiştirdi. Müzakere, ikna, pazarlık benim "
                    "işim. Ticaret yerine devlet hizmetinde çalışmak istiyorum' diyor.",
        skill_level=2,
        base_cost=280,
        loyalty_modifier=5,
        efficiency_modifier=1.1,
        special_trait="Pazarlık ustası",
        hidden_info="Ticaret ailesi bağlantıları var. Müzakere yeteneği iyi."
    ),
]


# Tüm adayları birleştir
ALL_CANDIDATES = {
    WorkerType.FARMER: FARMER_CANDIDATES,
    WorkerType.MINER: MINER_CANDIDATES,
    WorkerType.LUMBERJACK: LUMBERJACK_CANDIDATES,
    WorkerType.CRAFTSMAN: CRAFTSMAN_CANDIDATES,
    WorkerType.MERCHANT: MERCHANT_CANDIDATES,
    WorkerType.ENVOY: ENVOY_CANDIDATES,
}


def get_random_candidate(worker_type: WorkerType) -> CandidateProfile:
    """Belirli türde rastgele aday al"""
    candidates = ALL_CANDIDATES.get(worker_type, [])
    if not candidates:
        return None
    return random.choice(candidates)


def get_all_candidates_for_type(worker_type: WorkerType) -> List[CandidateProfile]:
    """Belirli türdeki tüm adayları al"""
    return ALL_CANDIDATES.get(worker_type, [])


def get_candidate_by_id(candidate_id: str) -> Optional[CandidateProfile]:
    """ID'ye göre aday bul"""
    for candidates in ALL_CANDIDATES.values():
        for candidate in candidates:
            if candidate.id == candidate_id:
                return candidate
    return None


# Görüşme durumu
@dataclass
class InterviewState:
    """Görüşme durumu"""
    candidate: CandidateProfile
    is_testing: bool = False  # "Sına" seçildiyse True
    turns_remaining: int = 0  # Test turları
    custom_name: str = ""  # Oyuncunun verdiği isim
    hired: bool = False
    rejected: bool = False
