from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'bengkel_super_rahasia'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Masukkan password MySQL Anda jika ada
        database="toko_online"
    )

# 1. HALAMAN UTAMA (Dashboard)
@app.route('/')
def index():
    return render_template('index.html')

# 2. HALAMAN DAFTAR PRODUK (PELANGGAN)
@app.route('/produk')
def produk():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Produk")
    daftar_produk = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('produk.html', produk_data=daftar_produk)

# 3. PROSES TRANSAKSI BELI PRODUK (PELANGGAN)
@app.route('/beli/<int:id_produk>', methods=['POST'])
def beli_produk(id_produk):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Nama_produk, Harga_produk, Stok FROM Produk WHERE Id_Produk = %s", (id_produk,))
    produk = cursor.fetchone()
    
    if produk and produk['Stok'] > 0:
        cursor.execute("UPDATE Produk SET Stok = Stok - 1 WHERE Id_Produk = %s", (id_produk,))
        query_riwayat = """
            INSERT INTO Riwayat_Transaksi (Tipe_Transaksi, Nama_Item, Metode_Pembayaran, Total_Harga)
            VALUES ('Pembelian Produk', %s, 'QRIS', %s)
        """
        cursor.execute(query_riwayat, (produk['Nama_produk'], produk['Harga_produk']))
        conn.commit()
        flash(f"🎉 Sukses membeli {produk['Nama_produk']}! Transaksi berhasil dicatat.", "success")
    else:
        flash("❌ Gagal membeli! Stok habis.", "danger")
    cursor.close()
    conn.close()
    return redirect(url_for('produk'))

# 4. HALAMAN DAFTAR SERVIS
@app.route('/servis')
def servis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Servis")
    daftar_servis = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('servis.html', servis_data=daftar_servis)

# 5. PROSES BOOKING SERVIS
@app.route('/booking/<int:id_servis>', methods=['POST'])
def booking_servis(id_servis):
    metode_bayar = request.form.get('metode_pembayaran')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Jenis_servis, Harga_Servis FROM Servis WHERE Id_Servis = %s", (id_servis,))
    servis = cursor.fetchone()
    
    if servis:
        query_riwayat = """
            INSERT INTO Riwayat_Transaksi (Tipe_Transaksi, Nama_Item, Metode_Pembayaran, Total_Harga)
            VALUES ('Booking Servis', %s, %s, %s)
        """
        cursor.execute(query_riwayat, (servis['Jenis_servis'], metode_bayar, servis['Harga_Servis']))
        conn.commit()
        flash(f"✅ Booking Berhasil untuk {servis['Jenis_servis']} via {metode_bayar}! Riwayat dicatat.", "success")
    else:
        flash("❌ Jasa servis tidak ditemukan.", "danger")
    cursor.close()
    conn.close()
    return redirect(url_for('servis'))

# 6. HALAMAN RIWAYAT TRANSAKSI
@app.route('/riwayat')
def riwayat():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Riwayat_Transaksi ORDER BY Id_Transaksi DESC")
    semua_riwayat = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('riwayat.html', riwayat_data=semua_riwayat)


# =======================================================
# PANEL ADMIN (CRUD + UPDATE STOK)
# =======================================================

@app.route('/admin')
def admin_panel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Produk ORDER BY Id_Produk DESC")
    daftar_produk = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', produk_data=daftar_produk)

@app.route('/admin/tambah', methods=['POST'])
def admin_tambah():
    nama = request.form.get('nama_produk')
    harga = request.form.get('harga_produk')
    stok = request.form.get('stok_produk')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Produk (Nama_produk, Harga_produk, Stok) VALUES (%s, %s, %s)", (nama, harga, stok))
    conn.commit()
    cursor.close()
    conn.close()
    flash("📦 Produk baru berhasil ditambahkan ke database!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/hapus/<int:id_produk>', methods=['POST'])
def admin_hapus(id_produk):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Produk WHERE Id_Produk = %s", (id_produk,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("🗑️ Produk berhasil dihapus dari database!", "danger")
    return redirect(url_for('admin_panel'))


# --- FITUR BARU: UTK MENGELOLA STOK (MANUAL ADMIN) ---

# Rute Tambah Stok +1
@app.route('/admin/stok_tambah/<int:id_produk>', methods=['POST'])
def stok_tambah(id_produk):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Produk SET Stok = Stok + 1 WHERE Id_Produk = %s", (id_produk,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("🔼 Stok produk berhasil ditambah 1!", "info")
    return redirect(url_for('admin_panel'))

# Rute Kurang Stok -1
@app.route('/admin/stok_kurang/<int:id_produk>', methods=['POST'])
def stok_kurang(id_produk):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cek dulu apakah stoknya sudah 0 atau belum, biar tidak minus
    cursor.execute("SELECT Stok FROM Produk WHERE Id_Produk = %s", (id_produk,))
    produk = cursor.fetchone()
    
    if produk and produk['Stok'] > 0:
        cursor.execute("UPDATE Produk SET Stok = Stok - 1 WHERE Id_Produk = %s", (id_produk,))
        conn.commit()
        flash("🔽 Stok produk berhasil dikurangi 1!", "warning")
    else:
        flash("❌ Gagal mengurangi! Stok sudah mencapai angka 0.", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)