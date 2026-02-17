# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Genişletilmiş Olaylar
30+ yeni tarihsel ve tematik olay
"""

from game.systems.events import (
    Event, EventType, EventSeverity, EventChoice, EventStage, EventChain
)


# Koşul fonksiyonları
def has_high_gold(game_state: dict) -> bool:
    """Hazine 50000 altından fazla mı?"""
    return game_state.get('gold', 0) >= 50000


def has_low_loyalty(game_state: dict) -> bool:
    """Sadakat %40'ın altında mı?"""
    return game_state.get('loyalty', 100) < 40


def has_strong_army(game_state: dict) -> bool:
    """Ordu gücü 5000 üzerinde mi?"""
    return game_state.get('army_strength', 0) >= 5000


def has_navy(game_state: dict) -> bool:
    """Donanma var mı?"""
    return game_state.get('total_ships', 0) >= 10


def is_at_war(game_state: dict) -> bool:
    """Savaşta mı?"""
    return game_state.get('at_war', False)


def has_trade_routes(game_state: dict) -> bool:
    """Ticaret yolu var mı?"""
    return game_state.get('trade_routes', 0) >= 3


# ============== TARİHSEL OLAYLAR ==============

HISTORICAL_EVENTS = [
    # Kanuni Dönemi
    Event(
        id="kanuni_throne",
        title="Kanuni Sultan Süleyman'ın Tahta Çıkışı",
        description="1520 yılında Sultan Selim Han vefat etti. Taht, oğlu Süleyman'a geçiyor. "
                    "Yeni padişahın ilk emirleri hazırlanıyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Adalet fermanı yayınla",
                effects={'loyalty': 15, 'gold': -2000, 'legitimacy': 10},
                description="Halk memnuniyeti artar ama hazineden ödeme yapılır."
            ),
            EventChoice(
                text="Ordu seferberliği ilan et",
                effects={'military_strength': 20, 'loyalty': -5},
                description="Ordu güçlenir ama halk tedirginleşir."
            ),
            EventChoice(
                text="Saray düzenlemesi yap",
                effects={'gold': -5000, 'efficiency': 10},
                description="İdari verimlilik artar."
            ),
        ],
        min_turn=1,
        max_year=1521
    ),
    
    Event(
        id="belgrade_campaign",
        title="Belgrad Kuşatması",
        description="1521 yılı, Belgrad kalesi Osmanlı'nın hedefi olmuştur. "
                    "Bu güçlü kale düşerse Avrupa'nın kapısı açılacak.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Tam kuvvetle kuşat",
                effects={'gold': -10000, 'army_strength': -1000, 'prestige': 25},
                description="Büyük zafer ama ağır kayıplar.",
                next_stage="belgrade_victory"
            ),
            EventChoice(
                text="Diplomatik yol dene",
                effects={'diplomacy_points': 10, 'gold': -3000},
                description="Barış görüşmeleri başlar.",
                next_stage="belgrade_diplomacy"
            ),
            EventChoice(
                text="Kuşatmayı ertele",
                effects={'prestige': -10},
                description="Fırsat kaçar ama kaynak korunur."
            ),
        ],
        min_turn=5,
        condition_func=has_strong_army,
        chain_id="balkan_wars"
    ),
    
    Event(
        id="rhodes_campaign",
        title="Rodos Seferi",
        description="1522 yılı, Saint Jean Şövalyeleri'nin kalesi Rodos. "
                    "Akdeniz hakimiyeti için bu kale düşmeli.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Deniz ve karadan kuşat",
                effects={'gold': -15000, 'navy_strength': -500, 'prestige': 30},
                description="Büyük zafer! Akdeniz'e hakim oldun."
            ),
            EventChoice(
                text="Sadece abluka uygula",
                effects={'gold': -5000, 'trade_income': 5},
                description="Ekonomik baskı uygula."
            ),
        ],
        min_turn=10,
        condition_func=has_navy
    ),
    
    Event(
        id="mohac_battle",
        title="Mohaç Savaşı",
        description="1526 yılı, Macar Kralı Ludwig karşında. Bu savaş Orta Avrupa'nın "
                    "kaderini belirleyecek.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Tüm gücünle saldır",
                effects={'gold': -20000, 'army_strength': -2000, 'prestige': 50, 'territory': 2},
                description="Büyük zafer! Budapeşte ve Macaristan senin."
            ),
            EventChoice(
                text="Akıncı taktikleri kullan",
                effects={'gold': -8000, 'loot': 5000, 'prestige': 25},
                description="Düşmanı yıprat ve hazineyi doldur."
            ),
        ],
        min_turn=15,
        condition_func=has_strong_army,
        chain_id="hungarian_campaign"
    ),
    
    Event(
        id="piri_reis_map",
        title="Piri Reis'in Haritası",
        description="Denizci Piri Reis, dünya haritasını padişaha sundu. "
                    "Bu harita denizcilik tarihinde çığır açacak.",
        event_type=EventType.OPPORTUNITY,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Piri Reis'i ödüllendir",
                effects={'gold': -2000, 'naval_tech': 10, 'prestige': 5},
                description="Denizcilik bilgisi artar."
            ),
            EventChoice(
                text="Denizcilik okulu aç",
                effects={'gold': -5000, 'naval_tech': 20, 'education': 5},
                description="Uzun vadeli denizcilik gelişimi."
            ),
            EventChoice(
                text="Haritayı gizli tut",
                effects={'spy_network': 5},
                description="Stratejik avantaj sağla."
            ),
        ],
        min_turn=8,
        condition_func=has_navy
    ),
    
    Event(
        id="mimar_sinan",
        title="Mimar Sinan'ın Keşfi",
        description="Kayseri'den gelen yetenekli bir mühendis dikkatinizi çekiyor. "
                    "Adı Sinan ve muhteşem projeler vaat ediyor.",
        event_type=EventType.OPPORTUNITY,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Saray mimarı yap",
                effects={'construction_speed': 20, 'prestige': 10},
                description="Sinan gelecek nesillere eser bırakacak."
            ),
            EventChoice(
                text="Askeri mühendis olarak görevlendir",
                effects={'military_tech': 15, 'siege_power': 10},
                description="Kale ve kuşatma teknolojisi gelişir."
            ),
        ],
        min_turn=12
    ),
    
    # ── İkinci Rapor Kaynaklı Yeni Tarihsel Olaylar ──
    
    Event(
        id="canberdi_revolt",
        title="Canberdi Gazali İsyanı",
        description="1521 — Yavuz Sultan Selim'in ölümünden cesaret alan eski Memlûk komutanı "
                    "Canberdi Gazali, Şam'da isyan bayrağı açtı. Memlûk Devleti'ni diriltme "
                    "girişiminde bulunuyor. Mısır ve Şam eyaletlerinde sadakat sarsılıyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Derhal cezai sefer düzenle",
                effects={'gold': -8000, 'army_strength': -500, 'loyalty': 10, 'prestige': 15},
                description="İsyan bastırılır, otoriteniz güçlenir."
            ),
            EventChoice(
                text="Diplomatik çözüm ara, af teklif et",
                effects={'gold': -3000, 'loyalty': -10, 'prestige': -5, 'stability': 5},
                description="Kan dökülmez ama zayıflık olarak algılanır."
            ),
            EventChoice(
                text="Mısır Beylerbeyi'ne görev ver",
                effects={'gold': -2000, 'loyalty': 5, 'administration': 5},
                description="Taşra gücüne güven, merkezi yükü azalt."
            ),
        ],
        min_turn=3,
        max_year=1522,
        chain_id="post_selim_crises"
    ),
    
    Event(
        id="vienna_siege",
        title="Viyana Kuşatması",
        description="1529 — Ordu Viyana surlarına ulaştı. Ancak kış yaklaşıyor, ağır toplar "
                    "çamurda kaldı. Lojistik sınırlar zorlanıyor. 'General Winter' etkisi "
                    "hissediliyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Kuşatmaya devam et — zafer yakın",
                effects={'gold': -25000, 'army_strength': -3000, 'prestige': -15},
                description="Kışta kuşatma riski çok yüksek. Kayıplar büyük olabilir."
            ),
            EventChoice(
                text="Akıllıca geri çekil — prestij koru",
                effects={'gold': -5000, 'prestige': -10, 'stability': 10},
                description="Ordunu koru, gelecek sefere hazırlan."
            ),
            EventChoice(
                text="Taktik değiştir — Akıncı baskınları yap",
                effects={'gold': -8000, 'loot': 3000, 'prestige': 5},
                description="Viyana'yı alamasan da Avusturya'yı yıprat."
            ),
        ],
        min_turn=20,
        condition_func=has_strong_army,
        chain_id="hungarian_campaign"
    ),
    
    Event(
        id="irakeyn_campaign",
        title="Irakeyn Seferi — Bağdat'ın Fethi",
        description="1534 — Safevi İmparatorluğu'na karşı büyük doğu seferi. Tebriz geçici "
                    "olarak alındı, asıl hedef Bağdat. Hz. Hüseyin ve İmam-ı Azam türbeleri "
                    "Osmanlı korumasına alınacak. İpek Yolu kontrolü ele geçecek.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Tam kuvvetle Bağdat'a yürü",
                effects={'gold': -20000, 'army_strength': -1500, 'prestige': 30, 'trade_income': 15},
                description="Bağdat fethedilir, İpek Yolu senin!"
            ),
            EventChoice(
                text="Safevilerle barış yap",
                effects={'gold': -5000, 'diplomacy_points': 15, 'stability': 10},
                description="Sınırı koru, barışı tercih et."
            ),
        ],
        min_turn=30,
        condition_func=has_strong_army,
        chain_id="eastern_wars"
    ),
    
    Event(
        id="prince_mustafa_execution",
        title="Şehzade Mustafa'nın İdamı",
        description="1553 — Konya Ereğlisi'nde Şehzade Mustafa, padişahın huzuruna çağrılarak "
                    "boğduruldu. Orduda büyük infial var. Yeniçeriler isyan tehdidinde. "
                    "Halk arasında 'Düzmece Mustafa' hareketleri baş gösterebilir.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Orduya bahşiş dağıt, morali topla",
                effects={'gold': -15000, 'military_morale': 10, 'loyalty': -15, 'stability': -10},
                description="Yeniçeriler yatışır ama halk tedirgin."
            ),
            EventChoice(
                text="Sert tedbirler al, muhalefeti bastır",
                effects={'order': 20, 'loyalty': -25, 'stability': -20},
                description="Düzen sağlanır ama derin yaralar açılır."
            ),
            EventChoice(
                text="Rüstem Paşa'yı görevden al, günah keçisi yap",
                effects={'loyalty': 5, 'administration': -10, 'prestige': -5},
                description="Halkın öfkesini yönlendir."
            ),
        ],
        min_turn=65,
        chain_id="succession_crisis"
    ),
    
    Event(
        id="prince_bayezid_revolt",
        title="Şehzade Bayezid İsyanı",
        description="1559 — Kardeşi Selim ile taht kavgasını kaybeden Bayezid, Anadolu'da isyan "
                    "bayrağı açtı. Konya yakınlarında mağlup olunca Safevi Şahı Tahmasb'a sığındı. "
                    "İran ile diplomatik kriz — yüklü altın bedeli isteniyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Safevilerle müzakere et, Bayezid'i geri iste",
                effects={'gold': -30000, 'diplomacy_points': -10, 'stability': 15},
                description="Çok pahalı ama çözüm sağlar."
            ),
            EventChoice(
                text="Safeviye savaş ilan et, Bayezid'i zorla al",
                effects={'gold': -20000, 'army_strength': -2000, 'prestige': 10},
                description="Askeri çözüm ama iki cephe riski."
            ),
            EventChoice(
                text="Bayezid'in iadesini diplomatik yollarla sağla",
                effects={'gold': -20000, 'diplomacy_points': 5, 'stability': 10},
                description="Sabırlı diplomasi."
            ),
        ],
        min_turn=78,
        chain_id="succession_crisis",
        triggers_event="prince_mustafa_execution"
    ),
]


