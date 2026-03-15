# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Simülasyonu - Güvenlik Anahtarı Üretici
=======================================================
Bu araç, API anahtarlarınızı şifreleyerek secured_keys.json dosyasını oluşturur.
Oluşturulan dosya otomatik olarak .gitignore tarafından hariç tutulur.

Kullanım:
    python tools/generate_secured_keys.py

Not: Herhangi bir alanı boş bırakabilirsiniz; o alan JSON dosyasına eklenmez.
"""

import base64
import json
import os
import sys


def _obfuscat(plain_text: str) -> str:
    """Düz metin değerini XOR+Base64+Ters çevirme ile şifreler."""
    key = 42
    xored = bytearray(b ^ key for b in plain_text.encode("utf-8"))
    b64 = base64.b64encode(bytes(xored)).decode("utf-8")
    return b64[::-1]


def _prompt(label: str, hint: str = "") -> str:
    """Kullanıcıdan bir değer ister; boş bırakılabilir."""
    display = f"{label}"
    if hint:
        display += f" ({hint})"
    display += ": "
    return input(display).strip()


def main():
    print("=" * 60)
    print("  Osmanlı Eyalet Simülasyonu - secured_keys.json Üretici")
    print("=" * 60)
    print()
    print("Değerleri girin. Kullanmadığınız alanları boş bırakın.")
    print()

    fields = {
        "github_token_encrypted": _prompt(
            "GitHub Personal Access Token",
            "ghp_... formatında, Issues:write yetkisi gerekli"
        ),
        "email_address_encrypted": _prompt(
            "E-Posta adresi",
            "örn. oyun@gmail.com"
        ),
        "email_pass_encrypted": _prompt(
            "E-Posta uygulama şifresi",
            "Gmail için 'Uygulama Şifresi' oluşturun"
        ),
        "smtp_server_encrypted": _prompt(
            "SMTP sunucu",
            "boş bırakırsanız varsayılan: smtp.gmail.com"
        ),
        "smtp_port_encrypted": _prompt(
            "SMTP port",
            "boş bırakırsanız varsayılan: 465"
        ),
    }

    # Boş olmayan değerleri şifrele
    result = {}
    for key, value in fields.items():
        if value:
            result[key] = _obfuscat(value)

    if not result:
        print("\nHiçbir değer girilmedi. Dosya oluşturulmadı.")
        return

    # Çıktı dosyasını repo kökünde oluştur
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(repo_root, "secured_keys.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Dosyayı yalnızca sahip okuyabilsin (world-readable olmayı önler)
    os.chmod(output_path, 0o600)

    print(f"\nBaşarılı! {len(result)} anahtar şifrelenerek kaydedildi:")
    print(f"  -> {output_path}")
    print()
    print("ÖNEMLİ: secured_keys.json dosyası .gitignore tarafından korunuyor.")
    print("Bu dosyayı asla git'e eklemeyin veya paylaşmayın.")


if __name__ == "__main__":
    main()
