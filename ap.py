import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
from io import BytesIO
import base64
from datetime import datetime as dt
from datetime import datetime
UPLOAD_DIR = "uploads"
LAPORAN_FILE = "laporan_warga.json"
import pytz
import subprocess
import json
import os
from PIL import Image
from rapidfuzz import process, fuzz


# ---------------------- Konfigurasi halaman ----------------------
import streamlit as st

st.set_page_config(
    page_title="Dashboard Pertanian Cerdas",
    layout="wide"
)

# ------------------ Dark Mode State ------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ------------------ Toggle Function ------------------
def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.experimental_rerun()

# ------------------ Warna Utama ------------------
COLOR_HIJAU_PADI = "#D4F1BE"
COLOR_BIRU_TUA = "#0A2647"
COLOR_BIRU_AIR = "#B6E2D3"
COLOR_PUTIH = "#FFFFFF"
COLOR_HITAM = "#000000"

# ------------------ Tema ------------------
LIGHT_THEME = {
    "sidebar_bg": f"linear-gradient(to bottom, {COLOR_HIJAU_PADI}, {COLOR_BIRU_AIR})",
    "main_bg": COLOR_PUTIH,
    "text_color": COLOR_HITAM,
    "input_bg": "#f7f7f7",
    "input_text": COLOR_HITAM,
}

DARK_THEME = {
    "sidebar_bg": f"linear-gradient(to bottom, {COLOR_BIRU_TUA}, {COLOR_BIRU_AIR})",
    "main_bg": COLOR_BIRU_TUA,
    "text_color": COLOR_PUTIH,
    "input_bg": "#1c1c1c",
    "input_text": COLOR_PUTIH,
}

theme = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME

# ------------------ CSS Styling ------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {theme['main_bg']};
        color: {theme['text_color']};
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        background: {theme['sidebar_bg']};
    }}
    section[data-testid="stSidebar"] * {{
        color: {theme['text_color']} !important;
    }}
    input, textarea, select {{
        background-color: {theme['input_bg']} !important;
        color: {theme['input_text']} !important;
    }}
    label {{
        color: {theme['text_color']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------ Sidebar ------------------
with st.sidebar:
    st.button(
        "🌗 Toggle Dark Mode",
        on_click=toggle_dark_mode
    )
    
# ------------------ INPUT KOORDINAT ------------------
LAT = st.sidebar.number_input("Latitude", value=-3.921406, format="%.6f")
LON = st.sidebar.number_input("Longitude", value=119.772731, format="%.6f")

# ------------------ HEADER ------------------
st.title("Dashboard Pertanian Cerdas – Kabupaten Sidenreng Rappang")
st.markdown("""
Lokasi: Kabupaten Sidenreng Rapppang – Sulawesi Selatan  
Dikembangkan oleh Dian Eka Putra | Email: ekaputradian01@gmail.com | WA: 085654073752
""")
# ------------------ PETA CURAH HUJAN ------------------
with st.expander("Peta Curah Hujan Real-time"):
    m = folium.Map(location=[LAT, LON], zoom_start=13, control_scale=True)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(
            tiles=tile_url, attr="© OpenWeatherMap",
            name="Curah Hujan", overlay=True, control=True, opacity=0.6
        ).add_to(m)
    folium.Marker([LAT, LON], tooltip="Lokasi Terpilih").add_to(m)
    st_folium(m, width="100%", height=400)

# ------------------ AMBIL DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "hourly=temperature_2m,precipitation,relative_humidity_2m&timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ DATAFRAME HARIAN ------------------
df_harian = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": np.round(data["daily"]["precipitation_sum"], 1),
    "Suhu Maks (°C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (°C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

threshold = st.sidebar.slider("Batas Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df_harian["Rekomendasi Irigasi"] = df_harian["Curah Hujan (mm)"].apply(
    lambda x: "Irigasi Diperlukan" if x < threshold else "Cukup"
)

# ------------------ TAMPILKAN TABEL DATA ------------------
with st.expander("Tabel Data Cuaca Harian"):
    st.dataframe(df_harian, use_container_width=True)

    csv = df_harian.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "data_cuaca_harian.csv", "text/csv")

    excel_io = BytesIO()
    with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
        df_harian.to_excel(writer, index=False, sheet_name="Cuaca Harian")
        workbook = writer.book
        worksheet = writer.sheets["Cuaca Harian"]
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        worksheet.set_column('A:A', 15, date_format)
    excel_io.seek(0)
    st.download_button("Download Excel", data=excel_io.read(), file_name="data_cuaca_harian.xlsx")

    pdf_html = df_harian.to_html(index=False)
    b64 = base64.b64encode(pdf_html.encode("utf-8")).decode("utf-8")
    href = f'<a href="data:text/html;base64,{b64}" download="laporan_cuaca_harian.html">📥 Download Laporan (HTML)</a>'
    st.markdown(href, unsafe_allow_html=True)

# ------------------ DATAFRAME PER JAM ------------------
df_jam = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": data["hourly"]["precipitation"],
    "Suhu (°C)": data["hourly"]["temperature_2m"],
    "Kelembapan (%)": data["hourly"]["relative_humidity_2m"]
})