# ============== EKONOMİK OLAYLAR ==============

ECONOMIC_EVENTS = [
    Event(
        id="caravan_attack",
        title="Kervan Saldırısı",
        description="Ticaret kervanlarına eşkıyalar saldırdı. Tüccarlar güvenlik istiyor.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Muhafız birliği gönder",
                effects={'gold': -1500, 'trade_income': 10, 'loyalty': 5},
                description="Ticaret yolları güvenli hale gelir."
            ),
            EventChoice(
                text="Eşkıyalarla anlaş",
                effects={'gold': -500, 'loyalty': -5, 'corruption': 5},
                description="Ucuz ama onursuz çözüm."
            ),
            EventChoice(
                text="Tüccarlar kendi başına halletsin",
                effects={'trade_income': -5},
                description="Ticaret azalır."
            ),
        ]
    ),
    
    Event(
        id="gold_mine_discovery",
        title="Altın Madeni Keşfi",
        description="Eyalet topraklarında altın madeni bulundu! Büyük bir servet vaat ediyor.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Devlet madeni olarak işlet",
                effects={'gold': 8000, 'gold_income': 200, 'workers_needed': 50},
                description="Hazine dolacak!"
            ),
            EventChoice(
                text="Mültezime ihale et",
                effects={'gold': 15000, 'gold_income': 50},
                description="Hemen büyük gelir ama uzun vadede az."
            ),
            EventChoice(
                text="Haberi gizle tut",
                effects={'loyalty': -5, 'corruption': 10},
                description="Yolsuzluk fırsatı ama risksiz."
            ),
        ],
        condition_func=has_high_gold
    ),
    
    Event(
        id="famine_threat",
        title="Kıtlık Tehlikesi",
        description="Kuraklık nedeniyle hasat kötü geçti. Halk açlık tehlikesiyle karşı karşıya.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Devlet ambarlarını aç",
                effects={'gold': -5000, 'food': -500, 'loyalty': 15},
                description="Halk kurtulur ama stoklar tükenir."
            ),
            EventChoice(
                text="Dışardan zahire ithal et",
                effects={'gold': -10000, 'food': 200, 'loyalty': 10},
                description="Pahalı ama etkili çözüm."
            ),
            EventChoice(
                text="Vergi affı ilan et",
                effects={'gold_income': -20, 'loyalty': 5},
                description="Geçici rahatlama."
            ),
        ]
    ),
    
    Event(
        id="tax_revolt",
        title="Vergi İsyanı",
        description="Yüksek vergilerden bunalan köylüler ayaklandı. İsyan büyümeden bastırılmalı.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Ordu gönder",
                effects={'loyalty': -20, 'army_strength': -200, 'order': 30},
                description="İsyan bastırılır ama halk öfkelenir."
            ),
            EventChoice(
                text="Vergiyi düşür",
                effects={'tax_rate': -5, 'loyalty': 15},
                description="Halk sakinleşir ama gelir azalır."
            ),
            EventChoice(
                text="Liderlerle görüş",
                effects={'gold': -2000, 'loyalty': 5, 'order': 10},
                description="Rüşvetle çözüm."
            ),
        ],
        condition_func=has_low_loyalty
    ),
    
    Event(
        id="guild_complaint",
        title="Loncaların Şikayeti",
        description="Esnaf loncaları rekabet kurallarından şikayet ediyor. Dükkanlar kapanabilir.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Loncaları destekle",
                effects={'production': 10, 'trade_income': -5, 'loyalty': 5},
                description="Üretim artar ama ticaret kısıtlanır."
            ),
            EventChoice(
                text="Serbest ticareti savun",
                effects={'trade_income': 10, 'production': -5},
                description="Ticaret canlanır."
            ),
        ]
    ),
]


