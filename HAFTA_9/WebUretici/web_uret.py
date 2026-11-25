import os
import re
import google.generativeai as genai

# 1. Gemini API Bağlantısı
API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6J5i-3vGEkOmN2g1XzMAW_J5db0d5636jyf46FYjdDDuw")
genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash"
model = genai.GenerativeModel(model_name=MODEL_NAME)

# 2. Sistem Talimatı
sistem_mesaji = """
Sen uzman bir Frontend geliştiricisi ve UI/UX tasarımcısısın.
Görevin, kullanıcı talebine göre birbiriyle tutarlı üç HTML sayfası (`index.html`, `forgot_password.html`, `signup.html`) üretmektir.

ÇIKTI FORMATI KURALLARI (KESİNLİKLE UYULMALI):
- Yanıtını YALNIZCA aşağıdaki üç ayıraç etiketi arasına yerleştir:
  ===INDEX.HTML===
  (buraya index.html kodu)
  ===FORGOT_PASSWORD.HTML===
  (buraya forgot_password.html kodu)
  ===SIGNUP.HTML===
  (buraya signup.html kodu)
- Ayraçların dışında açıklama, selamlama veya ekstra metin yazma.
- Markdown kod blokları (```html veya ```) kullanma; doğrudan saf HTML üret.

TASARIM VE İŞLEVSELLİK KURALLARI:
- Modern, profesyonel, mobil uyumlu (responsive) ve karanlık mod (Dark Mode) tasarım kullan.
- Mor ve mavi neon renk paleti uygula; butonların üzerine gelindiğinde (hover) yumuşak parlama (glow) ve geçiş animasyonları ekle.
- Tüm CSS ve JavaScript kodlarını harici dosya kullanmadan doğrudan her HTML dosyasının içine gömülü (`<style>` ve `<script>`) olarak yaz.
- Sayfalar arası bağlantıları (`href`) eksiksiz kur:
  * `index.html` (Giriş Yap):
    - E-posta alanı, Şifre alanı (şifre göster/gizle ikonu/butonu ile)
    - "Giriş Yap" butonu
    - "Şifremi Unuttum" bağlantısı -> `forgot_password.html`
    - "Üye Ol" bağlantısı -> `signup.html`
  * `forgot_password.html` (Şifremi Unuttum):
    - "Şifremi Unuttum" başlığı
    - E-posta adresi alanı
    - "Şifre sıfırlama bağlantısı gönder" butonu
    - "Giriş sayfasına dön" bağlantısı -> `index.html`
  * `signup.html` (Üye Ol):
    - Ad Soyad alanı, E-posta alanı, Şifre alanı (şifre göster/gizle ile), Şifre tekrar alanı (şifre göster/gizle ile)
    - "Üye Ol" butonu
    - "Giriş sayfasına dön" bağlantısı -> `index.html`
- Her formda submit engellenip (`e.preventDefault()`) JavaScript ile doğrulama yapılsın:
  * Boş alan kontrolü
  * Geçerli e-posta formatı kontrolü
  * `signup.html` sayfasında şifre ile şifre tekrar alanının eşleşme kontrolü (ve minimum şifre uzunluğu kontrolü)
  * Hata ve başarı mesajları kullanıcıya anlaşılır şekilde arayüzde gösterilsin.
"""

# 3. Kullanıcı Tasarım Talebi
varsayilan_talep = (
    "Modern, profesyonel, karanlık temalı bir üyelik sistemi oluştur. "
    "Mor ve mavi neon renkler kullan. Login, Forgot Password ve Signup sayfaları "
    "aynı tasarım dilini kullansın. Sayfalar arasında geçişler çalışsın. "
    "Butonların üzerine gelindiğinde parlama efekti oluşsun."
)

print("=== Yapay Zekâ Destekli Web Sayfası Üretici ===")
kullanici_girdisi = input(
    "Tasarım talebinizi girin (varsayılan talebi kullanmak için Enter'a basın):\n> "
).strip()
tasarim_talebi = kullanici_girdisi if kullanici_girdisi else varsayilan_talep

# 4. API İsteği
print("\nGemini API'ye istek gönderiliyor, lütfen bekleyin...")
response = model.generate_content(
    sistem_mesaji + "\n\nKullanıcı talebi:\n" + tasarim_talebi,
    generation_config={"temperature": 0.5, "max_output_tokens": 16000},
)

ham_yanit = response.text or ""

# 5. Ayrıştırma (Parsing), Markdown Temizleme ve Dosya Kayıt
dosya_etiketleri = {
    "index.html": "===INDEX.HTML===",
    "forgot_password.html": "===FORGOT_PASSWORD.HTML===",
    "signup.html": "===SIGNUP.HTML===",
}


def markdown_temizle(kod: str) -> str:
    # ```html, ```HTML, ```css, ```js veya ``` gibi blok işaretlerini temizle
    temiz = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", kod.strip())
    temiz = re.sub(r"\s*```$", "", temiz.strip())
    temiz = temiz.replace("```html", "").replace("```", "").strip()
    return temiz


etiket_sirasi = list(dosya_etiketleri.items())

for idx, (dosya_adi, baslangic_etiketi) in enumerate(etiket_sirasi):
    bas_index = ham_yanit.find(baslangic_etiketi)
    if bas_index == -1:
        print(f"[UYARI] '{baslangic_etiketi}' etiketi yanıtta bulunamadı ({dosya_adi} atlandı).")
        continue

    icerik_bas = bas_index + len(baslangic_etiketi)

    # Bir sonraki etiketin başlangıcını bul; son dosyaysa metnin sonuna kadar al
    if idx + 1 < len(etiket_sirasi):
        sonraki_etiket = etiket_sirasi[idx + 1][1]
        bit_index = ham_yanit.find(sonraki_etiket, icerik_bas)
        parca = ham_yanit[icerik_bas:bit_index] if bit_index != -1 else ham_yanit[icerik_bas:]
    else:
        parca = ham_yanit[icerik_bas:]

    html_kodu = markdown_temizle(parca)

    with open(dosya_adi, "w", encoding="utf-8") as dosya:
        dosya.write(html_kodu)

    print(f"[TAMAM] '{dosya_adi}' başarıyla oluşturuldu ({len(html_kodu)} karakter).")

print("\nİşlem tamamlandı. Oluşan HTML dosyalarını tarayıcıda açarak test edebilirsiniz.")