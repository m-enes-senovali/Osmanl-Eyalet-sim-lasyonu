# -*- coding: utf-8 -*-
"""
Danışman (Kethüda) Sistemi
Oyuncuya eyaletin genel durumu hakkında özet rapor ve acil uyarılar sunar.
Verileri her çağrıldığında o anki durumdan anlık olarak alır (gecikmeli/eski veri olmaz).
"""

from typing import List, Dict, Tuple
from enum import Enum

class Urgency(Enum):
    CRITICAL = 3  # Kırmızı (Acil müdahale)
    WARNING = 2   # Sarı (Dikkat edilmeli)
    INFO = 1      # Yeşil/Beyaz (Genel bilgi)

class AdvisorSystem:
    def __init__(self, game_manager):
        self.gm = game_manager

    def get_report(self) -> List[Tuple[Urgency, str]]:
        """
        Tüm sistemleri tarayarak güncel durumu analiz eder.
        Dönen liste aciliyet sırasına (CRITICAL -> WARNING -> INFO) göre sıralanmıştır.
        """
        report = []
        
        # 1. BAĞLILIK VE İSYAN (Kritik Hayatta Kalma)
        sultan_loyalty = getattr(self.gm.diplomacy, 'sultan_loyalty', 100)
        revolt_risk = getattr(self.gm.population, 'revolt_risk', 0)
        happiness = getattr(self.gm.population, 'happiness', 100)
        
        if sultan_loyalty < 30:
            report.append((Urgency.CRITICAL, f"Sultan'ın sadakati çok düşük (%{sultan_loyalty})! Görevden alınmamak için derhal divana katılıp sadakati artırın veya rüşvet verin."))
        elif sultan_loyalty < 50:
            report.append((Urgency.WARNING, f"Sultan bize şüpheyle bakıyor (Sadakat: %{sultan_loyalty}). Divan ile ilişkileri düzeltmekte fayda var."))
            
        if revolt_risk > 80:
            report.append((Urgency.CRITICAL, f"İsyan kapıda! Halkın isyan riski %{revolt_risk}. Derhal vergileri düşürün veya asayişi sağlayın."))
        elif revolt_risk > 50:
            report.append((Urgency.WARNING, f"Halk huzursuzlanıyor (İsyan Riski: %{revolt_risk}). Mutluluğu artıracak binalar inşa edebiliriz."))
            
        if happiness < 30:
            report.append((Urgency.WARNING, f"Halkın mutsuzluğu had safhada (Mutluluk: %{happiness}). Camii veya hamam inşaatı düşünün."))

        # 2. EKONOMİ (Hazine ve Üretim)
        gold = getattr(self.gm.economy.resources, 'gold', 0)
        food = getattr(self.gm.economy.resources, 'food', 0)
        wood = getattr(self.gm.economy.resources, 'wood', 0)
        iron = getattr(self.gm.economy.resources, 'iron', 0)
        
        if gold <= 0:
            report.append((Urgency.CRITICAL, "Hazine tamamen boş! Derhal vergi toplamalı veya bir üretim yapmalıyız, aksi takdirde askerler firar edebilir."))
        elif gold < 1000:
            report.append((Urgency.WARNING, f"Hazinede sadece {gold} altın kaldı. Yeni inşaatlar için daha fazla gelire ihtiyacımız olacak."))
            
        if food < 50:
            report.append((Urgency.WARNING, "Erzak depoları tükenmek üzere! Halk açlık çekerse isyan çıkabilir. Çiftlikleri güçlendirin."))
        if wood < 50 and iron < 50:
            report.append((Urgency.INFO, "Odun ve Demir stoklarımız düşük. İnşaat ve ordu üretimi için kaynak toplamanız gerekebilir."))

        # 3. İŞGÜCÜ (Üretim Potansiyeli)
        idle_workers = getattr(self.gm.population, 'idle_workers', 0)
        total_workers = getattr(self.gm.population, 'total_workers', 1)
        
        # Eğer çok fazla boşta işçi varsa uyar
        if total_workers > 0 and (idle_workers / total_workers) > 0.5 and total_workers > 10:
            report.append((Urgency.INFO, f"Eyalette {idle_workers} kişi boşta geziyor paşam. Onları loncalara atayarak ekonomiye kazandırabiliriz."))
        elif total_workers > 0 and idle_workers == 0:
            report.append((Urgency.INFO, "Tüm iş gücümüz tam kapasite çalışıyor, çok güzel."))

        # 4. ORDU VE SAVUNMA
        total_soldiers = sum(self.gm.military.units.values())
        if total_soldiers < 1000 and gold > 5000:
            report.append((Urgency.WARNING, "Hazinede altınımız var ancak ordumuz çok zayıf. Olası bir Safevi veya Venedik saldırısına karşı asker toplamalıyız."))
        
        morale = getattr(self.gm.military, 'morale', 100)
        if morale < 40:
            report.append((Urgency.WARNING, f"Ordunun morali çok düşük (%{morale}). Savaşlarda dezavantajlı olacağız, tatbikat yapabilirsiniz."))

        # 5. AKTİF OLAYLAR / İŞGAL
        current_invasion = getattr(self.gm, 'current_invasion', None)
        if current_invasion:
            invader = current_invasion.get('invader', 'Düşman')
            report.append((Urgency.CRITICAL, f"DİKKAT! {invader} şu an topraklarımızı kuşatıyor! Derhal 'Akın/Savaş' ekranına giderek şehri savunun!"))

        # Eğer hiçbir kritik sorun yoksa, genel bir iyi durum bildirimi ekle
        if not report:
            report.append((Urgency.INFO, "Eyalette asayiş berkemal paşam. Her şey yolunda görünüyor."))
        elif len([r for r in report if r[0] != Urgency.INFO]) == 0:
            report.append((Urgency.INFO, "Acil bir tehlike görünmüyor paşam, yönetiminiz altında güvendeyiz."))

        # Aciliyete göre sırala (CRITICAL önce, sonra WARNING, sonra INFO)
        # Urgency enum değerine göre sıralama: 3 (Critical), 2 (Warning), 1 (Info)
        # Tersten sıralayacağız ki büyük numaralar üste gelsin.
        report.sort(key=lambda x: x[0].value, reverse=True)
        
        return report

    def get_summary_text(self) -> str:
        """Ekran okuma için düz metin çıktısı verir."""
        report = self.get_report()
        if not report:
            return "Asayiş berkemal paşam, hiçbir sorunumuz yok."
            
        lines = ["Kethüda Raporu:"]
        for urgency, msg in report:
            if urgency == Urgency.CRITICAL:
                prefix = "KRİTİK DURUM: "
            elif urgency == Urgency.WARNING:
                prefix = "Uyarı: "
            else:
                prefix = "Bilgi: "
            lines.append(f"{prefix}{msg}")
            
        return " ".join(lines)