# ============== DOĞAL AFETLER ==============

NATURAL_EVENTS = [
    Event(
        id="earthquake",
        title="Büyük Deprem",
        description="Şiddetli bir deprem şehri vurdu. Binalar yıkıldı, can kayıpları var.",
        event_type=EventType.NATURAL,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Acil yardım gönder",
                effects={'gold': -8000, 'loyalty': 20, 'population': -500},
                description="Halk minnettar ama kayıplar büyük."
            ),
            EventChoice(
                text="Yeniden inşa programı başlat",
                effects={'gold': -15000, 'construction': 5, 'loyalty': 10},
                description="Uzun vadeli iyileşme."
            ),
        ]
    ),
    
    Event(
        id="flood",
        title="Sel Baskını",
        description="Nehir taştı, ovalar su altında. Tarım alanları zarar gördü.",
        event_type=EventType.NATURAL,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Baraj inşa et",
                effects={'gold': -10000, 'food': -200, 'infrastructure': 15},
                description="Gelecekte benzer felaketler önlenir."
            ),
            EventChoice(
                text="Köylülere yardım dağıt",
                effects={'gold': -3000, 'food': -100, 'loyalty': 10},
                description="Geçici çözüm."
            ),
        ]
    ),
    
    Event(
        id="plague",
        title="Veba Salgını",
        description="Korkunç hastalık eyalette yayılıyor. Her gün yüzlerce kişi ölüyor.",
        event_type=EventType.NATURAL,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Karantina uygula",
                effects={'trade_income': -30, 'population': -1000, 'health': 20},
                description="Salgın yavaşlar ama ticaret durur."
            ),
            EventChoice(
                text="Hekimler getirt",
                effects={'gold': -5000, 'population': -500, 'health': 10},
                description="Tedavi başlar."
            ),
            EventChoice(
                text="Dua ve sabır",
                effects={'population': -2000, 'piety': 10},
                description="En ucuz ama en ölümcül seçenek."
            ),
        ]
    ),
    
    Event(
        id="drought",
        title="Kuraklık",
        description="Aylar boyunca yağmur yağmadı. Kuyular kuruyor, hayvanlar ölüyor.",
        event_type=EventType.NATURAL,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Su kanalı projesi",
                effects={'gold': -12000, 'infrastructure': 20, 'food': 100},
                description="Kalıcı çözüm."
            ),
            EventChoice(
                text="Su ticareti yap",
                effects={'gold': -4000, 'loyalty': 5},
                description="Geçici rahatlama."
            ),
        ]
    ),
    
    Event(
        id="locust_invasion",
        title="Çekirge İstilası",
        description="Dev çekirge sürüleri tarlaları yok ediyor. Hasat tehlikede!",
        event_type=EventType.NATURAL,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Tüm halkı seferber et",
                effects={'food': -300, 'loyalty': 5, 'production': -10},
                description="Mücadele başlar."
            ),
            EventChoice(
                text="Etkilenen bölgeleri boşalt",
                effects={'food': -500, 'population': -200},
                description="Kayıpları kabullenmek."
            ),
        ]
    ),
]


