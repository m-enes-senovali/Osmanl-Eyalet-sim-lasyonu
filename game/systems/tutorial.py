# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eğitim/Tutorial Sistemi
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
    ECONOMY = "economy"
    MILITARY = "military"
    DIPLOMACY = "diplomacy"


@dataclass
class TutorialStep:
    """Tutorial adımı"""
    id: str
    chapter: TutorialChapter
    title: str
    description: str
    instruction: str  # Yapılması gereken eylem
    target_screen: str = None  # Hedef ekran (opsiyonel)
    target_action: str = None  # Hedef eylem (kontrol için)
    completed: bool = False
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'chapter': self.chapter.value,
            'completed': self.completed
        }


# Tutorial adımları tanımı
TUTORIAL_STEPS: List[TutorialStep] = []


def _init_tutorial_steps():
    """Tüm tutorial adımlarını tanımla"""
    global TUTORIAL_STEPS
    
    TUTORIAL_STEPS = [
        # === BÖLÜM 1: TEMEL KONTROLLER ===
        TutorialStep(
            id="basics_1",
            chapter=TutorialChapter.BASICS,
            title="Hoş Geldiniz!",
            description="Osmanlı Eyalet Yönetim Simülasyonuna hoş geldiniz! Bu eğitim size oyunun temellerini öğretecek.",
            instruction="Devam etmek için Enter tuşuna basın.",
            target_action="enter"
        ),
        TutorialStep(
            id="basics_2",
            chapter=TutorialChapter.BASICS,
            title="Menü Navigasyonu",
            description="Menülerde gezinmek için yukarı ve aşağı ok tuşlarını kullanın.",
            instruction="Aşağı ok tuşuna basarak bir sonraki menü öğesine gidin.",
            target_action="navigate_down"
        ),
        TutorialStep(
            id="basics_3",
            chapter=TutorialChapter.BASICS,
            title="Seçim Yapma",
            description="Bir öğeyi seçmek veya menüye girmek için Enter tuşuna basın.",
            instruction="Enter tuşuna basarak seçim yapın.",
            target_action="enter"
        ),
        TutorialStep(
            id="basics_4",
            chapter=TutorialChapter.BASICS,
            title="Geri Gitme",
            description="Bir önceki ekrana dönmek için Backspace tuşunu kullanın.",
            instruction="Backspace tuşuna basarak geri gidin.",
            target_action="back"
        ),
        TutorialStep(
            id="basics_5",
            chapter=TutorialChapter.BASICS,
            title="Tur Geçirme",
            description="Oyunda ilerlemek için tur geçirmeniz gerekir. Space tuşu ile tur geçirin.",
            instruction="Space tuşuna basarak bir tur geçirin.",
            target_action="next_turn"
        ),
        
        # === BÖLÜM 2: EKONOMİ ===
        TutorialStep(
            id="economy_1",
            chapter=TutorialChapter.ECONOMY,
            title="Ekonomi Ekranı",
            description="Ekonomi ekranında hazinenizi ve gelir-gider durumunuzu görebilirsiniz.",
            instruction="E tuşuna basarak Ekonomi ekranını açın.",
            target_screen="ECONOMY",
            target_action="open_economy"
        ),
        TutorialStep(
            id="economy_2",
            chapter=TutorialChapter.ECONOMY,
            title="Hazine Durumu",
            description="Sol üstte hazinenizdeki altın miktarını görebilirsiniz. Altın, tüm eylemler için gereklidir.",
            instruction="F1 tuşuna basarak mevcut durumu dinleyin.",
            target_action="announce"
        ),
        TutorialStep(
            id="economy_3",
            chapter=TutorialChapter.ECONOMY,
            title="Vergi Oranı",
            description="Vergi oranını değiştirerek gelirinizi artırabilirsiniz. Ancak yüksek vergi halkı mutsuz eder.",
            instruction="Menüden vergi ayarını bulun ve Enter ile değiştirin.",
            target_action="change_tax"
        ),
        TutorialStep(
            id="economy_4",
            chapter=TutorialChapter.ECONOMY,
            title="İşçiler",
            description="İşçiler kaynak üretimini artırır. Farklı alanlara işçi atayabilirsiniz.",
            instruction="Backspace ile geri dönün, sonra W tuşuyla İşçiler ekranına gidin.",
            target_screen="WORKERS",
            target_action="open_workers"
        ),
        TutorialStep(
            id="economy_5",
            chapter=TutorialChapter.ECONOMY,
            title="Ticaret",
            description="Ticaret yolları kurarak diğer devletlerle alışveriş yapabilirsiniz.",
            instruction="Backspace ile geri dönün, sonra T tuşuyla Ticaret ekranına gidin.",
            target_screen="TRADE",
            target_action="open_trade"
        ),
        TutorialStep(
            id="economy_6",
            chapter=TutorialChapter.ECONOMY,
            title="Ekonomi Tamamlandı",
            description="Harika! Ekonomi yönetiminin temellerini öğrendiniz.",
            instruction="Devam etmek için Enter'a basın.",
            target_action="enter"
        ),
        
        # === BÖLÜM 3: ASKERİ ===
        TutorialStep(
            id="military_1",
            chapter=TutorialChapter.MILITARY,
            title="Ordu Ekranı",
            description="Ordu ekranında askerlerinizi yönetebilirsiniz.",
            instruction="M tuşuna basarak Ordu ekranını açın.",
            target_screen="MILITARY",
            target_action="open_military"
        ),
        TutorialStep(
            id="military_2",
            chapter=TutorialChapter.MILITARY,
            title="Asker Toplama",
            description="Yeniçeri, Sipahi ve diğer birlikleri toplayabilirsiniz. Her birliğin maliyeti ve gücü farklıdır.",
            instruction="Menüden bir birlik türü seçin.",
            target_action="select_unit"
        ),
        TutorialStep(
            id="military_3",
            chapter=TutorialChapter.MILITARY,
            title="Savaş",
            description="Ordu hazır olduğunda savaş başlatabilirsiniz.",
            instruction="Backspace ile geri dönün.",
            target_action="back"
        ),
        TutorialStep(
            id="military_4",
            chapter=TutorialChapter.MILITARY,
            title="İnşaat",
            description="C tuşuyla İnşaat ekranına giderek binalar inşa edebilirsiniz.",
            instruction="C tuşuna basarak İnşaat ekranını açın.",
            target_screen="CONSTRUCTION",
            target_action="open_construction"
        ),
        TutorialStep(
            id="military_5",
            chapter=TutorialChapter.MILITARY,
            title="Askeri Tamamlandı",
            description="Harika! Askeri yönetimin temellerini öğrendiniz.",
            instruction="Devam etmek için Enter'a basın.",
            target_action="enter"
        ),
        
        # === BÖLÜM 4: DİPLOMASİ ===
        TutorialStep(
            id="diplomacy_1",
            chapter=TutorialChapter.DIPLOMACY,
            title="Diplomasi Ekranı",
            description="Diplomasi ekranında diğer devletlerle ilişkilerinizi yönetebilirsiniz.",
            instruction="D tuşuna basarak Diplomasi ekranını açın.",
            target_screen="DIPLOMACY",
            target_action="open_diplomacy"
        ),
        TutorialStep(
            id="diplomacy_2",
            chapter=TutorialChapter.DIPLOMACY,
            title="Devletler",
            description="Listede diğer devletleri ve onlarla olan ilişkilerinizi görebilirsiniz.",
            instruction="Bir devlet seçin.",
            target_action="select_state"
        ),
        TutorialStep(
            id="diplomacy_3",
            chapter=TutorialChapter.DIPLOMACY,
            title="Casusluk",
            description="S tuşuyla Casusluk ekranına giderek casus gönderebilirsiniz.",
            instruction="Backspace ile geri dönün, sonra S tuşuyla Casusluk ekranına gidin.",
            target_screen="ESPIONAGE",
            target_action="open_espionage"
        ),
        TutorialStep(
            id="diplomacy_4",
            chapter=TutorialChapter.DIPLOMACY,
            title="Eğitim Tamamlandı!",
            description="Tebrikler! Oyunun temellerini başarıyla öğrendiniz. Artık kendi imparatorluğunuzu yönetmeye hazırsınız!",
            instruction="Oyuna başlamak için Enter'a basın.",
            target_action="enter"
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
                
                # Tamamlanan adımları işaretle
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
        self._announce_current_step()
    
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
    
    def advance(self):
        """Bir sonraki adıma geç"""
        current = self.get_current_step()
        if current:
            current.completed = True
        
        self.current_step_index += 1
        
        if self.current_step_index >= len(self.steps):
            self._complete_tutorial()
        else:
            self._announce_current_step()
            self.save_progress()
    
    def _complete_tutorial(self):
        """Tutorial'ı tamamla"""
        self.is_active = False
        self.completed = True
        self.save_progress()
        self.audio.speak(
            "Tebrikler! Eğitimi başarıyla tamamladınız. "
            "Artık Osmanlı İmparatorluğunu yönetmeye hazırsınız!",
            interrupt=True
        )
    
    def _announce_current_step(self):
        """Mevcut adımı duyur"""
        step = self.get_current_step()
        if step:
            # Bölüm değişimi kontrolü
            prev_step = self.steps[self.current_step_index - 1] if self.current_step_index > 0 else None
            if not prev_step or prev_step.chapter != step.chapter:
                chapter_names = {
                    TutorialChapter.BASICS: "Temel Kontroller",
                    TutorialChapter.ECONOMY: "Ekonomi Yönetimi",
                    TutorialChapter.MILITARY: "Askeri Yönetim",
                    TutorialChapter.DIPLOMACY: "Diplomasi"
                }
                self.audio.speak(f"Bölüm: {chapter_names[step.chapter]}", interrupt=True)
            
            # Adımı duyur
            self.audio.speak(
                f"{step.title}. {step.description} {step.instruction}",
                interrupt=False
            )
    
    def check_action(self, action: str, screen: str = None) -> bool:
        """
        Eylem kontrolü yap.
        Doğru eylem yapıldıysa bir sonraki adıma geç.
        
        Returns: True eğer adım tamamlandıysa
        """
        if not self.is_active:
            return False
        
        step = self.get_current_step()
        if not step:
            return False
        
        # Ekran kontrolü
        if step.target_screen and screen:
            if screen.upper() == step.target_screen:
                self.advance()
                return True
        
        # Eylem kontrolü
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
        
        for step in self.steps:
            step.completed = False
        
        self.save_progress()
        self.audio.speak("Eğitim sıfırlandı.", interrupt=True)


# Global instance
_tutorial_system: Optional[TutorialSystem] = None


def get_tutorial_system() -> TutorialSystem:
    """Global TutorialSystem instance"""
    global _tutorial_system
    if _tutorial_system is None:
        _tutorial_system = TutorialSystem()
    return _tutorial_system