# ------------------ TAMPILKAN GRAFIK ------------------
with st.expander("Grafik Harian"):
    st.plotly_chart(px.bar(df_harian, x="Tanggal", y="Curah Hujan (mm)", title="Curah Hujan Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Maks (°C)", title="Suhu Maksimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Min (°C)", title="Suhu Minimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Kelembapan (%)", title="Kelembapan Harian"), use_container_width=True)

# ------------------ GRAFIK JAM KE DEPAN ------------------
df_jam_prediksi = df_jam[df_jam["Waktu"] > dt.now()].head(48)
with st.expander("Grafik Per Jam (48 Jam Ke Depan)"):
    if df_jam_prediksi.empty:
        st.warning("Tidak ada data prediksi ke depan tersedia saat ini.")
    else:
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Curah Hujan (mm)", title="Prediksi Curah Hujan per Jam (48 Jam Ke Depan)"), use_container_width=True)
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Suhu (°C)", title="Prediksi Suhu per Jam (48 Jam Ke Depan)"), use_container_width=True)
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Kelembapan (%)", title="Prediksi Kelembapan per Jam (48 Jam Ke Depan)"), use_container_width=True)

# ------------------ MODEL PREDIKSI ------------------
model_df = pd.DataFrame({
    "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
    "Suhu (°C)": [30, 32, 29, 31, 33],
    "Kelembapan (%)": [75, 80, 78, 82, 79],
    "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
})
model = LinearRegression().fit(
    model_df.drop("Hasil Panen (kg/ha)", axis=1), model_df["Hasil Panen (kg/ha)"]
)

