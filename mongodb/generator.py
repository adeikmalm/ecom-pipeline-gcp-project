import os
import requests
import random
import time
from datetime import datetime, timezone
from pymongo import MongoClient
from faker import Faker
from dotenv import load_dotenv

# Load variabel dari file .env
load_dotenv()

# Inisialisasi Faker
fake = Faker()



# os.getenv() akan mengambil nilai MONGO_URI dari file .env
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "oltp_ecommerce"
COLLECTION_NAME = "carts"

# Validasi jika MONGO_URI tidak terbaca
if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI tidak ditemukan! Pastikan file .env sudah dibuat dan terisi.")

# Koneksi ke MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# 1. FETCH MASTER DATA DARI FAKESTORE API

def fetch_master_data():
    print("Mengambil Master Data dari FakeStore API...")
    try:
        users = requests.get("https://fakestoreapi.com/users").json()
        products = requests.get("https://fakestoreapi.com/products").json()
        print(f"Berhasil mengambil {len(users)} users dan {len(products)} products.\n")
        return users, products
    except Exception as e:
        print(f"Gagal mengambil API: {e}")
        return [], []

# 2. FUNGSI GENERATE TRANSAKSI (DENGAN ANOMALI)
def generate_cart_event(users, products):
    now_utc = datetime.now(timezone.utc)
    
    # Menentukan Partisi Waktu
    gmt_create = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    dt = int(now_utc.strftime("%Y%m%d"))
    
    # Pilih user dan produk secara acak
    selected_user = random.choice(users)
    num_items = random.randint(1, 4)
    selected_products = random.sample(products, num_items)
    
    # Format keranjang standar (Data Bersih)
    cart_items = []
    for p in selected_products:
        cart_items.append({
            "product_id": p['id'],
            "price": p['price'],
            "quantity": random.randint(1, 5)
        })

    payload = {
        "transaction_id": fake.uuid4(),
        "user_id": selected_user['id'],
        "dt": dt,
        "gmt_create": gmt_create,
        "items": cart_items,
        "status": random.choice(["completed", "completed", "completed", "failed"]),
        "is_anomalous": False # Flag bawaan
    }

    # INJEKSI MESSY DATA (Probabilitas 15%)
    if random.random() < 0.15:
        payload["is_anomalous"] = True
        anomali_tipe = random.choice(["missing_user", "string_price", "negative_qty"])
        
        if anomali_tipe == "missing_user":
            # Anomali 1: User ID tiba-tiba Null
            payload["user_id"] = None 
            
        elif anomali_tipe == "string_price":
            # Anomali 2: Harga tiba-tiba berubah jadi string kacau
            payload["items"][0]["price"] = f"{payload['items'][0]['price']} USD"
            
        elif anomali_tipe == "negative_qty":
            # Anomali 3: Kuantitas minus (indikasi error sistem)
            payload["items"][0]["quantity"] = random.randint(-5, -1)

    return payload

# 3. MAIN LOOP (EKSEKUSI TERUS-MENERUS)
def main():
    users, products = fetch_master_data()
    
    if not users or not products:
        print("Data master kosong, program dihentikan.")
        return

    # 1. TAMBAHAN BARU: Insert Master Data ke MongoDB
    print("Menyimpan data master ke MongoDB...")
    # Menghapus data lama (jika ada) untuk mencegah duplikasi ID saat script dijalankan ulang
    db.users.delete_many({}) 
    db.products.delete_many({})
    
    # Menyimpan data baru ke collection terpisah
    db.users.insert_many(users)
    db.products.insert_many(products)
    print("Data master berhasil disimpan ke collection 'users' dan 'products'.")

    # 2. EKSEKUSI TRANSAKSI
    print("Memulai Generator Transaksi Real-Time...")
    print("Tekan CTRL+C untuk menghentikan program.\n")
    
    try:
        while True:
            event = generate_cart_event(users, products)
            collection.insert_one(event) # collection ini merujuk ke 'carts'
            
            if event["is_anomalous"]:
                print(f"[ANOMALI] Transaksi {event['transaction_id']} di-insert! (Data kotor)")
            else:
                print(f"[NORMAL] Transaksi {event['transaction_id']} di-insert.")
            
            time.sleep(random.randint(2, 5))
            
    except KeyboardInterrupt:
        print("\nGenerator dihentikan secara manual.")

if __name__ == "__main__":
    main()