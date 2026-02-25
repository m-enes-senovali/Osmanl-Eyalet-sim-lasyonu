# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eğitim/Tutorial Sistemi
Tüm oyun sistemlerini ve mekanikleri kapsayan kapsamlı interaktif eğitim.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
from audio.audio_manager import get_audio_manager


class TutorialChapter(Enum):
    """Tutorial bölümleri"""
    BASICS = "basics"
    NAVIGATION = "navigation"
    ECONOMY = "economy"
    MILITARY = "military"
    CONSTRUCTION = "construction"
    DIPLOMACY = "diplomacy"
    PEOPLE = "people"
    ADVANCED = "advanced"


@dataclass
class TutorialStep:
    """Tutorial adımı"""
    id: str
    chapter: TutorialChapter
    title: str
    description: str
    instruction: str
    target_screen: str = None
    target_action: str = None
    required_key: str = None
    completed: bool = False
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'chapter': self.chapter.value,
            'completed': self.completed
        }


TUTORIAL_STEPS: List[TutorialStep] = []


def _init_tutorial_steps():
    """Tüm tutorial adımlarını tanımla — oyundaki güncel tuşlar ve mekanikler"""
    global TUTORIAL_STEPS
    
    TUTORIAL_STEPS = [
        # ═══════════════════════════════════════════════════════
        # BÖLÜM 1: HOŞ GELDİNİZ ve TEMEL KONTROLLER
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="basics_welcome",
            chapter=TutorialChapter.BASICS,
            title="Hoş Geldiniz!",
            description="Osmanlı Eyalet Yönetim Simülasyonuna hoş geldiniz! "
                        "1520 yılında, Kanuni Sultan Süleyman döneminde bir Osmanlı eyaletini yöneteceksiniz. "
                        "Ekonomi, ordu, diplomasi, halk ve inşaat gibi tüm alanları yönetmek sizin elinizde. "
                        "Bu eğitimde oyunun tüm sistemlerini adım adım uygulayarak öğreneceksiniz.",
            instruction="Başlamak için Enter tuşuna basın.",
            required_key="return"
        ),
        TutorialStep(
            id="basics_nav_down",
            chapter=TutorialChapter.BASICS,
            title="Menüde Aşağı Gitme",
            description="Oyundaki tüm menüler klavyeyle kontrol edilir. "
                        "Aşağı ok tuşuyla bir sonraki menü öğesine geçersiniz. "
                        "Ekran okuyucu her öğeyi sesli olarak duyuracaktır.",
            instruction="Aşağı ok tuşuna basın.",
            required_key="down"
        ),
        TutorialStep(
            id="basics_nav_up",
            chapter=TutorialChapter.BASICS,
            title="Menüde Yukarı Gitme",
            description="Yukarı ok tuşuyla bir önceki menü öğesine dönersiniz. "
                        "Menülerde istediğiniz kadar yukarı-aşağı gezinebilirsiniz.",
            instruction="Yukarı ok tuşuna basın.",
            required_key="up"
        ),
        TutorialStep(
            id="basics_select",
            chapter=TutorialChapter.BASICS,
            title="Seçim Yapma — Enter",
            description="Bir menü öğesini seçmek, bir eylemi onaylamak veya bir alt menüye girmek için "
                        "Enter tuşuna basarsınız. Enter oyundaki en temel etkileşim tuşudur.",
            instruction="Enter tuşuna basın.",
            required_key="return"
        ),
        TutorialStep(
            id="basics_back",
            chapter=TutorialChapter.BASICS,
            title="Geri Gitme — Backspace",
            description="Bir önceki ekrana veya üst menüye dönmek için Backspace tuşunu kullanırsınız. "
                        "Bu tuş sizi her zaman bir adım geriye götürür. "
                        "Herhangi bir alt ekrandan ana eyalet ekranına dönmek için kullanılır.",
            instruction="Backspace tuşuna basın.",
            required_key="backspace"
        ),
        TutorialStep(
            id="basics_escape",
            chapter=TutorialChapter.BASICS,
            title="Ana Menü — Escape",
            description="Escape tuşu sizi ana menüye döndürür veya açık diyalogları kapatır. "
                        "Oyun sırasında Escape'e basarsanız ana menüye gidersiniz. "
                        "Bu eğitimde Escape'e basarsanız eğitim sonlanır ve ana menüye dönersiniz. "
                        "Şimdi ise eğitime devam edelim.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 2: EYALET EKRANI ve GEZINME
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="nav_province_intro",
            chapter=TutorialChapter.NAVIGATION,
            title="Eyalet Ekranı",
            description="Oyunun ana ekranı Eyalet Görünümüdür. Buradan tüm yönetim ekranlarına erişirsiniz. "
                        "Sol tarafta kaynak paneliniz, ortada yan menünüz ve sağ tarafta butonlarınız bulunur. "
                        "Yan menüde Ekonomi, Ordu, İnşaat, Diplomasi ve diğer tüm ekranlar listelenir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_turn_system",
            chapter=TutorialChapter.NAVIGATION,
            title="Tur Sistemi",
            description="Oyun tur tabanlıdır. Her tur bir günü temsil eder. "
                        "Tur geçirdiğinizde vergiler toplanır, kaynaklar üretilir, binalar inşa edilir, "
                        "askerler eğitilir ve olaylar meydana gelir. "
                        "Her tur sonunda kaynak değişimleri sesli olarak duyurulur. "
                        "Space tuşuyla tur geçirirsiniz.",
            instruction="Space tuşuna basın.",
            required_key="space"
        ),
        TutorialStep(
            id="nav_f1_status",
            chapter=TutorialChapter.NAVIGATION,
            title="Tam Durum Özeti — F1",
            description="F1 tuşu size bulunduğunuz ekranın tam özetini okur. "
                        "Eyalet ekranında hazinenizi, nüfusunuzu, ordunuzun gücünü "
                        "ve diğer kritik bilgileri duyurur. "
                        "Her ekranda F1'e basarak o anki durumu öğrenebilirsiniz.",
            instruction="F1 tuşuna basın.",
            required_key="f1"
        ),
        TutorialStep(
            id="nav_h_help",
            chapter=TutorialChapter.NAVIGATION,
            title="Yardım — H",
            description="H tuşu Kethüda'nızdan (yardımcınızdan) hızlı yardım alır. "
                        "Mevcut durumunuza göre size tavsiyelerde bulunur. "
                        "Ne yapacağınızı bilemediğinizde H tuşuna basın.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_r_resources",
            chapter=TutorialChapter.NAVIGATION,
            title="Kaynakları Öğrenme — R",
            description="R tuşu tüm kaynaklarınızı okur: Altın, Zahire, Kereste, Demir ve Taş. "
                        "Kaynaklar her şeyin temelidir — bina inşa etmek, asker toplamak, "
                        "ticaret yapmak ve halkı beslemek için kaynaklara ihtiyacınız vardır.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_w_warnings",
            chapter=TutorialChapter.NAVIGATION,
            title="Uyarıları Dinleme — W",
            description="W tuşu mevcut uyarılarınızı okur: isyan riski, düşük kaynaklar, "
                        "düşman tehditleri gibi kritik durumları bildirir. "
                        "W tuşuna düzenli basarak beklenmedik krizlerden kaçınabilirsiniz.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_i_income",
            chapter=TutorialChapter.NAVIGATION,
            title="Gelir ve Gider — I",
            description="I tuşu gelir-gider özetinizi okur. "
                        "Ne kadar kazandığınızı ve ne kadar harcadığınızı görürsünüz. "
                        "Dengeli bir bütçe eyaletinizin sağlığının anahtarıdır.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_y_year",
            chapter=TutorialChapter.NAVIGATION,
            title="Tarih Bilgisi — Y",
            description="Y tuşu şu anki yılı, ayı ve kaçıncı turda olduğunuzu duyurur. "
                        "Oyun 1520 yılında başlar ve her tur bir gün ilerler.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_tab_stats",
            chapter=TutorialChapter.NAVIGATION,
            title="İstatistik Paneli — Tab",
            description="Tab tuşu erişilebilir istatistik panelini açar. "
                        "Bu panelde tüm detaylı istatistikler madde madde listelenir "
                        "ve yukarı-aşağı oklarla gezinebilirsiniz. "
                        "Tab veya Escape ile paneli kapatırsınız.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_save",
            chapter=TutorialChapter.NAVIGATION,
            title="Oyunu Kaydetme — F5",
            description="F5 tuşu oyununuzu kaydetmenizi sağlar. "
                        "Kayıt yuvalarından birini seçerek ilerlemenizi saklarsınız. "
                        "Ana menüden Devam Et seçeneğiyle kayıtlı oyununuza geri dönebilirsiniz. "
                        "Düzenli kayıt alışkanlığı çok önemlidir!",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_music",
            chapter=TutorialChapter.NAVIGATION,
            title="Müzik Sesi Ayarı",
            description="Page Up tuşuyla müzik sesini artırabilir, "
                        "Page Down tuşuyla azaltabilirsiniz. "
                        "Yüzde sıfırdan yüzde yüze kadar ayarlanabilir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="nav_summary",
            chapter=TutorialChapter.NAVIGATION,
            title="Gezinme Tamamlandı",
            description="Eyalet ekranı tuş kısayollarını öğrendiniz! Özetleyelim: "
                        "Space: tur geç, F1: tam durum, H: yardım, R: kaynaklar, "
                        "W: uyarılar, I: gelir-gider, Y: tarih, Tab: istatistik paneli, "
                        "F5: kayıt, Escape: ana menü, PageUp-Down: müzik sesi.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 3: EKONOMİ YÖNETİMİ
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="econ_intro",
            chapter=TutorialChapter.ECONOMY,
            title="Ekonomi Yönetimi",
            description="Ekonomi eyaletinizin bel kemiğidir. Altın olmadan hiçbir şey yapamazsınız: "
                        "asker toplayamaz, bina yapamaz, ticaret edemezsiniz. "
                        "Yan menüden E tuşuyla Ekonomi ekranına erişirsiniz.",
            instruction="E tuşuna basın.",
            required_key="e"
        ),
        TutorialStep(
            id="econ_treasury",
            chapter=TutorialChapter.ECONOMY,
            title="Hazine ve Kaynaklar",
            description="Ekonomi ekranında hazinenizi ve tüm kaynaklarınızı görürsünüz. "
                        "Beş temel kaynak vardır: Altın (para birimi), Zahire (yiyecek), "
                        "Kereste (ahşap yapı malzemesi), Demir (silah ve alet) ve Taş (inşaat). "
                        "Her kaynak farklı amaçlara hizmet eder.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_income_expense",
            chapter=TutorialChapter.ECONOMY,
            title="Gelir ve Gider Dengesi",
            description="Gelir kaynakları: vergiler, ticaret geliri, üretim satışı, ganimet. "
                        "Gider kaynakları: asker maaşları, bina bakım masrafları, diplomatik hediyeler. "
                        "Her tur sonunda net gelir hazinenize eklenir veya çıkarılır. "
                        "Eğer hazineniz sıfırın altına düşerse asker morali çöker ve isyan riski artar.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_tax",
            chapter=TutorialChapter.ECONOMY,
            title="Vergi Yönetimi",
            description="Vergi oranını değiştirerek gelirinizi artırabilirsiniz. "
                        "Ancak yüksek vergi halkı mutsuz eder ve isyan riskini artırır. "
                        "Düşük vergi halkı memnun eder ama hazineniz zayıflar. "
                        "Vergi oranını yüzde 20 ile yüzde 30 arasında tutmak genellikle güvenlidir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_inflation",
            chapter=TutorialChapter.ECONOMY,
            title="Enflasyon",
            description="Hazinede çok fazla altın biriktiğinde veya aşırı harcama yapıldığında enflasyon artar. "
                        "Yüksek enflasyon tüm maliyetleri artırır: asker maaşları, bina fiyatları ve ticaret bedelleri pahalanır. "
                        "Ayrıca vergi geliriniz de enflasyondan olumsuz etkilenir. "
                        "Dengeyi korumak çok önemlidir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_workers",
            chapter=TutorialChapter.ECONOMY,
            title="İşçi Yönetimi — O tuşu",
            description="İşçiler kaynak üretiminin temelini oluşturur. "
                        "Tarım, madencilik, ormancılık ve taş ocağı gibi alanlara işçi atarsınız. "
                        "Her alana daha fazla işçi atadığınızda o kaynağın üretimi artar. "
                        "O tuşuyla İşçiler ekranına erişirsiniz.",
            instruction="O tuşuna basın.",
            required_key="o"
        ),
        TutorialStep(
            id="econ_worker_types",
            chapter=TutorialChapter.ECONOMY,
            title="İşçi Türleri ve Üretim",
            description="Tarım işçileri zahire üretir — halkı beslemek için şarttır. "
                        "Madenciler demir çıkarır — silah ve top üretimi için gereklidir. "
                        "Oduncular kereste toplar — bina inşaatı için lazımdır. "
                        "Taşçılar taş çıkarır — kale ve surların yapımında kullanılır. "
                        "İşçi sayısı nüfusunuza bağlıdır, sınırsız değildir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_trade",
            chapter=TutorialChapter.ECONOMY,
            title="Ticaret — X tuşu",
            description="X tuşuyla Ticaret ekranını açarsınız. "
                        "Ticaret yolları kurarak diğer devletlerle alışveriş yapabilirsiniz. "
                        "Fazla ürettiğiniz kaynakları satarak altın kazanır, "
                        "ihtiyacınız olan kaynakları satın alırsınız. "
                        "Ticaret ilişkileri diplomasiyi de olumlu etkiler.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_guilds",
            chapter=TutorialChapter.ECONOMY,
            title="Loncalar — L tuşu",
            description="Yan menüden L tuşuyla Lonca ekranına gidersiniz. "
                        "Loncalar zanaatkarların örgütleridir: silah üretimi, tekstil, gıda, "
                        "deri işçiliği gibi alanlarda faaliyet gösterirler. "
                        "Loncaları güçlendirerek üretim kalitenizi ve miktarınızı artırabilirsiniz. "
                        "Güçlü loncalar eyaletinizin ekonomik temelini sağlamlaştırır.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="econ_summary",
            chapter=TutorialChapter.ECONOMY,
            title="Ekonomi Bölümü Tamamlandı",
            description="Ekonomi yönetimini öğrendiniz! Özetle: "
                        "E: Ekonomi ekranı, O: İşçiler, X: Ticaret, L: Loncalar. "
                        "R: Kaynakları dinle, I: Gelir-gider dinle. "
                        "Vergiyi dengeleyin, enflasyona dikkat edin, işçileri doğru alanlara atayın.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 4: ASKERİ YÖNETİM
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="mil_intro",
            chapter=TutorialChapter.MILITARY,
            title="Askeri Yönetim — M tuşu",
            description="Güçlü bir ordu eyaletinizi düşmanlardan korur. "
                        "Yan menüden M tuşuyla Ordu ekranına erişirsiniz. "
                        "Burada asker toplayabilir, birlikleri yönetebilir ve komutanlarınızı görebilirsiniz.",
            instruction="M tuşuna basın.",
            required_key="m"
        ),
        TutorialStep(
            id="mil_unit_types",
            chapter=TutorialChapter.MILITARY,
            title="Birlik Türleri",
            description="Oyunda çeşitli birlik türleri vardır: "
                        "Yeniçeriler en güçlü piyade birliğidir ama bakım maliyetleri yüksektir. "
                        "Sipahiler atlı süvari birliğidir, hızlıdır ve akınlarda etkilidir. "
                        "Azaplar ucuz ve çabuk toplanan hafif piyadelerdir. "
                        "Topçular kuşatmada ve savunmada kilit önem taşır. "
                        "Akıncılar düşman topraklarına baskın için idealdir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="mil_recruitment",
            chapter=TutorialChapter.MILITARY,
            title="Asker Toplama",
            description="Asker toplamak altın ve zaman gerektirir. "
                        "Her birlik türünün toplama maliyeti, günlük bakım ücreti ve savaş gücü farklıdır. "
                        "Çok fazla asker tutmak hazinenizi eritir. "
                        "Çok az asker ise eyaletinizi savunmasız bırakır. "
                        "Ordu büyüklüğünü ihtiyacınıza göre ayarlayın.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="mil_morale",
            chapter=TutorialChapter.MILITARY,
            title="Ordu Morali ve Komutanlar",
            description="Ordunuzun morali savaşın sonucunu doğrudan etkiler. "
                        "Düşük moral: askerler savaştan kaçar, bozguna uğrarsınız. "
                        "Yüksek moral: kahramanca savaşır, zafer kazanırsınız. "
                        "Askerleri düzenli ödeyerek, galibiyetler kazanarak ve iyi komutanlarla morali yüksek tutun. "
                        "Komutanları isimlendirebilir ve yönetebilirsiniz.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="mil_warfare",
            chapter=TutorialChapter.MILITARY,
            title="Savaş ve Akınlar — K tuşu",
            description="K tuşuyla Akın ve Savaş ekranına gidersiniz. "
                        "Akınlar: düşman topraklarına baskın düzenleyip ganimet kazanırsınız. "
                        "Akınlar hızlı ve kârlıdır ama diplomatik ilişkileriniz kötüleşir. "
                        "Tam Savaş: düşman eyaletlerini fethetmek için tam çaplı savaş başlatırsınız. "
                        "Savunma Savaşı: düşman saldırırsa otomatik olarak savunma savaşı başlar.",
            instruction="K tuşuna basın.",
            required_key="k"
        ),
        TutorialStep(
            id="mil_artillery",
            chapter=TutorialChapter.MILITARY,
            title="Topçu Birliği",
            description="Topçu birlikleri kuşatmalarda ve kale savunmasında kritik önem taşır. "
                        "Top dökmek için demir ve bakıra ihtiyacınız vardır. "
                        "Topçu ekranına yan menüden T tuşuyla erişebilirsiniz. "
                        "Güçlü bir topçu birliği düşmanın surlarını yıkabilir "
                        "veya kendi kalelerinizi savunabilir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="mil_naval",
            chapter=TutorialChapter.MILITARY,
            title="Donanma",
            description="Kıyı eyaletlerinde tersane inşa ederek donanma kurabilirsiniz. "
                        "Gemiler deniz ticaretini korur, kıyı savunmasını güçlendirir "
                        "ve deniz akınları düzenlemenize olanak tanır. "
                        "Donanma ekranına yan menüden N tuşuyla erişilir. "
                        "Gemi inşası kereste, halat, zift ve yelken bezi gerektirir. "
                        "Bu özellik sadece kıyı eyaletlerinde aktiftir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="mil_summary",
            chapter=TutorialChapter.MILITARY,
            title="Askeri Bölüm Tamamlandı",
            description="Askeri yönetimi öğrendiniz! Özetle: "
                        "M: Ordu ekranı, K: Savaş ve Akın, T (menüden): Topçu, N: Donanma. "
                        "Ordu moraline ve bakım masraflarına dikkat edin. "
                        "Dengeyi koruyun — ne çok az ne çok fazla asker tutun.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 5: İNŞAAT ve ALTYAPI
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="const_intro",
            chapter=TutorialChapter.CONSTRUCTION,
            title="İnşaat ve Binalar — C tuşu",
            description="Binalar eyaletinize kalıcı bonuslar sağlar. "
                        "Yan menüden C tuşuyla İnşaat ekranına erişirsiniz. "
                        "Her bina türü farklı kaynak ve altın gerektirir ve farklı faydalar sunar.",
            instruction="C tuşuna basın.",
            required_key="c"
        ),
        TutorialStep(
            id="const_building_types",
            chapter=TutorialChapter.CONSTRUCTION,
            title="Bina Türleri ve Faydaları",
            description="Cami: halkın mutluluğunu artırır, nüfus artış hızını yükseltir. "
                        "Hastane: salgın hastalıkları önler, nüfus kaybını azaltır. "
                        "Pazar: ticaret gelirini artırır. "
                        "Kışla: asker eğitim hızını yükseltir. "
                        "Kale: savunma gücünü artırır, düşman akınlarına karşı koruma sağlar. "
                        "Tersane: donanma inşa etmenize izin verir (sadece kıyı eyaletleri). "
                        "İnşaat süresi bina türüne göre değişir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="const_levels",
            chapter=TutorialChapter.CONSTRUCTION,
            title="Bina Seviyeleri",
            description="Binalar seviye seviye yükseltilebilir. "
                        "Her seviye yükselmesi daha fazla kaynak gerektirir ama bonusu da artar. "
                        "Örneğin seviye 2 Cami, seviye 1'den daha fazla mutluluk sağlar. "
                        "İnşaat sırası önemlidir — önce hangi binaları yapacağınız strateji gerektirir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="const_resources",
            chapter=TutorialChapter.CONSTRUCTION,
            title="İnşaat Kaynakları",
            description="İnşaat için genellikle kereste, taş, demir ve altın gerekir. "
                        "İşçilerinizi doğru alanlara atayarak bu kaynakları üretirsiniz. "
                        "Ayrıca ticaretten de kaynak satın alabilirsiniz. "
                        "İnşaat başladığında tamamlanana kadar her tur otomatik olarak ilerler.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="const_summary",
            chapter=TutorialChapter.CONSTRUCTION,
            title="İnşaat Bölümü Tamamlandı",
            description="İnşaat ve altyapıyı öğrendiniz! C tuşuyla İnşaat ekranını açın. "
                        "Stratejik olarak hangi binaları önce yapacağınıza karar verin. "
                        "Cami mutluluk, hastane sağlık, kışla askeri güç, kale savunma sağlar.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 6: DİPLOMASİ ve DIŞ İLİŞKİLER
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="diplo_intro",
            chapter=TutorialChapter.DIPLOMACY,
            title="Diplomasi — D tuşu",
            description="Diplomasi ekranında komşu devletlerle ilişkilerinizi yönetirsiniz. "
                        "Yan menüden D tuşuyla Diplomasi ekranına erişirsiniz. "
                        "İttifak, ticaret anlaşması, barış ya da savaş ilan edebilirsiniz.",
            instruction="D tuşuna basın.",
            required_key="d"
        ),
        TutorialStep(
            id="diplo_relations",
            chapter=TutorialChapter.DIPLOMACY,
            title="Devlet İlişkileri",
            description="Her devletle olan ilişkiniz bir puan ile ölçülür. "
                        "Yüksek ilişki ticaret ve ittifak fırsatları sunar. "
                        "Düşük ilişki savaş ve saldırı riskini artırır. "
                        "Hediye göndermek, ticaret yapmak ve müzakere ilişkiyi iyileştirir. "
                        "Savaş, casusluk ve akın ilişkiyi kötüleştirir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="diplo_sultan",
            chapter=TutorialChapter.DIPLOMACY,
            title="Padişah Sadakati",
            description="Padişah'ın size olan güveni kritik önem taşır. "
                        "Padişah sadakati düşerse görevden alınabilir, hatta idam edilebilirsiniz! "
                        "Sadakati artırmak için vergileri düzenli toplayın, isyanları bastırın "
                        "ve padişahın buyruklarına uyun. Yüzde 30'un altına düşmesi çok tehlikelidir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="diplo_negotiation",
            chapter=TutorialChapter.DIPLOMACY,
            title="Müzakere Sistemi",
            description="Diplomasi ekranında bir devlet seçtiğinizde müzakere ekranına girersiniz. "
                        "Burada hediye gönderme, ticaret teklifi, ittifak önerme, "
                        "vasal ilişkisi kurma veya savaş ilan etme seçenekleri bulunur. "
                        "Müzakere sonucu karşı tarafın gücüne ve ilişki durumuna bağlıdır.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="diplo_espionage",
            chapter=TutorialChapter.DIPLOMACY,
            title="Casusluk — S tuşu",
            description="Yan menüden S tuşuyla Casusluk ekranına gidersiniz. "
                        "Casuslar düşman devletlerin ordusunu, hazinesini ve planlarını keşfeder. "
                        "Sabotaj yapabilir, propaganda yayabilir veya isyan kışkırtabilirsiniz. "
                        "Ancak casusunuz yakalanabilir — bu diplomatik kriz yaratır!",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="diplo_summary",
            chapter=TutorialChapter.DIPLOMACY,
            title="Diplomasi Bölümü Tamamlandı",
            description="Diplomasiyi öğrendiniz! D: Diplomasi, S (menüden): Casusluk. "
                        "İlişkilerinizi dengeli tutun, padişah sadakatine dikkat edin. "
                        "Hem müttefikleriniz hem casuslarınız olsun.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 7: HALK, DİN VE TOPLUM
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="ppl_intro",
            chapter=TutorialChapter.PEOPLE,
            title="Halk Yönetimi — P tuşu",
            description="Halkınız eyaletinizin temelidir. Mutlu halk vergi öder, "
                        "asker olur ve üretim yapar. Mutsuz halk isyan eder! "
                        "Yan menüden P tuşuyla Halk ekranına erişirsiniz.",
            instruction="P tuşuna basın.",
            required_key="p"
        ),
        TutorialStep(
            id="ppl_happiness",
            chapter=TutorialChapter.PEOPLE,
            title="Mutluluk ve Huzursuzluk",
            description="Halkın mutluluğu şu faktörlere bağlıdır: "
                        "Vergi oranı — düşük vergi mutlu eder, yüksek vergi mutsuz eder. "
                        "Gıda durumu — yeterli zahire yoksa halk aç kalır. "
                        "Güvenlik — askeri güç düşükse halk tedirgin olur. "
                        "Adalet — Kadı'nın etkinliği ve suç oranı. "
                        "Dini ihtiyaçlar — cami ve ibadethaneler mutluluğu artırır.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_revolt",
            chapter=TutorialChapter.PEOPLE,
            title="İsyan Tehlikesi",
            description="Huzursuzluk belli bir seviyeyi aşarsa isyan patlar! "
                        "İsyan sırasında üretim durur, ticaret kesilir ve askerleriniz "
                        "isyancılarla savaşmak zorunda kalır. "
                        "İsyanı bastırmak ordunuzun bir kısmını meşgul eder. "
                        "İsyanı önlemek her zaman bastırmaktan daha iyidir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_food",
            chapter=TutorialChapter.PEOPLE,
            title="Gıda ve Nüfus",
            description="Halkınızın yeterli gıdaya ihtiyacı vardır. "
                        "Gıda üretimi tarım işçilerine ve iklim koşullarına bağlıdır. "
                        "Gıda yetersizse nüfus azalır, halk mutsuzlaşır ve isyan riski artar. "
                        "Tahrir sistemiyle nüfusunuzu ve tahıl üretimini takip edebilirsiniz.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_population_growth",
            chapter=TutorialChapter.PEOPLE,
            title="Nüfus Artışı",
            description="Nüfus doğal olarak artar — yeterli gıda, sağlık ve mutluluk koşullarında. "
                        "Cami nüfus artış hızını yükseltir. "
                        "Hastane salgın hastalıkları önleyerek nüfus kaybını azaltır. "
                        "Daha fazla nüfus demek daha fazla işçi, daha fazla vergi ve daha büyük ordu demektir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_religion",
            chapter=TutorialChapter.PEOPLE,
            title="Din ve Milletler",
            description="Eyaletinizde farklı dini gruplar (milletler) yaşar. "
                        "Her milletin sadakati farklıdır ve yönetim tarzınıza bağlıdır. "
                        "Hoşgörülü yönetim tüm milletlerin sadakatini artırır. "
                        "Baskıcı yönetim kısa vadede vergiyi artırsa da uzun vadede isyan riskini yükseltir. "
                        "Din ekranına yan menüden erişebilirsiniz.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_divan",
            chapter=TutorialChapter.PEOPLE,
            title="Eyalet Divanı — V tuşu",
            description="Yan menüden V tuşuyla Divan ekranına gidersiniz. "
                        "Divan'da dört danışmanınız vardır: "
                        "Defterdar ekonomiyi analiz eder, "
                        "Kadı adaleti ve huzursuzluğu değerlendirir, "
                        "Subaşı askeri durumu ve düşman tehditlerini inceler, "
                        "Tahrir Emini nüfus ve gıda durumunu raporlar.",
            instruction="V tuşuna basın.",
            required_key="v"
        ),
        TutorialStep(
            id="ppl_divan_detail",
            chapter=TutorialChapter.PEOPLE,
            title="Danışman Becerileri",
            description="Her danışmanın bir beceri ve sadakat puanı vardır. "
                        "Yüksek becerili danışmanlar daha doğru raporlar sunar. "
                        "Düşük becerili danışmanlar önemli bilgileri kaçırabilir. "
                        "Düşük sadakatli danışmanlar raporları manipüle edebilir — "
                        "acil durumları gizleyebilir veya önemini düşürebilir! "
                        "Danışmanlarınızın güvenilirliğine dikkat edin.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_events",
            chapter=TutorialChapter.PEOPLE,
            title="Olaylar ve Kararlar",
            description="Oyun sırasında çeşitli olaylar meydana gelir: deprem, salgın, kuraklık, "
                        "kervan baskını, bayram kutlaması, padişah buyruğu gibi. "
                        "Olaylar meydana geldiğinde ekrana bildirim gelir "
                        "ve bazı olaylar sizden karar vermenizi ister. "
                        "Her kararın farklı sonuçları olabilir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="ppl_summary",
            chapter=TutorialChapter.PEOPLE,
            title="Halk Bölümü Tamamlandı",
            description="Halk yönetimini öğrendiniz! P: Halk, V: Divan. "
                        "Halkın mutluluğunu yüksek tutun, gıda üretimine dikkat edin, "
                        "dini hoşgörüyü koruyun, danışmanlarınızı takip edin "
                        "ve olaylara akıllıca yanıt verin.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),

        # ═══════════════════════════════════════════════════════
        # BÖLÜM 8: İLERİ KONULAR ve SON
        # ═══════════════════════════════════════════════════════
        TutorialStep(
            id="adv_achievements",
            chapter=TutorialChapter.ADVANCED,
            title="Başarılar — B tuşu",
            description="Yan menüden B tuşuyla Başarılar ekranına gidersiniz. "
                        "Oyunda belirli hedeflere ulaşarak başarılar kazanırsınız: "
                        "ilk binanızı inşa etmek, 1000 altına ulaşmak, ilk savaşı kazanmak, "
                        "padişah sadakatini yüzde 100'e çıkarmak gibi. "
                        "Başarılar oyun deneyiminizi zenginleştirir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_history",
            chapter=TutorialChapter.ADVANCED,
            title="Geçmiş Olaylar — G tuşu",
            description="Yan menüden G tuşuyla Geçmiş ekranına gidersiniz. "
                        "Burada eyaletinizde yaşanan tüm önemli olayları kronolojik olarak görebilirsiniz: "
                        "savaşlar, ticaret anlaşmaları, felaketler, başarılar ve daha fazlası. "
                        "Not: Eyalet ekranında G tuşuna basarsanız sadece altın miktarınızı duyurur.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_guides",
            chapter=TutorialChapter.ADVANCED,
            title="Rehber Tuşları",
            description="Eyalet ekranında detaylı rehberlere erişebilirsiniz: "
                        "F2: Ekonomi rehberi — vergiler, ticaret ve kaynak yönetimi hakkında bilgi. "
                        "F3: Askeri rehber — birlik türleri, savaş taktikleri hakkında bilgi. "
                        "F4: İnşaat rehberi — bina türleri ve maliyetleri hakkında bilgi. "
                        "Bu rehberler herhangi bir zamanda erişilebilirdir.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_shortcuts_menu",
            chapter=TutorialChapter.ADVANCED,
            title="Yan Menü Kısayolları",
            description="Eyalet ekranında yan menü tuşları şunlardır: "
                        "E: Ekonomi, M: Ordu, C: İnşaat, D: Diplomasi, P: Halk, "
                        "L: Loncalar, S: Casusluk, B: Başarılar, G: Geçmiş, "
                        "T: Topçu, K: Akın ve Savaş, V: Divan, N: Donanma. "
                        "Bu tuşlar yan menüdeki öğelere doğrudan erişim sağlar.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_shortcuts_keys",
            chapter=TutorialChapter.ADVANCED,
            title="Özel Kısayol Tuşları",
            description="Ek kısayollar: "
                        "R: Tüm kaynakları oku, I: Gelir-gider özeti, "
                        "W: Uyarıları oku, O: İşçi ekranı, X: Ticaret ekranı, "
                        "Y: Yıl ve tur bilgisi, H: Yardım al, "
                        "Space: Tur geç, F1: Durum özeti, F5: Kayıt. "
                        "Tab: İstatistik paneli, PageUp-Down: Müzik sesi.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_strategy_economy",
            chapter=TutorialChapter.ADVANCED,
            title="Strateji İpuçları: Ekonomi",
            description="İlk turlarınızda: vergiyi orta seviyede tutun. "
                        "Tarım işçilerine öncelik verin, halkınızı aç bırakmayın. "
                        "İlk binaların camı olsun, mutluluk çok önemli. "
                        "Ticaret yolları kurun, fazla kaynakları satın. "
                        "Enflasyonu yüzde 20'nin altında tutmaya çalışın.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_strategy_military",
            chapter=TutorialChapter.ADVANCED,
            title="Strateji İpuçları: Askeri",
            description="Küçük ama güçlü bir ordu büyük ama zayıf bir ordudan iyidir. "
                        "Başlangıçta Yeniçeri ve birkaç Azap yeterlidir. "
                        "Savaş başlatmadan önce ordunuzun beslenmesine ve moraline bakın. "
                        "Akını düşman zayıfken yapın. "
                        "Topçu birliği kuşatmada büyük avantaj sağlar.",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_strategy_diplomacy",
            chapter=TutorialChapter.ADVANCED,
            title="Strateji İpuçları: Diplomasi",
            description="Birden fazla cephede savaşmaktan kaçının. "
                        "En az bir güçlü müttefikiniz olsun. "
                        "Padişah sadakatini her zaman yüzde 50'nin üzerinde tutun. "
                        "Casuslarınızı düşmanlarınıza gönderin, bilgi güçtür. "
                        "İlişkileri kötüleştirmeden önce düşünün — savaş pahalıdır!",
            instruction="Devam etmek için Enter'a basın.",
            required_key="return"
        ),
        TutorialStep(
            id="adv_complete",
            chapter=TutorialChapter.ADVANCED,
            title="Eğitim Tamamlandı!",
            description="Tebrikler! Osmanlı Eyalet Yönetim Simülasyonunun tüm sistemlerini öğrendiniz. "
                        "Artık kendi eyaletinizi kurup yönetmeye hazırsınız! "
                        "Unutmayın: her kararınızın bir sonucu vardır. "
                        "Adil ve dengeli yönetin. Halkınızı mutlu, ordunuzu güçlü, "
                        "hazinenizi dolu ve düşmanlarınızı uzak tutun. İyi oyunlar!",
            instruction="Eğitimi tamamlamak için Enter'a basın.",
            required_key="return"
        ),
    ]


