# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eyalet Divanı Sistemi

Tarihsel: "Beylerbeyi, yanındaki defterdar ve kadı ile divan toplantısı yapar.
Her türlü devlet işi müzakere edilir, karar verilir."

4 NPC danışman her tur oyunun durumunu analiz edip rapor ve öneri üretir:
- Defterdar: Ekonomi, hazine, ticaret, enflasyon
- Kadı: Adalet, halk huzursuzluğu, millet sadakati
- Subaşı: Askeriye, savunma, tehditler
- Tahrir Emini: Nüfus, tahrir doğruluğu, gıda durumu
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class ReportSeverity(Enum):
    """Rapor önem seviyesi"""
    BILGI = "bilgi"      # Yeşil — bilgilendirme
    UYARI = "uyari"      # Sarı — dikkat gerekli
    ACIL = "acil"        # Kırmızı — acil müdahale


class AdvisorRole(Enum):
    """Danışman rolleri"""
    DEFTERDAR = "defterdar"      # Mali danışman
    KADI = "kadi"                # Adalet danışmanı
    SUBASI = "subasi"            # Güvenlik danışmanı
    TAHRIR_EMINI = "tahrir_emini"  # Nüfus/arazi danışmanı


ROLE_DISPLAY_NAMES = {
    AdvisorRole.DEFTERDAR: "Defterdar",
    AdvisorRole.KADI: "Kadı",
    AdvisorRole.SUBASI: "Subaşı",
    AdvisorRole.TAHRIR_EMINI: "Tahrir Emini",
}


