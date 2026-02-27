# -*- coding: utf-8 -*-
"""
Kayıt Dosyası Göç (Save Migration) Sistemi
Eski oyun sürümlerinde oluşturulmuş save (kayıt) dosyalarını,
yeni eklenen sistemler (donanma, topçu vb.) için varsayılan değerlerle
doldurarak çökmeden yüklenmesini sağlar.
"""

from typing import Dict, Any
from config import SAVE_FORMAT_VERSION

class SaveMigrator:
    
    @classmethod
    def migrate(cls, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verilen save datasının versiyonunu kontrol eder,
        gerekliyse sıralı göç (migration) adımlarını uygular.
        """
        # Eski save'lerde 'version' anahtarı olmayabiliyor veya "1.1" olabiliyor
        version = save_data.get('version', '1.0')
        
        # Versiyon zaten güncelse hiçbir şeye dokunma
        if version == SAVE_FORMAT_VERSION:
            return save_data
            
        print(f"[SaveMigrator] Eski kayıt tespit edildi: v{version}. Göç işlemi başlatılıyor...")
        
        # Sıralı göç zinciri
        if version == '1.0' or version == '1.1' or version == '1.1.1':
            save_data = cls._migrate_to_1_2(save_data)
            
        # Eğer gelecekte 1.2'den 1.3'e geçiş olursa buraya eklenebilir:
        # if save_data['version'] == '1.2':
        #     save_data = cls._migrate_to_1_3(save_data)
            
        print(f"[SaveMigrator] Göç işlemi başarılı. Yeni format: v{save_data['version']}")
        return save_data
        
    @classmethod
    def _migrate_to_1_2(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Versiyon 1.1'den Versiyon 1.2'ye geçiş.
        Eklenen yeni sistemler: warfare, trade, workers, naval, artillery, espionage, religion, divan.
        """
        # Eğer eksik anahtarlar varsa varsayılan boş yapılarla doldur
        if 'warfare' not in data:
            from game.systems.warfare import WarfareSystem
            data['warfare'] = WarfareSystem().to_dict()
            
        if 'trade' not in data:
            from game.systems.economy import TradeSystem
            data['trade'] = TradeSystem().to_dict()
            
        if 'workers' not in data:
            from game.systems.workers import WorkerSystem
            data['workers'] = WorkerSystem().to_dict()
            
        if 'naval' not in data:
            # naval_system henüz to_dict desteklemiyor olabilir, güvenli default
            data['naval'] = {'ships': {}}
            
        if 'artillery' not in data:
            from game.systems.artillery import ArtillerySystem
            data['artillery'] = ArtillerySystem().to_dict()
            
        if 'espionage' not in data:
            from game.systems.espionage import EspionageSystem
            data['espionage'] = EspionageSystem().to_dict()
            
        if 'religion' not in data:
            from game.systems.religion import ReligionSystem
            data['religion'] = ReligionSystem().to_dict()
            
        if 'divan' not in data:
            from game.systems.divan import DivanSystem
            data['divan'] = DivanSystem().to_dict()
            
        # Versiyon bilgisini güncelle
        data['version'] = '1.2'
        return data