# Tutorial adımlarını yükle
_init_tutorial_steps()


class TutorialSystem:
    """Tutorial yönetim sistemi"""
    
    SAVE_FILE = "tutorial_progress.json"
    
    def __init__(self):
        self.audio = get_audio_manager()
        self.steps = TUTORIAL_STEPS.copy()
        self.current_step_index = 0
        self.is_active = False
        self.completed = False
        self.skipped = False
        
        self._load_progress()
    
    def _get_save_path(self) -> str:
        """Kayıt dosyası yolunu al"""
        save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'save')
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, self.SAVE_FILE)
    
    def _load_progress(self):
        """İlerlemeyi yükle"""
        save_path = self._get_save_path()
        if os.path.exists(save_path):
            try:
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.completed = data.get('completed', False)
                self.skipped = data.get('skipped', False)
                self.current_step_index = data.get('current_step', 0)
                
                completed_ids = data.get('completed_steps', [])
                for step in self.steps:
                    if step.id in completed_ids:
                        step.completed = True
                        
            except Exception as e:
                print(f"Tutorial yükleme hatası: {e}")
    
    def save_progress(self):
        """İlerlemeyi kaydet"""
        save_path = self._get_save_path()
        
        data = {
            'completed': self.completed,
            'skipped': self.skipped,
            'current_step': self.current_step_index,
            'completed_steps': [s.id for s in self.steps if s.completed]
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Tutorial kayıt hatası: {e}")
    
    def should_show_tutorial(self) -> bool:
        """Tutorial gösterilmeli mi?"""
        return not self.completed and not self.skipped
    
    def start(self):
        """Tutorial'ı başlat"""
        self.is_active = True
        self.current_step_index = 0
    
    def skip(self):
        """Tutorial'ı atla"""
        self.is_active = False
        self.skipped = True
        self.save_progress()
        self.audio.speak("Eğitim atlandı. Ana menüden tekrar başlatabilirsiniz.", interrupt=True)
    
    def get_current_step(self) -> Optional[TutorialStep]:
        """Mevcut adımı al"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_current_chapter(self) -> Optional[TutorialChapter]:
        """Mevcut bölümü al"""
        step = self.get_current_step()
        return step.chapter if step else None
    
    def advance(self, silent: bool = False):
        """Bir sonraki adıma geç."""
        current = self.get_current_step()
        if current:
            current.completed = True
        
        self.current_step_index += 1
        
        if self.current_step_index >= len(self.steps):
            self._complete_tutorial()
        else:
            self.save_progress()
    
    def _complete_tutorial(self):
        """Tutorial'ı tamamla"""
        self.is_active = False
        self.completed = True
        self.save_progress()
    
    def check_action(self, action: str, screen: str = None) -> bool:
        """Eylem kontrolü yap."""
        if not self.is_active:
            return False
        
        step = self.get_current_step()
        if not step:
            return False
        
        if step.target_screen and screen:
            if screen.upper() == step.target_screen:
                self.advance()
                return True
        
        if step.target_action:
            if action == step.target_action or action == "enter":
                self.advance()
                return True
        
        return False
    
    def get_progress(self) -> Dict:
        """İlerleme bilgisini al"""
        completed_count = sum(1 for s in self.steps if s.completed)
        total = len(self.steps)
        
        return {
            'current_step': self.current_step_index + 1,
            'total_steps': total,
            'completed': completed_count,
            'percentage': (completed_count / total) * 100 if total > 0 else 0,
            'current_chapter': self.get_current_chapter()
        }
    
    def get_steps_by_chapter(self, chapter: TutorialChapter) -> List[TutorialStep]:
        """Bölüme göre adımları al"""
        return [s for s in self.steps if s.chapter == chapter]
    
    def reset(self):
        """Tutorial'ı sıfırla"""
        self.current_step_index = 0
        self.completed = False
        self.skipped = False
        self.is_active = False
        
        _init_tutorial_steps()
        self.steps = TUTORIAL_STEPS.copy()
        
        self.save_progress()


# Global instance
_tutorial_system: Optional[TutorialSystem] = None


def get_tutorial_system() -> TutorialSystem:
    """Global TutorialSystem instance"""
    global _tutorial_system
    if _tutorial_system is None:
        _tutorial_system = TutorialSystem()
    return _tutorial_system