# ============== SOSYAL OLAYLAR ==============

SOCIAL_EVENTS = [
    Event(
        id="janissary_revolt",
        title="Yeniçeri Ayaklanması",
        description="Yeniçeriler maaş artışı ve ikramiye istiyor. Kazanları devirdiler!",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Talepleri kabul et",
                effects={'gold': -15000, 'military_morale': 20, 'prestige': -10},
                description="Barış sağlanır ama prestij düşer."
            ),
            EventChoice(
                text="Sadık birlikleri gönder",
                effects={'military_strength': -2000, 'loyalty': -10, 'order': 30},
                description="İsyan bastırılır ama kayıplar büyük."
            ),
            EventChoice(
                text="Elebaşlarını tut, diğerlerini bağışla",
                effects={'gold': -5000, 'military_morale': -5, 'order': 15},
                description="Dengeli yaklaşım."
            ),
        ],
        condition_func=has_strong_army
    ),
    
    Event(
        id="kizilbas_uprising",
        title="Kızılbaş Hareketleri",
        description="Anadolu'da Kızılbaş tarikatları faaliyetlerini artırdı. "
                    "Safevi yanlısı propaganda yayılıyor.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Sert müdahale",
                effects={'kizilbas_threat': -20, 'loyalty': -15, 'piety': 5},
                description="Tehdit azalır ama halk mutsuz."
            ),
            EventChoice(
                text="Hoşgörü politikası",
                effects={'kizilbas_threat': 10, 'loyalty': 10, 'tolerance': 15},
                description="Barışçıl ama riskli."
            ),
            EventChoice(
                text="Ulema fetvaları yayınlat",
                effects={'kizilbas_threat': -10, 'piety': 10, 'legitimacy': 5},
                description="Dini otorite kullan."
            ),
        ]
    ),
    
    Event(
        id="ulema_protest",
        title="Ulema Protestosu",
        description="Din alimleri bazı uygulamalarınıza itiraz ediyor. Fetva tartışmaları başladı.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Ulemanın sözünü dinle",
                effects={'piety': 15, 'legitimacy': 10, 'innovation': -10},
                description="Dini otorite güçlenir."
            ),
            EventChoice(
                text="Reformları savun",
                effects={'piety': -10, 'innovation': 15, 'education': 10},
                description="Modernleşme yolu."
            ),
        ]
    ),
    
    Event(
        id="prince_conflict",
        title="Şehzade Kavgası",
        description="Şehzadeler arasında taht mücadelesi başladı. Saray entrikalarla dolu.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Büyük şehzadeyi destekle",
                effects={'legitimacy': 10, 'loyalty': -5, 'stability': -10},
                description="Gelenek korunur."
            ),
            EventChoice(
                text="En yetenekliyi seç",
                effects={'administration': 10, 'legitimacy': -5},
                description="Meritokrasi."
            ),
            EventChoice(
                text="Karışma, onlar halletsin",
                effects={'stability': -20, 'civil_war_risk': 10},
                description="Tehlikeli bekleme."
            ),
        ]
    ),
    
    Event(
        id="millet_unrest",
        title="Millet İsyanı",
        description="Gayrimüslim milletlerden biri isyan etti. Pax Ottomana tehlikede.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Askeri müdahale",
                effects={'loyalty': -20, 'order': 25, 'tolerance': -10},
                description="İsyan bastırılır."
            ),
            EventChoice(
                text="Özerklik tanı",
                effects={'loyalty': 15, 'central_authority': -10, 'tolerance': 10},
                description="Barış sağlanır."
            ),
            EventChoice(
                text="Patrikle görüş",
                effects={'gold': -3000, 'loyalty': 10, 'piety': -5},
                description="Diplomatik çözüm."
            ),
        ],
        condition_func=has_low_loyalty
    ),
]


# Tüm genişletilmiş olayları birleştir
EXPANDED_EVENTS = (
    HISTORICAL_EVENTS +
    ECONOMIC_EVENTS +
    NATURAL_EVENTS +
    SOCIAL_EVENTS
)


def get_expanded_events() -> list:
    """Genişletilmiş olay listesini döndür"""
    return EXPANDED_EVENTS.copy()


def get_events_by_type(event_type: EventType) -> list:
    """Türe göre olayları filtrele"""
    return [e for e in EXPANDED_EVENTS if e.event_type == event_type]


def get_historical_events() -> list:
    """Sadece tarihsel olayları döndür"""
    return HISTORICAL_EVENTS.copy()
