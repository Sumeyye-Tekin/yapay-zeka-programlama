import sqlite3
import os
import re
import time
import random
import pandas as pd
from google import genai
from google.genai import types

# API anahtarını doğrudan buraya veriyoruz
API_KEY = "AQ.Ab8RN6KBzadmqt8n8LrCAdqTcGZ2uKH-LUXuWzRWLc7PXbYZhw"

# Doğrudan api_key parametresi ile istemciyi başlatıyoruz
client = genai.Client(api_key=API_KEY)

# 1. VERITABANI OLUŞTURMA VE SHADOW SCHEMA
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

cursor.execute("CREATE TABLE musteriler (musteri_id INT, ad_soyad TEXT, sehir TEXT)")
cursor.execute(
    "CREATE TABLE siparisler (siparis_id INT, musteri_id INT, tutar REAL, tarih"
    " TEXT)"
)

# TODO 1: random ile 1.000 müşteri ve 1.000 sipariş verisi üretip executemany() ile ekleyin.
sehirler = ["İstanbul", "Ankara", "Izmir", "Bursa", "Antalya"]
isimler = [
    "Ahmet",
    "Mehmet",
    "Ayşe",
    "Fatma",
    "Ali",
    "Zeynep",
    "Mustafa",
    "Elif",
    "Can",
    "Deniz",
]
soyisimler = [
    "Yılmaz",
    "Kaya",
    "Demir",
    "Çelik",
    "Şahin",
    "Yıldız",
    "Öztürk",
    "Aydın",
    "Arslan",
    "Doğan",
]

musteri_verileri = []
for i in range(1, 1001):
  ad_soyad = f"{random.choice(isimler)} {random.choice(soyisimler)}"
  sehir = random.choice(sehirler)
  musteri_verileri.append((i, ad_soyad, sehir))

siparis_verileri = []
for i in range(1, 1001):
  musteri_id = random.randint(1, 1000)
  tutar = round(random.uniform(100.0, 10000.0), 2)
  tarih = f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
  siparis_verileri.append((i, musteri_id, tutar, tarih))

cursor.executemany("INSERT INTO musteriler VALUES (?, ?, ?)", musteri_verileri)
cursor.executemany("INSERT INTO siparisler VALUES (?, ?, ?, ?)", siparis_verileri)
conn.commit()
print(
    "[BİLGİ] Veritabanı oluşturuldu. 1.000 müşteri ve 1.000 sipariş yüklendi."
)


def guvenlik_kontrolu(sql_kodu: str) -> bool:
  # TODO 2: DROP, DELETE, UPDATE, INSERT, ALTER komutlarını re.search() ile engelleyin.
  yasakli_kelimeler = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE)\b"
  if re.search(yasakli_kelimeler, sql_kodu, re.IGNORECASE):
    print(
        f"[GÜVENLİK ENGELİ] Zararlı SQL tespit edildi: Yasaklı komut içeriyor!"
    )
    return False

  temiz_kod = sql_kodu.strip().upper()
  if not temiz_kod.startswith("SELECT"):
    print(f"[GÜVENLİK ENGELİ] Sorgu SELECT ile başlamıyor!")
    return False

  return True


def clean_sql(raw_sql: str) -> str:
  # TODO 3: Gemini yanıtındaki ```sql ... ``` markdown etiketlerini regex ile temizleyin.
  cleaned = re.sub(r"```sql\s*", "", raw_sql, flags=re.IGNORECASE)
  cleaned = re.sub(r"```\s*", "", cleaned)
  return cleaned.strip()


def sql_asistani_calistir(kullanici_talebi: str):
  system_instruction = (
      "Aşağıdaki veritabanı şemasına göre kullanıcının doğal dille istediği"
      " veriyi çekecek SQLite uyumlu SQL sorgusunu yaz. Şema:"
      " Musteriler(musteri_id, ad_soyad, sehir), Siparisler(siparis_id,"
      " musteri_id, tutar, tarih). Kurallar: Sadece SELECT komutu kullan."
      " Çıktıda markdown etiketi ve açıklama olmasın, sadece saf SQL sorgusu"
      " döndür."
  )

  mevcut_talep = kullanici_talebi
  deneme = 0
  max_deneme = 3
  hata_mesaji = None

  while deneme < max_deneme:
    deneme += 1
    try:
      prompt = mevcut_talep
      if hata_mesaji:
        prompt = (
            f"Önceki yazdığın SQL hataya sebep oldu. Hata: {hata_mesaji}."
            f" Lütfen sorguyu düzelt. Orijinal istek: {kullanici_talebi}"
        )

      response = client.models.generate_content(
          model="gemini-3.5-flash-lite",  # <--- BURASI DEĞİŞTİRİLDİ (Yoğunluk almamak için)
          contents=prompt,
          config=types.GenerateContentConfig(
              system_instruction=system_instruction, temperature=0.1
          ),
      )

      raw_sql = response.text
      sql_sorgu = clean_sql(raw_sql)
      print(f"[SQL - Deneme {deneme}] {sql_sorgu}")

      # Güvenlik Kontrolü
      if not guvenlik_kontrolu(sql_sorgu):
        return None, "Güvenlik Engeli"

      # İcra Süresi Ölçümü ve Çalıştırma
      baslangic_zamani = time.perf_counter()
      df = pd.read_sql_query(sql_sorgu, conn)
      bitis_zamani = time.perf_counter()

      icra_suresi = round(bitis_zamani - baslangic_zamani, 4)
      print(f"[SONUÇ] (İcra Süresi: {icra_suresi} sn)")
      return df, icra_suresi

    except sqlite3.Error as e:
      hata_mesaji = str(e)
      print(
          f"[HATA DÜZELTME] SQLite Hatası Yakalandı: {hata_mesaji}. Gemini'ye"
          " bildiriliyor..."
      )
      if deneme == max_deneme:
        print("[HATA] Maksimum deneme sınırına ulaşıldı, sorgu başarısız.")
        return None, str(e)
    except Exception as ex:
      hata_str = str(ex)
      print(f"[HATA] Beklenmeyen hata: {hata_str}")
      # 503 veya UNAVAILABLE hatası alınırsa kısa bir süre bekleyip tekrar deneyelim
      if "503" in hata_str or "UNAVAILABLE" in hata_str:
        print(
            "[BİLGİ] Sunucu yoğunluğu (503) tespit edildi. 3 saniye bekleyip"
            " tekrar deneniyor..."
        )
        time.sleep(3)
        continue
      if deneme == max_deneme:
        return None, hata_str

  return None, "Başarısız"


if __name__ == "__main__":
  # TODO 5: while True döngüsü kurarak kullanıcıdan interaktif istek alın.
  print("\n--- AKILLI SQL ASİSTANI HAZIR ---")
  print("Örnek: İstanbul'daki müşterilerin adını ve toplam harcamasını getir.")
  print("Çıkış için 'q' yazın.\n")

  while True:
    talep = input("Soru Girin (Çıkış için 'q'): ").strip()
    if talep.lower() == "q":
      print("Çıkış yapılıyor...")
      break

    if not talep:
      continue

    print("[GEMINI] SQL Üretiliyor...")
    sonuc_df, sure = sql_asistani_calistir(talep)

    if isinstance(sonuc_df, pd.DataFrame):
      print("\nTablo Çıktısı:")
      print(sonuc_df.head(10).to_string(index=False))
      print("-" * 40 + "\n")