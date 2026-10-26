from google import genai

# API istemcisini tanımlayın
client = genai.Client(api_key="BURAYA_ANAHTAR_GELECEK")

# Veritabanı şeması
sema = """
1. Musteriler Tablosu: musteri_id, ad_soyad, eposta, sehir
2. Siparisler Tablosu: siparis_id, musteri_id, tutar, siparis_tarihi
"""

# Güncellenen yeni doğal dil talebiniz (5000 TL altı alışverişler)
talep = """
Son 30 günde 5000 TL altı alışveriş yapan İstanbul'daki müşterilerin sayılarını, siparis tarihlerini getir.
"""


def sql_uretici(veritabani_semasi, kullanici_talebi):
    print(
        "========================================================================="
    )
    print("               YAPAY ZEKA DESTEKLİ DOĞAL DİLDEN SQL ÜRETİCİ")
    print(
        "========================================================================="
    )

    print("\n[AŞAMA 1] VERİTABANI ŞEMASI VE KULLANICI TALEBİ ALINDI...")
    print("\n[AŞAMA 2] SQL ÇEVİRİSİ İÇİN GEMİNİ'YE BAĞLANILIYOR...")

    prompt = f"""
    Aşağıdaki veritabanı şemasını ve kullanıcının doğal dildeki talebini analiz et. 
    Bu istek doğrultusunda uygun olan SQL sorgusunu yaz. Sadece SQL kodunu döndür, ekstra markdown formatı veya açıklama ekleme.

    Veritabanı Şeması:
    {veritabani_semasi}

    Kullanıcı Talebi:
    {kullanici_talebi}
    """

    print("Gemini isteği gönderiliyor...")

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite", contents=prompt
        )

        print("Gemini yanıtı alındı!")
        print(
            "========================================================================="
        )
        print("                         ÜRETİLEN SQL SORGUSU")
        print(
            "========================================================================="
        )

        # Gelen yanıttaki olası markdown işaretlerini temizleyelim
        temiz_sql = (
            response.text.replace("```sql", "").replace("```", "").strip()
        )
        print(temiz_sql)
        print(
            "========================================================================="
        )

    except Exception as e:
        print(f"[HATA] API çağrısı sırasında bir hata oluştu: {e}")


if __name__ == "__main__":
    sql_uretici(sema, talep)