@dataclass
class DivanReport:
    """Divan raporu — bir NPC'nin bir konudaki analizi"""
    severity: ReportSeverity
    category: str           # ekonomi / adalet / askeriye / nufus
    role: AdvisorRole       # Raporu üreten NPC
    advisor_name: str       # NPC'nin ismi
    message: str            # Analiz metni
    recommendation: str     # Önerilen eylem
    turn: int               # Raporun oluştuğu tur
    read: bool = False       # Okundu işareti
    resolve_key: str = ""   # Sorun tanımlayıcı — aynı key'li eski raporlar otomatik çözülür
    
    def to_dict(self) -> Dict:
        return {
            'severity': self.severity.value,
            'category': self.category,
            'role': self.role.value,
            'advisor_name': self.advisor_name,
            'message': self.message,
            'recommendation': self.recommendation,
            'turn': self.turn,
            'read': self.read,
            'resolve_key': self.resolve_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DivanReport':
        return cls(
            severity=ReportSeverity(data['severity']),
            category=data['category'],
            role=AdvisorRole(data['role']),
            advisor_name=data['advisor_name'],
            message=data['message'],
            recommendation=data['recommendation'],
            turn=data['turn'],
            read=data.get('read', False),
            resolve_key=data.get('resolve_key', '')
        )


@dataclass
class DivanAdvisor:
    """Divan danışman NPC'si"""
    role: AdvisorRole
    name: str
    skill: int = 5          # Beceri (1-10), analiz kalitesini etkiler
    loyalty: int = 70        # Sadakat (0-100)
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role.value,
            'name': self.name,
            'skill': self.skill,
            'loyalty': self.loyalty
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DivanAdvisor':
        return cls(
            role=AdvisorRole(data['role']),
            name=data['name'],
            skill=data.get('skill', 5),
            loyalty=data.get('loyalty', 70)
        )


def _generate_advisor_name(role: AdvisorRole) -> str:
    """Dönemin Osmanlı danışman ismi üret"""
    first_names = [
        "Mehmed", "Ahmed", "Mustafa", "Ali", "Süleyman", "İbrahim",
        "Mahmud", "Kasım", "Haydar", "Lütfi", "Hasan", "Hüseyin"
    ]
    
    if role == AdvisorRole.DEFTERDAR:
        suffixes = ["Çelebi", "Efendi", "Paşa"]
    elif role == AdvisorRole.KADI:
        suffixes = ["Efendi", "Molla"]
    elif role == AdvisorRole.SUBASI:
        suffixes = ["Ağa", "Bey"]
    else:
        suffixes = ["Efendi", "Çelebi"]
    
    return f"{random.choice(first_names)} {random.choice(suffixes)}"


class DivanSystem:
    """
    Eyalet Divanı — AI Danışman NPC Sistemi
    
    Her tur game_manager'ı analiz eder, 3 seviyeli raporlar üretir.
    Raporlar son 10 turdan saklanır.
    """
    
    MAX_REPORT_HISTORY = 50  # Maksimum rapor geçmişi
    
    def __init__(self):
        # 4 danışman NPC
        self.advisors: Dict[AdvisorRole, DivanAdvisor] = {}
        for role in AdvisorRole:
            self.advisors[role] = DivanAdvisor(
                role=role,
                name=_generate_advisor_name(role),
                skill=random.randint(5, 8),
                loyalty=random.randint(65, 85)
            )
        
        # Rapor geçmişi
        self.reports: List[DivanReport] = []
        self.last_analysis_turn = -1
    
    def analyze_turn(self, gm) -> List[DivanReport]:
        """
        Tüm danışmanlar ilgili sistemleri analiz eder.
        Her tur GameManager.process_turn() sonunda çağrılır.
        
        Otomatik Çözüm Mantığı:
        - Yeni raporlar üretilir (mevcut duruma göre)
        - Eski raporlardan, aynı resolve_key'e sahip olanlar kaldırılır
          (ya yeni rapor aynı sorunu günceller, ya sorun çözülmüş demektir)
        - BILGI raporları (pozitif) 3 turda otomatik silinir
        - Bu sayede 'Hazine düşük' raporu, hazine düzelince otomatik kaybolur
        """
        turn = gm.turn_count
        if turn == self.last_analysis_turn:
            return []
        
        self.last_analysis_turn = turn
        new_reports = []
        
        # Her danışman kendi alanını analiz eder
        new_reports.extend(self._analyze_defterdar(gm, turn))
        new_reports.extend(self._analyze_kadi(gm, turn))
        new_reports.extend(self._analyze_subasi(gm, turn))
        new_reports.extend(self._analyze_tahrir_emini(gm, turn))
        
        # === OTOMATİK ÇÖZÜM ===
        # Yeni raporların resolve_key'lerini topla
        new_keys = {r.resolve_key for r in new_reports if r.resolve_key}
        
        # Eski raporlardan:
        # 1) Aynı resolve_key'e sahip olanları kaldır (yenisi zaten var veya sorun çözülmüş)
        # 2) BILGI raporlarını 3 tur sonra kaldır
        # 3) UYARI/ACIL raporlarını resolve_key ile kontrol et
        surviving_reports = []
        for old in self.reports:
            # Eski raporun resolve_key'i varsa ve bu key artık yeni raporlarda da var
            # → eski kaldırılır, yenisi eklenecek (güncelleme)
            if old.resolve_key and old.resolve_key in new_keys:
                continue  # Eski raporu kaldır, yenisi zaten eklenecek
            
            # BILGI raporları 3 tur sonra otomatik silinir
            if old.severity == ReportSeverity.BILGI and (turn - old.turn) > 3:
                continue
            
            # resolve_key'li UYARI/ACIL raporlar: eğer aynı key bu tur yeniden üretilmediyse
            # → sorun çözülmüş, raporu kaldır (ama en az 1 tur göster)
            if old.resolve_key and old.resolve_key not in new_keys and old.turn < turn:
                continue  # Sorun çözülmüş!
            
            # Genel yaşlanma: resolve_key olmayan raporlar 5 tur sonra silinir
            if not old.resolve_key and (turn - old.turn) > 5:
                continue
            
            surviving_reports.append(old)
        
        self.reports = surviving_reports
        
        # Yeni raporları ekle
        self.reports.extend(new_reports)
        
        # Geçmiş sınırla
        if len(self.reports) > self.MAX_REPORT_HISTORY:
            self.reports = self.reports[-self.MAX_REPORT_HISTORY:]
        
        # Acil raporları sesli duyur
        urgent = [r for r in new_reports if r.severity == ReportSeverity.ACIL]
        if urgent:
            audio = get_audio_manager()
            audio.speak(f"Divan'dan {len(urgent)} acil rapor var!", interrupt=False)
        
        return new_reports
    
    def mark_read(self, report: DivanReport):
        """Raporu okundu olarak işaretle"""
        report.read = True
    
    def mark_all_read(self):
        """Tüm raporları okundu olarak işaretle"""
        for r in self.reports:
            r.read = True
    
    def get_unread_count(self) -> int:
        """Okunmamış rapor sayısı"""
        return sum(1 for r in self.reports if not r.read)
    
    def _skill_check(self, advisor: DivanAdvisor) -> bool:
        """
        Danışmanın beceri kontrolü.
        Düşük becerili danışman bazen sorunları gözden kaçırabilir.
        Skill 1  → %40 başarı, Skill 10 → %100 başarı
        """
        chance = 0.4 + (advisor.skill * 0.06)  # 5 skill = %70, 8 skill = %88
        return random.random() < chance
    
    def _loyalty_tamper(self, advisor: DivanAdvisor, report: DivanReport) -> DivanReport:
        """
        Sadakatsiz danışman raporu manipule edebilir.
        Düşük sadakat → önem derecesini düşürme veya yanıltıcı öneriler.
        """
        if advisor.loyalty >= 60:
            return report  # Sadık — değiştirmez
        
        # Sadakat 0-60 arasında → manipulasyon şansı
        tamper_chance = (60 - advisor.loyalty) / 100  # loyalty 30 → %30
        if random.random() < tamper_chance:
            # Acil raporu uyarıya düşür veya tamamen sakla
            if report.severity == ReportSeverity.ACIL:
                report.severity = ReportSeverity.UYARI
                report.recommendation += " (Bu danışmanın sadakati düşük — rapor güvenilir olmayabilir.)"
            elif report.severity == ReportSeverity.UYARI:
                report.severity = ReportSeverity.BILGI
        
        return report
    
    def _try_add_report(self, reports: list, advisor: DivanAdvisor, severity, category: str, message: str, recommendation: str, turn: int, resolve_key: str = ""):
        """
        Rapor oluştur ve skill/loyalty kontrolü uygula.
        resolve_key: Bu raporun hangi sorunu izlediğini belirtir.
                     Aynı resolve_key'e sahip eski raporlar, sorun çözülünce otomatik silinir.
        BILGI raporları doğrudan eklenir.
        ACIL/UYARI raporları skill check'ten geçer ve loyalty tamper'a uğrar.
        """
        report = DivanReport(
            severity=severity,
            category=category,
            role=advisor.role,
            advisor_name=advisor.name,
            message=message,
            recommendation=recommendation,
            turn=turn,
            resolve_key=resolve_key
        )
        
        if severity == ReportSeverity.BILGI:
            reports.append(report)
        else:
            if self._skill_check(advisor):
                reports.append(self._loyalty_tamper(advisor, report))
    
    def refresh_analysis(self, gm):
        """
        Mevcut duruma göre raporları yenile.
        Divan ekranına girildiğinde çağrılır — eski raporları temizleyip
        güncel analiz yapar.
        """
        turn = gm.turn_count
        
        # Bu tura ait eski raporları temizle
        self.reports = [r for r in self.reports if r.turn != turn]
        
        # Yeniden analiz et
        self.last_analysis_turn = -1  # Kilidi kaldır
        self.analyze_turn(gm)
    
    # ═══════════════════════════════════════════
    # DEFTERDAR — Mali Analiz
    # ═══════════════════════════════════════════
    def _analyze_defterdar(self, gm, turn: int) -> List[DivanReport]:
        """Defterdar: Hazine, enflasyon, gelir-gider analizi"""
        reports = []
        advisor = self.advisors[AdvisorRole.DEFTERDAR]
        eco = gm.economy
        
        # Hazine kontrolü
        gold = eco.resources.gold
        if gold < 500:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "ekonomi",
                f"Hazine tehlikeli seviyede: {gold:,} altın. İflas kapıda!",
                "Vergiyi artırın veya sikke tağşişi yapın.", turn,
                resolve_key="hazine_durum")
        elif gold < 2000:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "ekonomi",
                f"Hazine düşük: {gold:,} altın. Tedbirsizlik sıkıntı doğurur.",
                "Giderleri azaltın veya ticaret yollarını genişletin.", turn,
                resolve_key="hazine_durum")
        
        # Net gelir kontrolü
        net = eco.income.total - eco.expense.total
        if net < -500:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "ekonomi",
                f"Bütçe ciddi açık veriyor: {net:,} altın/tur.",
                "Askeri harcamaları kısın veya vergiyi artırın.", turn,
                resolve_key="butce_durum")
        elif net < 0:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "ekonomi",
                f"Bütçe açık veriyor: {net:,} altın/tur.",
                "Gelir kaynaklarını çeşitlendirin.", turn,
                resolve_key="butce_durum")
        
        # Enflasyon kontrolü
        if eco.inflation_rate > 0.30:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "ekonomi",
                f"Enflasyon çok yüksek: %{int(eco.inflation_rate * 100)}. Fiyatlar halkı eziyor!",
                "Sikke tashihi yaparak enflasyonu düşürün.", turn,
                resolve_key="enflasyon_durum")
        elif eco.inflation_rate > 0.15:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "ekonomi",
                f"Enflasyon yükseliyor: %{int(eco.inflation_rate * 100)}.",
                "Para arzını kontrol altında tutun.", turn,
                resolve_key="enflasyon_durum")
        
        # Pozitif bilgi — çok iyi hazine
        if gold > 20000 and net > 0 and not reports:
            self._try_add_report(reports, advisor, ReportSeverity.BILGI, "ekonomi",
                f"Hazine bereketli: {gold:,} altın, tur başı +{net:,} net gelir.",
                "Yeni vakıflar veya askeri genişleme için uygun zaman.", turn)
        
        return reports
    
    # ═══════════════════════════════════════════
    # KADI — Adalet ve Halk Analizi
    # ═══════════════════════════════════════════
    def _analyze_kadi(self, gm, turn: int) -> List[DivanReport]:
        """Kadı: Halk memnuniyeti, isyan riski, millet sadakati"""
        reports = []
        advisor = self.advisors[AdvisorRole.KADI]
        pop = gm.population
        
        # Memnuniyet kontrolü
        if pop.happiness < 25:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "adalet",
                f"Halk memnuniyeti kritik: %{pop.happiness}. İsyan kaçınılmaz!",
                "Vergiyi düşürün, imaret veya cami inşa edin.", turn,
                resolve_key="memnuniyet_durum")
        elif pop.happiness < 40:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "adalet",
                f"Halk memnuniyeti düşük: %{pop.happiness}.",
                "Hoşgörü politikasını gözden geçirin.", turn,
                resolve_key="memnuniyet_durum")
        
        # Huzursuzluk kontrolü
        if pop.unrest > 70:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "adalet",
                f"Huzursuzluk çok yüksek: %{pop.unrest}. Ayaklanma riski!",
                "Acil önlem: askeri güç gösterisi veya vergi indirimi.", turn,
                resolve_key="huzursuzluk_durum")
        elif pop.unrest > 50:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "adalet",
                f"Huzursuzluk artıyor: %{pop.unrest}.",
                "Halkın şikayetlerini dinleyin, adaleti sağlayın.", turn,
                resolve_key="huzursuzluk_durum")
        
        # Millet sadakati kontrolü (din sistemi)
        if hasattr(gm, 'religion'):
            from game.systems.religion import Millet, MILLET_DEFINITIONS
            for millet, state in gm.religion.millet_states.items():
                stats = MILLET_DEFINITIONS[millet]
                if state['loyalty'] < 30:
                    self._try_add_report(reports, advisor, ReportSeverity.UYARI, "adalet",
                        f"{stats.name_tr} milletinin sadakati düşük: %{state['loyalty']}.",
                        "Hoşgörü politikasını değiştirin veya liderlerle görüşün.", turn,
                        resolve_key=f"millet_sadakat_{millet.value}")
        
        # Pozitif bilgi
        if pop.happiness > 80 and pop.unrest < 10 and not reports:
            self._try_add_report(reports, advisor, ReportSeverity.BILGI, "adalet",
                f"Eyalette huzur hâkim. Memnuniyet: %{pop.happiness}, huzursuzluk: %{pop.unrest}.",
                "Mevcut politikayı sürdürün.", turn)
        
        return reports
    
    # ═══════════════════════════════════════════
    # SUBAŞI — Askeri Analiz
    # ═══════════════════════════════════════════
    def _analyze_subasi(self, gm, turn: int) -> List[DivanReport]:
        """Subaşı: Askeri güç, savunma durumu, tehditler"""
        reports = []
        advisor = self.advisors[AdvisorRole.SUBASI]
        mil = gm.military
        
        # Toplam asker kontrolü
        total_soldiers = mil.get_total_soldiers() if hasattr(mil, 'get_total_soldiers') else 0
        if total_soldiers < 200:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "askeriye",
                f"Askeri güç kritik seviyede: {total_soldiers} asker. Savunmasız durumdayız!",
                "Acilen yeniçeri veya sipahi eğitin.", turn,
                resolve_key="askeri_guc_durum")
        elif total_soldiers < 500:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "askeriye",
                f"Askeri güç yetersiz: {total_soldiers} asker.",
                "Ordunuzu güçlendirmeyi düşünün.", turn,
                resolve_key="askeri_guc_durum")
        
        # Moral kontrolü
        if hasattr(mil, 'morale'):
            if mil.morale < 30:
                self._try_add_report(reports, advisor, ReportSeverity.ACIL, "askeriye",
                    f"Askeri moral çok düşük: %{mil.morale}. Firar riski var!",
                    "Maaşları ödeyin, cihad fetvası ilan edin.", turn,
                    resolve_key="moral_durum")
            elif mil.morale < 50:
                self._try_add_report(reports, advisor, ReportSeverity.UYARI, "askeriye",
                    f"Askeri moral düşüyor: %{mil.morale}.",
                    "Asker maaşlarını ve ikmalini kontrol edin.", turn,
                    resolve_key="moral_durum")
        
        # Diplomasi tehdit kontrolü
        if hasattr(gm, 'diplomacy') and hasattr(gm.diplomacy, 'neighbors'):
            hostile_count = 0
            for nid, ndata in gm.diplomacy.neighbors.items():
                # Relation nesnesi olabilir, güvenli erişim
                if hasattr(ndata, 'value'):
                    rel = ndata.value
                elif isinstance(ndata, dict):
                    rel = ndata.get('relation', 50)
                elif isinstance(ndata, (int, float)):
                    rel = ndata
                else:
                    rel = 50
                if rel < 20:
                    hostile_count += 1
            
            if hostile_count >= 2:
                self._try_add_report(reports, advisor, ReportSeverity.ACIL, "askeriye",
                    f"{hostile_count} düşman komşu var! Çok cepheli savaş riski.",
                    "Diplomatik çözüm arayın veya savunmayı güçlendirin.", turn,
                    resolve_key="dusman_tehdit")
            elif hostile_count == 1:
                self._try_add_report(reports, advisor, ReportSeverity.UYARI, "askeriye",
                    "Bir düşman komşu ile gergin ilişkiler. Saldırı riski var.",
                    "Kale inşası veya ittifak arayışı öneriyorum.", turn,
                    resolve_key="dusman_tehdit")
        
        # Pozitif bilgi
        if total_soldiers > 1000 and not reports:
            self._try_add_report(reports, advisor, ReportSeverity.BILGI, "askeriye",
                f"Eyaletin askeri gücü sağlam: {total_soldiers} asker.",
                "Sefer veya genişleme için uygun koşullar.", turn)
        
        return reports
    
    # ═══════════════════════════════════════════
    # TAHRİR EMİNİ — Nüfus ve Arazi Analizi
    # ═══════════════════════════════════════════
    def _analyze_tahrir_emini(self, gm, turn: int) -> List[DivanReport]:
        """Tahrir Emini: Nüfus, tahrir doğruluğu, gıda durumu"""
        reports = []
        advisor = self.advisors[AdvisorRole.TAHRIR_EMINI]
        pop = gm.population
        eco = gm.economy
        
        # Tahrir doğruluğu
        accuracy = eco.tahrir_accuracy
        if accuracy < 40:
            self._try_add_report(reports, advisor, ReportSeverity.ACIL, "nufus",
                f"Tahrir kayıtları çok eski: %{accuracy} doğruluk. Vergi gelirimiz eriyor!",
                "Derhal yeni tahrir emri verin (Ekonomi ekranı).", turn,
                resolve_key="tahrir_dogruluk")
        elif accuracy < 60:
            self._try_add_report(reports, advisor, ReportSeverity.UYARI, "nufus",
                f"Tahrir kayıtları eskiyor: %{accuracy} doğruluk.",
                "Yakın zamanda tahrir yaptırmayı düşünün.", turn,
                resolve_key="tahrir_dogruluk")
        
        # Gıda durumu
        food = eco.resources.food
        food_consumption = pop.calculate_food_consumption() if hasattr(pop, 'calculate_food_consumption') else 0
        if food_consumption > 0:
            food_turns = food // food_consumption if food_consumption > 0 else 999
            if food_turns < 5:
                self._try_add_report(reports, advisor, ReportSeverity.ACIL, "nufus",
                    f"Zahire tükeniyor! Sadece {food_turns} tur yetecek kadar zahire var.",
                    "Zahire satın alın veya ticaret yolu açın.", turn,
                    resolve_key="gida_durum")
            elif food_turns < 15:
                self._try_add_report(reports, advisor, ReportSeverity.UYARI, "nufus",
                    f"Zahire azalıyor: {food:,} birim, yaklaşık {food_turns} tur yeter.",
                    "Gıda üretimini veya ticaretini artırın.", turn,
                    resolve_key="gida_durum")
        
        # Nüfus artışı bilgisi (her 10 turda bir)
        if turn % 10 == 0:
            total_pop = pop.population.total
            if total_pop > 0:
                self._try_add_report(reports, advisor, ReportSeverity.BILGI, "nufus",
                    f"Eyalet nüfusu: {total_pop:,} kişi. Tahrir doğruluğu: %{accuracy}.",
                    "Nüfus artışı sürdürülebilir seviyede." if pop.health > 50 else "Sağlık yatırımlarına ihtiyaç var.",
                    turn)
        
        return reports
    
    # ═══════════════════════════════════════════
    # SORGULAMA METODLARl
    # ═══════════════════════════════════════════
    def get_latest_reports(self, turn: int = None) -> List[DivanReport]:
        """Son turda oluşan raporlar"""
        if turn is None:
            turn = self.last_analysis_turn
        return [r for r in self.reports if r.turn == turn]
    
    def get_urgent_reports(self) -> List[DivanReport]:
        """Tüm aktif acil raporlar (son 5 tur)"""
        cutoff = max(0, self.last_analysis_turn - 5)
        return [r for r in self.reports 
                if r.severity == ReportSeverity.ACIL and r.turn >= cutoff]
    
    def get_reports_by_role(self, role: AdvisorRole) -> List[DivanReport]:
        """Belirli bir danışmanın son 10 turdaki raporları"""
        cutoff = max(0, self.last_analysis_turn - 10)
        return [r for r in self.reports 
                if r.role == role and r.turn >= cutoff]
    
    def get_all_active_reports(self) -> List[DivanReport]:
        """Son 5 turdan tüm raporlar"""
        cutoff = max(0, self.last_analysis_turn - 5)
        return [r for r in self.reports if r.turn >= cutoff]
    
    def get_report_count_by_severity(self) -> Dict:
        """Son turdaki rapor sayıları"""
        latest = self.get_latest_reports()
        return {
            'acil': len([r for r in latest if r.severity == ReportSeverity.ACIL]),
            'uyari': len([r for r in latest if r.severity == ReportSeverity.UYARI]),
            'bilgi': len([r for r in latest if r.severity == ReportSeverity.BILGI]),
            'total': len(latest)
        }
    
    def announce_summary(self):
        """Divan durumunu sesli duyur"""
        audio = get_audio_manager()
        counts = self.get_report_count_by_severity()
        
        audio.speak("Eyalet Divanı Durumu:", interrupt=True)
        
        if counts['acil'] > 0:
            audio.speak(f"{counts['acil']} acil rapor!", interrupt=False)
        if counts['uyari'] > 0:
            audio.speak(f"{counts['uyari']} uyarı.", interrupt=False)
        if counts['bilgi'] > 0:
            audio.speak(f"{counts['bilgi']} bilgilendirme.", interrupt=False)
        
        if counts['total'] == 0:
            audio.speak("Şu an rapor bulunmuyor.", interrupt=False)
        
        # Danışmanları tanıt
        for role, advisor in self.advisors.items():
            display = ROLE_DISPLAY_NAMES[role]
            audio.speak(f"{display}: {advisor.name}", interrupt=False)
    
    # ═══════════════════════════════════════════
    # KAYIT / YÜKLEME
    # ═══════════════════════════════════════════
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'advisors': {
                role.value: adv.to_dict() for role, adv in self.advisors.items()
            },
            'reports': [r.to_dict() for r in self.reports[-self.MAX_REPORT_HISTORY:]],
            'last_analysis_turn': self.last_analysis_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DivanSystem':
        """Dictionary'den yükle"""
        system = cls()
        
        # Danışmanları yükle
        for role_val, adv_data in data.get('advisors', {}).items():
            try:
                role = AdvisorRole(role_val)
                system.advisors[role] = DivanAdvisor.from_dict(adv_data)
            except ValueError:
                pass
        
        # Raporları yükle
        for r_data in data.get('reports', []):
            try:
                system.reports.append(DivanReport.from_dict(r_data))
            except (ValueError, KeyError):
                pass
        
        system.last_analysis_turn = data.get('last_analysis_turn', -1)
        
        return system