# ------------------ PREDIKSI PANEN ------------------
with st.expander("Prediksi Panen"):
    # ---- Prediksi Manual dengan Input Cuaca (Khusus Padi) ----
    st.subheader("Prediksi Panen Khusus Padi (Dengan Input Cuaca)")
    ch_manual_padi = st.number_input("Curah Hujan (mm)", value=5.0, key="manual_padi_ch")
    suhu_manual_padi = st.number_input("Suhu Maks (°C)", value=32.0, key="manual_padi_suhu")
    hum_manual_padi = st.number_input("Kelembapan (%)", value=78.0, key="manual_padi_hum")
    luas_manual_padi = st.number_input("Luas Lahan (ha)", value=1.0, key="manual_padi_luas")
    harga_manual_padi = st.number_input("Harga Padi (Rp/kg)", value=7000, key="manual_padi_harga")
    biaya_manual_padi = st.number_input("Biaya Produksi per Ha (Rp)", value=5000000, key="manual_padi_biaya")

    pred_manual_padi = model.predict([[ch_manual_padi, suhu_manual_padi, hum_manual_padi]])[0]
    total_manual_padi = pred_manual_padi * luas_manual_padi
    pendapatan_manual_padi = total_manual_padi * harga_manual_padi
    laba_bersih_manual_padi = pendapatan_manual_padi - (biaya_manual_padi * luas_manual_padi)

    st.markdown(f"""
    - **Prediksi Hasil Panen Padi (Manual):** {pred_manual_padi:,.0f} kg/ha  
    - **Total Panen:** {total_manual_padi:,.0f} kg  
    - **Pendapatan Kotor:** Rp {pendapatan_manual_padi:,.0f}  
    - **Laba Bersih:** Rp {laba_bersih_manual_padi:,.0f}
    """)

    # ---- Prediksi Manual tanpa Input Cuaca (Untuk Semua Komoditas) ----
    st.subheader("Prediksi Panen Otomatis Komoditas Pertanian Di Kabupaten Sidrap")
    komoditas_list = ["Padi", "Jagung", "Kopi", "Kakao", "Kelapa", "Porang"]
    komoditas_manual = st.selectbox("Pilih Komoditas", komoditas_list, key="manual2_komoditas")
    pred_yield_default = {
        "Padi": 5000,
        "Jagung": 6000,
        "Kopi": 1200,
        "Kakao": 1500,
        "Kelapa": 2000,
        "Porang": 10000
    }
    hasil_per_ha = pred_yield_default.get(komoditas_manual, 5000)
    luas_lahan = st.number_input("Luas Lahan (ha)", value=1.0, key="manual2_luas")
    harga = st.number_input(f"Harga {komoditas_manual} (Rp/kg)", value=7000, key="manual2_harga")
    biaya = st.number_input("Biaya Produksi per Ha (Rp)", value=5000000, key="manual2_biaya")

    total_hasil = hasil_per_ha * luas_lahan
    pendapatan = total_hasil * harga
    laba = pendapatan - (biaya * luas_lahan)

    st.markdown(f"""
    - **Prediksi Hasil Panen {komoditas_manual}:** {hasil_per_ha:,.0f} kg/ha  
    - **Total Panen:** {total_hasil:,.0f} kg  
    - **Pendapatan Kotor:** Rp {pendapatan:,.0f}  
    - **Laba Bersih:** Rp {laba:,.0f}
    """)

    # ---- Prediksi Otomatis Berdasarkan Cuaca Harian (Khusus Padi) ----
    st.subheader("Prediksi Panen Otomatis Khusus Padi")
    luas_auto = st.number_input("Luas Sawah (ha) (otomatis)", value=1.0, key="auto_luas")
    harga_auto = st.number_input("Harga Padi (Rp/kg) (otomatis)", value=7000, key="auto_harga")
    biaya_auto = st.number_input("Biaya Produksi per Ha (Rp) (otomatis)", value=5000000, key="auto_biaya")

    if not df_harian.empty:
        input_auto = df_harian[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
        pred_auto = model.predict(input_auto)[0]
    else:
        pred_auto = 0

    total_auto = pred_auto * luas_auto
    pendapatan_auto = total_auto * harga_auto
    laba_bersih_auto = pendapatan_auto - (biaya_auto * luas_auto)

    st.markdown(f"""
    - **Prediksi Hasil Panen Padi (Otomatis):** {pred_auto:,.0f} kg/ha  
    - **Total Panen:** {total_auto:,.0f} kg  
    - **Pendapatan Kotor:** Rp {pendapatan_auto:,.0f}  
    - **Laba Bersih:** Rp {laba_bersih_auto:,.0f}
    """)

    # ---- Prediksi 3 Kali Panen Tahunan (Khusus Padi) ----
    st.markdown("Proyeksi Panen Tahunan Padi (3 Kali Panen)")
    df_panen1 = df_harian.head(7)
    input_panen1 = df_panen1[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    pred1 = model.predict(input_panen1)[0]

    df_panen2 = df_harian[60:67] if len(df_harian) >= 67 else df_harian.tail(7)
    input_panen2 = df_panen2[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    pred2 = model.predict(input_panen2)[0]

    df_panen3 = df_harian[120:127] if len(df_harian) >= 127 else df_harian.tail(7)
    input_panen3 = df_panen3[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    pred3 = model.predict(input_panen3)[0]

    luas_ha = st.number_input("Luas Lahan (ha) (Tahunan)", value=1.0, key="luas_tahunan")
    harga_rp = st.number_input("Harga Padi (Rp/kg) (Tahunan)", value=7000, key="harga_tahunan")
    biaya_tahunan = st.number_input("Biaya Produksi per Ha (Rp) (Tahunan)", value=5000000, key="biaya_tahunan")

    total1 = pred1 * luas_ha
    total2 = pred2 * luas_ha
    total3 = pred3 * luas_ha
    hasil_total = total1 + total2 + total3
    pendapatan_total = hasil_total * harga_rp
    biaya_total = biaya_tahunan * luas_ha * 3
    laba_bersih_total = pendapatan_total - biaya_total

    st.write("#### Panen 1")
    st.write(f"- Prediksi Hasil: {pred1:,.0f} kg/ha | Total: {total1:,.0f} kg | Rp {total1 * harga_rp:,.0f}")

    st.write("#### Panen 2")
    st.write(f"- Prediksi Hasil: {pred2:,.0f} kg/ha | Total: {total2:,.0f} kg | Rp {total2 * harga_rp:,.0f}")

    st.write("#### Panen 3")
    st.write(f"- Prediksi Hasil: {pred3:,.0f} kg/ha | Total: {total3:,.0f} kg | Rp {total3 * harga_rp:,.0f}")

    st.success(f"🟩 Total Panen Tahunan: {hasil_total:,.0f} kg | Rp {pendapatan_total:,.0f}")
    st.success(f"🟨 Laba Bersih Tahunan: Rp {laba_bersih_total:,.0f}")

faq_pairs = [
    # Padi
    ("mengapa padi saya kuning", "Padi kuning biasanya karena kekurangan nitrogen, kurang air, atau serangan hama."),
    ("cara mengatasi padi kuning", "Berikan pupuk nitrogen, perbaiki irigasi, dan cek hama."),
    ("mengapa padi layu", "Layu dapat disebabkan kekurangan air, penyakit layu bakteri, atau akar rusak."),
    ("hama wereng pada padi", "Wereng menghisap getah tanaman dan bisa merusak padi."),
    ("pengendalian hama wereng", "Gunakan insektisida yang tepat dan varietas tahan hama."),
    ("penyakit bercak daun pada padi", "Biasanya disebabkan jamur, gunakan fungisida."),
    ("penyebab padi kerontang", "Kerontang terjadi akibat kurangnya penyerbukan atau kekurangan hara."),
    ("waktu tanam padi terbaik", "Musim hujan biasanya waktu terbaik untuk tanam padi."),
    ("apa itu padi organik", "Padi yang dibudidayakan tanpa bahan kimia sintetis."),
    ("cara meningkatkan hasil panen padi", "Gunakan benih unggul, pupuk tepat, dan pengendalian hama baik."),

    # Jagung
    ("cara menanam jagung", "Pilih lahan bersih, tanam benih unggul, berikan pupuk dan air cukup."),
    ("penyakit hawar daun jagung", "Penyakit jamur yang menyebabkan daun mengering, kendalikan dengan fungisida."),
    ("hama ulat pada jagung", "Ulat memakan daun jagung, kendalikan dengan insektisida atau musuh alami."),
    ("waktu panen jagung", "Panen ketika biji sudah keras dan kering."),

    # Kedelai
    ("cara budidaya kedelai", "Tanam di lahan gembur, berikan pupuk dan air cukup."),
    ("penyakit karat pada kedelai", "Penyakit jamur menyebabkan bercak oranye pada daun."),
    ("hama penggerek batang kedelai", "Serangga yang merusak batang, kendalikan dengan insektisida."),

    # Irigasi & Curah Hujan
    ("apa itu irigasi", "Pengairan lahan untuk memenuhi kebutuhan air tanaman."),
    ("jenis irigasi", "Irigasi tetes, sprinkler, banjir, dan lainnya."),
    ("curah hujan yang ideal untuk padi", "Sekitar 1000-2000 mm/tahun, tergantung varietas."),
    ("cara mengukur curah hujan", "Gunakan alat penakar hujan."),
    ("irigasi tetes", "Memberikan air langsung ke akar dengan jumlah kecil."),

    # Pupuk & Tanah
    ("jenis pupuk untuk padi", "Urea, SP-36, KCl adalah pupuk utama."),
    ("pupuk organik", "Pupuk alami seperti kompos dan pupuk kandang."),
    ("kapan waktu memupuk padi", "Saat umur 20-30 hari dan menjelang berbunga."),
    ("fungsi pupuk N", "Meningkatkan pertumbuhan daun dan batang."),
    ("fungsi pupuk P", "Meningkatkan perkembangan akar dan pembungaan."),
    ("fungsi pupuk K", "Meningkatkan ketahanan tanaman terhadap penyakit."),

    # Hama & Penyakit Umum
    ("jenis hama padi", "Wereng, penggerek batang, kutu daun, tikus."),
    ("cara mengendalikan hama tikus", "Perangkap dan rodentisida aman."),
    ("penyakit blas pada padi", "Penyakit jamur yang menyebabkan bercak hitam pada daun."),
    ("penyakit hawar daun", "Penyakit jamur yang membuat daun mengering dan mati."),
    ("cara mengatasi penyakit tanaman", "Gunakan fungisida dan sanitasi lahan."),

    # Lingkungan & Pengelolaan Lahan
    ("apa itu pertanian berkelanjutan", "Pertanian yang menjaga keseimbangan lingkungan."),
    ("cara mencegah erosi tanah", "Terasering, mulsa, dan penanaman pohon pelindung."),
    ("apa itu agroforestri", "Sistem campuran pohon dan tanaman pertanian."),
    ("cara menjaga kualitas air irigasi", "Hindari pencemaran dan lakukan filtrasi."),
    ("cara mengatasi kekeringan lahan", "Mulsa, irigasi efisien, dan tanaman tahan kekeringan."),

    # Teknik Budidaya & Praktik Terbaik
    ("cara rotasi tanaman", "Ganti tanaman setiap musim untuk mencegah hama dan menjaga tanah."),
    ("manfaat mulsa", "Menjaga kelembaban tanah dan mencegah gulma."),
    ("cara penyiangan gulma", "Manual atau penggunaan herbisida selektif."),
    ("apa itu penanaman serentak", "Menanam pada waktu yang sama untuk mengendalikan hama."),

    # Cuaca & Prediksi Panen
    ("pengaruh suhu terhadap tanaman", "Suhu mempengaruhi fotosintesis dan metabolisme."),
    ("cara memprediksi hasil panen", "Data cuaca, tanah, dan pengelolaan tanaman."),
    ("apa itu kelembapan tanah", "Jumlah air yang tersedia di tanah."),
    ("cara mengukur kelembapan tanah", "Sensor kelembapan atau metode gravimetri."),
    ("pengaruh curah hujan terhadap panen", "Curah hujan cukup penting untuk pertumbuhan."),

    # Variasi typo dan singkatan umum
    ("padi kuning", "Padi kuning biasanya karena kekurangan hara."),
    ("padi layu", "Padi layu bisa karena kekurangan air atau penyakit."),
    ("irigasi", "Irigasi adalah pengairan lahan."),
    ("curah hujan", "Jumlah air hujan di suatu tempat."),
    ("hama padi", "Hama umum padi termasuk wereng dan tikus."),
    ("pupuk padi", "Pupuk utama padi adalah Urea, SP-36, dan KCl."),
    ("kualitas air", "Air harus bersih untuk irigasi."),
    ("penyakit tanaman", "Gunakan fungisida untuk mengatasi penyakit."),
    ("kelembapan tanah", "Kelembapan tanah penting bagi tanaman."),
    ("pengaruh suhu", "Suhu mempengaruhi metabolisme tanaman."),

    # Tambahan umum lain
    ("apa itu penyerbukan", "Proses perpindahan serbuk sari ke kepala putik."),
    ("cara meningkatkan kesuburan tanah", "Tambahkan pupuk organik dan lakukan rotasi tanaman."),
    ("apa itu pupuk hayati", "Pupuk yang mengandung mikroorganisme bermanfaat."),
    ("cara mengatasi kekeringan", "Gunakan mulsa dan irigasi yang tepat."),
    ("apa itu gulma", "Tanaman pengganggu yang bersaing dengan tanaman utama."),
    ("cara pengendalian gulma", "Penyiangan manual atau herbisida."),
    ("apa itu erosi", "Hilangnya lapisan tanah atas oleh air atau angin."),
    ("cara menjaga kelembaban tanah", "Penggunaan mulsa dan irigasi teratur."),
    ("apa itu rehabilitasi lahan", "Pemulihan lahan yang rusak agar dapat produktif kembali."),
    ("cara memanfaatkan limbah pertanian", "Dijadikan kompos atau bahan bakar biomassa."),
    # Padi lanjut
    ("penyebab daun padi berlubang", "Biasanya karena serangan hama penggerek daun atau ulat."),
    ("cara mengatasi daun padi berlubang", "Semprot insektisida dan gunakan varietas tahan hama."),
    ("padi gagal panen", "Bisa karena kekeringan, serangan hama parah, atau penyakit berat."),
    ("penyakit hawar daun", "Penyakit jamur yang menyebabkan daun mengering dan gugur."),
    ("pengendalian penyakit hawar daun", "Gunakan fungisida dan rotasi tanaman."),
    ("kapan pemupukan padi", "Umumnya pada fase vegetatif dan generatif."),
    ("pupuk susulan padi", "Diberikan saat tanaman mulai berbunga agar hasil optimal."),
    ("penyebab padi keriting", "Kekurangan unsur hara atau serangan hama."),
    ("cara mengatasi padi keriting", "Berikan pupuk daun dan kendalikan hama."),
    ("penyebab padi busuk", "Serangan jamur seperti padi bercak dan jamur batang."),
    ("apa itu padi organik", "Padi yang dibudidayakan tanpa pestisida dan pupuk kimia."),
    ("cara tanam padi organik", "Gunakan pupuk organik, pestisida alami, dan pengelolaan tanah baik."),
    ("berat panen padi per hektar", "Rata-rata 5-7 ton gabah kering tergantung varietas dan pengelolaan."),

    # Jagung lanjut
    ("hama wereng jagung", "Wereng jagung menyerang daun dan batang, menyebabkan layu."),
    ("penyakit busuk batang jagung", "Biasanya disebabkan jamur, kendalikan dengan fungisida."),
    ("pupuk terbaik untuk jagung", "Pupuk NPK dan Urea, sesuai kebutuhan tanah."),
    ("kapan panen jagung", "Setelah 90-110 hari setelah tanam tergantung varietas."),
    ("penyebab jagung gagal panen", "Serangan hama, kekurangan air, atau cuaca ekstrem."),

    # Kedelai lanjut
    ("penyebab daun kedelai keriting", "Infeksi virus atau serangan hama."),
    ("cara mengatasi virus pada kedelai", "Gunakan benih sehat dan kendalikan vektor serangga."),
    ("hama kutu daun kedelai", "Kutu daun menyebabkan daun menguning dan rontok."),
    ("waktu tanam kedelai", "Pada musim kemarau awal dengan pengairan memadai."),

    # Irigasi dan pengairan lanjut
    ("apa itu irigasi tetes", "Metode pengairan yang mengalirkan air langsung ke akar."),
    ("keuntungan irigasi tetes", "Hemat air dan mencegah pemborosan."),
    ("irigasi banjir", "Pengairan lahan dengan cara membanjiri seluruh area."),
    ("kapan irigasi dilakukan", "Saat curah hujan kurang dari kebutuhan tanaman."),
    ("cara cek kelembaban tanah", "Gunakan sensor kelembaban atau metode manual seperti cocol tanah."),
    ("irigasi otomatis", "Pengairan yang dikontrol dengan sistem elektronik sesuai kebutuhan tanaman."),
    ("penyebab irigasi tidak merata", "Saluran tersumbat atau desain sistem yang buruk."),
    ("cara memperbaiki saluran irigasi", "Bersihkan dan perbaiki kerusakan fisik saluran."),

    # Curah hujan dan cuaca lanjut
    ("apa itu kelembapan relatif", "Persentase kadar uap air di udara dibandingkan kapasitas maksimum."),
    ("pengaruh curah hujan rendah", "Tanaman bisa stres kekurangan air dan pertumbuhan terganggu."),
    ("curah hujan tinggi berdampak apa", "Bisa menyebabkan genangan dan penyakit jamur."),
    ("alat ukur suhu", "Termometer."),
    ("alat ukur kelembapan", "Higrometer atau sensor kelembapan."),

    # Pupuk dan tanah lanjut
    ("fungsi pupuk organik", "Meningkatkan kesuburan dan struktur tanah."),
    ("pupuk kimia yang umum", "Urea, SP-36, KCl, NPK."),
    ("apa itu pupuk dasar", "Pupuk yang diberikan sebelum tanam."),
    ("apa itu pupuk susulan", "Pupuk yang diberikan setelah tanaman tumbuh."),
    ("tanda kekurangan nitrogen", "Daun menguning terutama daun tua."),
    ("tanda kekurangan fosfor", "Tanaman tumbuh lambat dan warna daun gelap."),
    ("tanda kekurangan kalium", "Daun menguning di tepi dan mudah rusak."),
    ("pengaruh pH tanah", "pH mempengaruhi ketersediaan hara untuk tanaman."),
    ("cara memperbaiki pH tanah asam", "Tambahkan kapur atau dolomit."),

    # Hama & penyakit lanjut
    ("jenis hama tikus", "Tikus sawah, tikus rumah, tikus ladang."),
    ("cara mengendalikan hama tikus", "Perangkap, rodentisida, dan sanitasi lahan."),
    ("penyakit blas", "Penyakit jamur yang menyebabkan bercak hitam."),
    ("penyakit hawar", "Penyakit jamur yang menyebabkan daun layu."),
    ("penyakit bulai", "Penyakit yang menyebabkan bulir kosong."),
    ("pengendalian penyakit", "Gunakan fungisida dan varietas tahan."),
    ("serangga penghisap getah", "Wereng dan kutu daun."),
    ("serangga penggerek batang", "Penggerek batang merusak jaringan dalam tanaman."),

    # Lingkungan & pengelolaan lahan lanjut
    ("apa itu konservasi tanah", "Upaya mencegah erosi dan degradasi tanah."),
    ("cara konservasi tanah", "Terasering, mulsa, penanaman pohon."),
    ("apa itu agroekologi", "Sistem pertanian yang ramah lingkungan."),
    ("pengelolaan limbah pertanian", "Dijadikan kompos atau biogas."),
    ("pengaruh polusi air irigasi", "Merusak tanaman dan mengurangi hasil panen."),

    # Teknik budidaya & praktik terbaik lanjut
    ("apa itu tanam tumpangsari", "Menanam dua jenis tanaman secara bersamaan."),
    ("manfaat tanam tumpangsari", "Mengoptimalkan lahan dan mengendalikan hama."),
    ("apa itu sistem tanam jajar legowo", "Baris tanaman dibuat lebih renggang untuk sirkulasi udara."),
    ("manfaat sistem legowo", "Meningkatkan hasil dan mengurangi penyakit."),
    ("apa itu pemangkasan", "Mengurangi bagian tanaman untuk memperbaiki pertumbuhan."),

    # Cuaca & prediksi lanjut
    ("apa itu indeks panas tanaman", "Pengukuran stres panas pada tanaman."),
    ("cara memprediksi hasil panen", "Menggunakan data cuaca, tanah, dan pemodelan statistik."),
    ("pengaruh angin kencang", "Merusak tanaman dan mempercepat penguapan air."),
    ("pengaruh kelembapan tinggi", "Meningkatkan risiko penyakit jamur."),

    # Terminologi umum & typo tambahan
    ("padi kuneng", "Padi kuning biasanya karena kekurangan hara."),
    ("padi kering", "Bisa disebabkan kekurangan air atau penyakit."),
    ("penyakit padi", "Penyakit umum padi termasuk blas, hawar, dan bulai."),
    ("cara tanam jagung", "Pilih lahan bersih, berikan pupuk, dan siram cukup."),
    ("hama padi wereng", "Wereng adalah hama yang menghisap getah tanaman."),
    ("pupuk urea", "Pupuk nitrogen untuk pertumbuhan vegetatif."),
    ("pupuk sp36", "Pupuk fosfor untuk perkembangan akar."),
    ("kapan panen padi", "Biasanya 3-4 bulan setelah tanam."),
    ("kapan panen jagung", "Setelah 3-4 bulan sesuai varietas."),

    # Tips dan trik
    ("tips menanam padi", "Gunakan benih unggul, jaga irigasi dan kendalikan hama."),
    ("tips irigasi hemat", "Gunakan sistem irigasi tetes atau jadwal irigasi tepat."),
    ("cara menghindari gulma", "Penyiangan rutin dan mulsa."),
    ("cara meningkatkan hasil panen", "Pengelolaan tanah baik, pupuk tepat, dan kendali hama."),
    ("cara mendeteksi penyakit tanaman", "Perhatikan gejala seperti perubahan warna dan tekstur daun."),

    # Tanya umum terkait pertanian
    ("apa itu pertanian modern", "Pertanian yang menggunakan teknologi dan ilmu pengetahuan terkini."),
    ("apa itu smart farming", "Pertanian dengan otomatisasi dan sensor canggih."),
    ("apa itu drone pertanian", "Drone yang digunakan untuk pemantauan dan penyemprotan."),
    ("apa itu hidroponik", "Budidaya tanaman tanpa tanah menggunakan larutan nutrisi."),
    ("apa itu aquaponik", "Sistem gabungan budidaya ikan dan tanaman."),

    # Pertanyaan seputar lingkungan
    ("bagaimana menjaga lingkungan pertanian", "Kurangi penggunaan pestisida, gunakan pupuk organik, dan konservasi air."),
    ("apa itu deforestasi", "Penggundulan hutan yang berdampak buruk pada ekosistem."),
    ("bagaimana perubahan iklim mempengaruhi pertanian", "Cuaca ekstrem dan pola hujan yang tidak menentu dapat merusak tanaman."),

    # Pertanyaan soal peralatan
    ("alat untuk mengukur pH tanah", "pH meter atau kertas lakmus."),
    ("alat pengukur curah hujan", "Penakar hujan."),
    ("alat pengukur kelembapan tanah", "Sensor kelembapan atau tensiometer."),

    # Pertanyaan seputar hasil panen dan pasar
    ("bagaimana menentukan harga gabah", "Bergantung kualitas, pasokan, dan permintaan pasar."),
    ("apa itu gabah kering", "Gabah yang sudah dikeringkan untuk penyimpanan."),

    # Tambahan typo dan variasi bahasa gaul
    ("padi kuneng", "Padi kuning biasanya karena kekurangan hara."),
    ("padi kering banget", "Mungkin tanaman kurang air atau terkena penyakit."),
    ("padi rusak", "Periksa hama dan penyakit serta kondisi air."),
    ("tanem padi gimana", "Gunakan benih bagus, siram teratur, dan pupuk tepat."),
    ("jagung ga tumbuh", "Cek kualitas benih dan kondisi tanah serta air."),
    ("pupuk kurang", "Tanaman akan terlihat layu dan kuning."),
    ("kenapa saya sayang aripa", "Karena aripaku sayang diannnnnnn."),
]

def cari_jawaban(pertanyaan, faq_list, threshold=70):
    pertanyaan = pertanyaan.lower()
    pertanyaan = pertanyaan.strip()
    # Cari pertanyaan paling mirip
    hasil = process.extractOne(pertanyaan, [q for q, _ in faq_list], scorer=fuzz.token_set_ratio)
    if hasil and hasil[1] >= threshold:
        for q, a in faq_list:
            if q == hasil[0]:
                return a
    return "Maaf, saya belum punya jawaban untuk pertanyaan itu. Silakan tanyakan hal lain."

# -------------------- Streamlit Chatbot Interface -------------------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Chatbot FAQ Pertanian")

user_input = st.text_input("Tanyakan apa saja tentang pertanian, irigasi, cuaca, hama, dan lingkungan:")

if user_input:
    st.session_state.chat_history.append(("🧑", user_input))
    jawaban = cari_jawaban(user_input, faq_pairs)
    st.session_state.chat_history.append(("🤖", jawaban))

for role, msg in st.session_state.chat_history:
    if role == "🧑":
        st.markdown(f"**{role}**: {msg}")
    else:
        st.markdown(f"**{role}**: {msg}")
        
# ------------------ KALKULATOR PEMUPUKAN ------------------
with st.expander("Kalkulator Pemupukan"):
    tanaman = st.selectbox("Pilih Komoditas", ["Padi", "Jagung", "Kedelai", "Kopi", "Kakao", "Kelapa", "Porang"], key="komoditas_pupuk")
    luas_lahan = st.number_input("Luas Lahan (ha)", value=1.0, min_value=0.01, step=0.1, key="luas_pupuk")

    rekomendasi_pupuk = {
        "Padi": {
            "Urea": {"dosis": 250, "fungsi": "Merangsang pertumbuhan daun dan batang"},
            "SP-36": {"dosis": 100, "fungsi": "Membentuk akar dan anakan, serta meningkatkan hasil malai"},
            "KCl": {"dosis": 100, "fungsi": "Meningkatkan ketahanan terhadap hama/penyakit dan kualitas gabah"},
        },
        "Jagung": {
            "Urea": {"dosis": 300, "fungsi": "Mendorong pertumbuhan vegetatif (daun dan batang)"},
            "SP-36": {"dosis": 150, "fungsi": "Meningkatkan perkembangan akar dan pembentukan tongkol"},
            "KCl": {"dosis": 100, "fungsi": "Meningkatkan pengisian biji dan ketahanan tanaman"},
        },
        "Kedelai": {
            "Urea": {"dosis": 100, "fungsi": "Dosis rendah karena kedelai bisa fiksasi nitrogen sendiri"},
            "SP-36": {"dosis": 100, "fungsi": "Mendukung pembentukan bunga dan polong"},
            "KCl": {"dosis": 75, "fungsi": "Meningkatkan kualitas dan daya simpan hasil panen"},
        },
        "Kopi": {
            "NPK": {"dosis": 500, "fungsi": "Meningkatkan pertumbuhan dan produksi buah kopi"}
        },
        "Kakao": {
            "Urea": {"dosis": 150, "fungsi": "Meningkatkan pertumbuhan daun dan buah kakao"},
            "TSP": {"dosis": 100, "fungsi": "Meningkatkan pembentukan bunga dan buah"},
            "KCl": {"dosis": 150, "fungsi": "Meningkatkan rasa dan mutu biji kakao"}
        },
        "Kelapa": {
            "NPK": {"dosis": 300, "fungsi": "Memperbaiki pertumbuhan dan produktivitas kelapa"}
        },
        "Porang": {
            "Urea": {"dosis": 200, "fungsi": "Meningkatkan pertumbuhan daun dan umbi porang"},
            "KCl": {"dosis": 100, "fungsi": "Meningkatkan pembentukan dan bobot umbi"}
        }
    }

    data_pupuk = []
    for jenis_pupuk, data in rekomendasi_pupuk.get(tanaman, {}).items():
        total_dosis = data["dosis"] * luas_lahan
        data_pupuk.append({
            "Jenis": jenis_pupuk,
            "Total (kg)": round(total_dosis, 2),
            "Fungsi": data["fungsi"]
        })

    df_pupuk = pd.DataFrame(data_pupuk)

    if not df_pupuk.empty:
        st.markdown("### Rekomendasi Pemupukan")
        st.markdown(df_pupuk.to_html(classes='styled-table', index=False), unsafe_allow_html=True)
    else:
        st.write("Data pupuk belum tersedia untuk tanaman ini.")
    
# ------------------ Harga Komoditas ------------------

HARGA_FILE = "data/harga_komoditas.json"

# Buat folder jika belum ada
if not os.path.exists("data"):
    os.makedirs("data")

# Fungsi untuk load & simpan harga
def load_harga_komoditas():
    if os.path.exists(HARGA_FILE):
        with open(HARGA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    # Default komoditas khas Sidrap
    return [
        {"Komoditas": "Padi", "Harga (Rp/kg)": 7000},
        {"Komoditas": "Jagung", "Harga (Rp/kg)": 5300},
        {"Komoditas": "Kopi", "Harga (Rp/kg)": 8500},
        {"Komoditas": "Kakao", "Harga (Rp/kg)": 12000},
        {"Komoditas": "Kelapa", "Harga (Rp/kg)": 2500},
        {"Komoditas": "Porang", "Harga (Rp/kg)": 10000}
    ]

def save_harga_komoditas(data):
    with open(HARGA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Load harga ke session_state
if "harga_komoditas" not in st.session_state:
    st.session_state.harga_komoditas = load_harga_komoditas()

# UI Harga Komoditas
with st.expander("Harga Komoditas di Sidrap"):
    st.markdown("Silakan ubah harga langsung di tabel berikut:")

    # Ambil data
    df_edit = pd.DataFrame(st.session_state.harga_komoditas)

    # Rename kolom ke bentuk lebih pendek dan mobile-friendly
    df_edit = df_edit.rename(columns={"Harga (Rp/kg)": "Harga"})

    # Tampilkan tabel editor
    edited_df = st.data_editor(
        df_edit,
        column_config={
            "Komoditas": st.column_config.TextColumn("Komoditas"),
            "Harga": st.column_config.NumberColumn("Harga (Rp/kg)", format="Rp. %d"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_harga"
    )

    if st.button("Simpan Perubahan Harga"):
        # Kembalikan nama kolom ke format aslinya untuk penyimpanan
        edited_df = edited_df.rename(columns={"Harga": "Harga (Rp/kg)"})
        st.session_state.harga_komoditas = edited_df.to_dict(orient="records")
        save_harga_komoditas(st.session_state.harga_komoditas)
        st.success("✅ Harga komoditas berhasil diperbarui.")

# ------------------ LAPORAN WARGA ------------------
# Pastikan folder upload ada
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "laporan" not in st.session_state:
    st.session_state.laporan = load_data(LAPORAN_FILE)

if "laporan_update" not in st.session_state:
    st.session_state.laporan_update = False

with st.expander("Laporan Warga"):
    with st.form("form_laporan"):
        nama = st.text_input("Nama")
        kontak = st.text_input("Kontak")
        jenis = st.selectbox("Jenis", ["Masalah Irigasi", "Gangguan Hama", "Kondisi Cuaca", "Lainnya"])
        lokasi = st.text_input("Lokasi")
        isi = st.text_area("Deskripsi")
        gambar = st.file_uploader("Upload Gambar (opsional)", type=["png", "jpg", "jpeg"])
        kirim = st.form_submit_button("Kirim")

        if kirim:
            if nama.strip() and kontak.strip() and isi.strip():
                path_gambar = None
                if gambar is not None:
                    # Simpan gambar ke folder upload dengan nama unik
                    ext = os.path.splitext(gambar.name)[1]
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(gambar.getbuffer())
                    path_gambar = filepath

                new_laporan = {
                    "Nama": nama.strip(),
                    "Kontak": kontak.strip(),
                    "Jenis": jenis,
                    "Lokasi": lokasi.strip(),
                    "Deskripsi": isi.strip(),
                    "Tanggal": datetime.now(pytz.timezone("Asia/Makassar")).strftime("%d %B %Y %H:%M"),
                    "Gambar": path_gambar,
                }
                st.session_state.laporan.append(new_laporan)
                save_data(LAPORAN_FILE, st.session_state.laporan)
                st.session_state.laporan_update = True
                st.success("Laporan berhasil dikirim.")
            else:
                st.warning("Lengkapi semua isian sebelum mengirim laporan.")

    # Tampilkan laporan warga
    for i, lap in enumerate(st.session_state.laporan):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown(
                f"**{lap['Tanggal']}**  \n"
                f"*{lap['Jenis']}* oleh **{lap['Nama']}**  \n"
                f"{lap['Lokasi']}  \n"
                f"{lap['Deskripsi']}"
            )
            if lap.get("Gambar"):
                try:
                    img = Image.open(lap["Gambar"])
                    st.image(img, width=300)
                except Exception as e:
                    st.warning("Gambar tidak dapat ditampilkan.")
        with col2:
            if st.button("🗑️ Hapus", key=f"del_lap_{i}"):
                # Hapus file gambar jika ada
                if lap.get("Gambar") and os.path.exists(lap["Gambar"]):
                    os.remove(lap["Gambar"])
                st.session_state.laporan.pop(i)
                save_data(LAPORAN_FILE, st.session_state.laporan)
                st.session_state.laporan_update = True
                st.experimental_rerun()


# ------------------ PENGINGAT HARIAN ------------------
TODO_FILE = "todo_harian.json"

def load_todo():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_todo(data):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "todo" not in st.session_state:
    st.session_state.todo = load_todo()

with st.expander("Pengingat Harian"):
    tugas_baru = st.text_input("Tambah Tugas Baru:")
    if st.button("✅ Simpan Tugas Baru"):
        if tugas_baru.strip():
            st.session_state.todo.append(tugas_baru.strip())
            save_todo(st.session_state.todo)
            st.success("Tugas berhasil disimpan.")
        else:
            st.warning("⚠️ Tugas tidak boleh kosong.")

    # Tampilkan daftar tugas dengan tombol hapus
    for i, tugas in enumerate(st.session_state.todo):
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"- {tugas}")
        if col2.button("🗑️", key=f"hapus_tugas_{i}"):
            st.session_state.todo.pop(i)
            save_todo(st.session_state.todo)
            st.experimental_rerun()
# Footer
st.markdown("---")
st.caption("© 2025 – Kabupaten Sidenreng Rappang | Dashboard Pertanian Digital by Dian Eka Putra")
