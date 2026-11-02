import base64
import math
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from supabase import create_client

st.set_page_config(page_title="SiParkir UM", page_icon="🅿️", layout="wide")

REFRESH = 5  # detik
WIB = timezone(timedelta(hours=7))
PUSAT = [-7.9604, 112.6183]
HARI = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]
FOLDER = Path(__file__).parent / "gambar"
KODE = {"parkir-k": "K", "fmipa-pipa": "F1", "fmipa-gracak": "F2", "gkb-a20": "A20",
        "gkb-a19": "A19", "gkb-depan": "GD", "masjid": "M", "uji-1": "UJ"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Dancing+Script:wght@600&display=swap');
.sp, .sp *, .stButton button {font-family: 'Poppins', sans-serif;}
.stApp {background: linear-gradient(180deg, #eaf2ff 0%, #f8fbff 45%, #ffffff 100%);}
.block-container {max-width: 1180px; padding-top: 1.2rem; padding-bottom: 3rem;}
header[data-testid="stHeader"] {background: transparent;}
footer {visibility: hidden;}

.brand {display: flex; align-items: center; gap: 14px; padding-top: 4px;}
.brand img {height: 44px; width: auto;}
.logo-ph {height: 44px; min-width: 44px; padding: 0 10px; border-radius: 10px; background: #dbeafe;
  color: #1d4ed8; font-weight: 800; display: flex; align-items: center; justify-content: center;}
.brand-sep {width: 1px; height: 40px; background: #cbd5e1;}
.brand-name {font-size: 1.7rem; font-weight: 800; color: #0b2a6f;}
.motto {text-align: right; font-style: italic; color: #1d4ed8; font-weight: 600; padding-top: 12px;}

div[data-testid="stButtonGroup"] button {border-radius: 999px; font-weight: 600; border: none;
  background: transparent; color: #1e293b;}
button[data-testid="stBaseButton-pillsActive"] {background: #0b2a6f !important; color: #ffffff !important;}

.hero-text h1 {font-size: 2.7rem; line-height: 1.15; font-weight: 800; color: #0b2a6f; margin: 0.6rem 0 0.8rem;}
.hero-text .hl {color: #1d4ed8;}
.hero-text p {color: #334155; font-size: 1.02rem; max-width: 520px;}
.hero-img {position: relative; height: 320px; border-radius: 24px; overflow: hidden;
  background: linear-gradient(135deg, #bfdbfe, #e0f2fe);}
.hero-img img {width: 100%; height: 100%; object-fit: cover;
  -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 28%);
  mask-image: linear-gradient(to right, transparent 0%, #000 28%);}
.hero-ph {display: flex; align-items: center; justify-content: center; height: 100%; color: #1e40af;
  font-weight: 600; text-align: center; padding: 20px;}
.salam {position: absolute; top: 14px; right: 24px; font-family: 'Dancing Script', cursive !important;
  font-size: 2rem; color: #1d4ed8; transform: rotate(-6deg);}

.st-key-cta button {background: #0b2a6f; color: #ffffff; border: none; border-radius: 999px;
  padding: 0.6rem 1.6rem; font-weight: 600;}
.st-key-cta button:hover {background: #1d4ed8; color: #ffffff;}
.st-key-panduan button {background: #ffffff; color: #0b2a6f; border: 1.5px solid #0b2a6f;
  border-radius: 999px; font-weight: 600;}

.stats {display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 10px 0 22px;}
.card {background: #ffffff; border-radius: 22px; box-shadow: 0 8px 28px rgba(30, 64, 175, 0.10);
  padding: 18px 24px; display: flex; align-items: center; gap: 18px;}
.ico {width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 1.8rem; flex-shrink: 0;}
.ico.blue {background: #dbeafe;} .ico.green {background: #d9f2e3;} .ico.amber {background: #fdf0cf;}
.lbl {color: #475569; font-size: 0.9rem; font-weight: 500;}
.val {color: #0b2a6f; font-size: 1.55rem; font-weight: 700;}

.panel {background: #ffffff; border-radius: 22px; box-shadow: 0 8px 28px rgba(30, 64, 175, 0.10);
  overflow: hidden; border: 1px solid #e2e8f0; margin-bottom: 12px;}
.panel-head {background: #0b2a6f; color: #ffffff; padding: 14px 22px; display: flex;
  align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem;}
.panel-head .live {margin-left: auto; background: rgba(255, 255, 255, 0.15); border-radius: 999px;
  padding: 4px 12px; font-size: 0.8rem; font-weight: 500;}
.panel-head .dot {color: #4ade80;}
.row {display: flex; align-items: center; gap: 14px; padding: 12px 20px; border-bottom: 1px solid #e8eef7;}
.row:last-child {border-bottom: none;}
.thumb {width: 86px; height: 56px; border-radius: 10px; object-fit: cover; background: #dbeafe;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 1.4rem;}
.kode {min-width: 44px; height: 44px; border-radius: 12px; background: #dbeafe; color: #1d4ed8;
  font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0;}
.info {flex: 1; min-width: 0;}
.info .nama {color: #0b2a6f; font-weight: 700;}
.info .sub {color: #64748b; font-size: 0.82rem;}
.pill {border-radius: 999px; padding: 6px 16px; font-size: 0.82rem; font-weight: 600; white-space: nowrap;}
.pill.tersedia {background: #e3f6ea; color: #16a34a;}
.pill.sebagian {background: #e0ebff; color: #1d4ed8;}
.pill.hampir {background: #fff0d9; color: #d97706;}
.pill.penuh {background: #fde4e4; color: #dc2626;}
.pill.tutup {background: #eceff3; color: #6b7280;}
.chev {color: #475569; font-size: 1.3rem;}

.tips {background: linear-gradient(160deg, #e6f0ff, #f3f8ff); border-radius: 22px; padding: 22px;
  border: 1px solid #dbe7fb; margin-bottom: 10px;}
.tips h3 {color: #0b2a6f; font-weight: 700; font-size: 1.15rem; margin: 0 0 8px;}
.tips p {color: #334155; font-size: 0.92rem; margin: 0;}
.infobar {background: #e8f0ff; border-radius: 14px; padding: 12px 18px; color: #334155;
  font-size: 0.88rem; margin-top: 14px;}
.langkah {display: flex; gap: 16px; align-items: flex-start; background: #ffffff; border-radius: 18px;
  padding: 16px 20px; box-shadow: 0 6px 20px rgba(30, 64, 175, 0.08); margin-bottom: 12px;}
.langkah .no {width: 38px; height: 38px; border-radius: 50%; background: #0b2a6f; color: #ffffff;
  font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0;}
.langkah .jud {color: #0b2a6f; font-weight: 700;}
.langkah .isi {color: #475569; font-size: 0.92rem;}
.judul-hal {color: #0b2a6f; font-weight: 800; font-size: 1.8rem; margin: 6px 0 12px;}

@media (max-width: 768px) {
  .stats {grid-template-columns: 1fr;}
  .hero-text h1 {font-size: 2rem;}
  .thumb {display: none;}
  .motto {text-align: left;}
}
</style>
"""


@st.cache_resource
def klien():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data
def gambar(nama):
    for ekst, mime in (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp")):
        p = FOLDER / f"{nama}.{ekst}"
        if p.exists():
            return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None


def tampil_html(teks):
    st.markdown("".join(b.strip() for b in teks.strip().splitlines()), unsafe_allow_html=True)


def hari_ini():
    return HARI[datetime.now(WIB).weekday()]


def tutup_hari_ini(a):
    daftar = [h.strip().lower() for h in (a.get("tutup_hari") or "").split(",") if h.strip()]
    return hari_ini() in daftar


def status(a):
    terisi = 100 * (a["kapasitas"] - a["kosong"]) / a["kapasitas"]
    if tutup_hari_ini(a):
        return "Tutup hari ini", "tutup", "gray", terisi
    if a["kosong"] == 0:
        return "Penuh", "penuh", "red", terisi
    if terisi >= 85:
        return "Hampir Penuh", "hampir", "orange", terisi
    if terisi >= 50:
        return "Terisi Sebagian", "sebagian", "lightblue", terisi
    return "Tersedia", "tersedia", "green", terisi


def jam(teks):
    return datetime.fromisoformat(teks).astimezone(WIB).strftime("%H:%M")


def waktu_lengkap(teks):
    dt = datetime.fromisoformat(teks).astimezone(WIB)
    if dt.date() == datetime.now(WIB).date():
        return f"Hari ini, {dt:%H:%M}"
    return f"{dt:%d/%m, %H:%M}"


def jarak_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def fmt_jarak(m):
    return f"{m:.0f} m" if m < 1000 else f"{m / 1000:.1f} km"


def baca():
    try:
        area = klien().table("deteksi_area").select("*").execute().data
        log = klien().table("deteksi_log").select("*").order("id", desc=True).limit(20).execute().data
    except Exception:
        st.error("Gagal membaca database. Cek Secrets dan tabel di Supabase.")
        return None, None
    pos = st.session_state.get("pos")
    for a in area:
        if pos and a.get("lat") is not None and a.get("lon") is not None:
            a["jarak"] = jarak_m(pos[0], pos[1], a["lat"], a["lon"])
    if pos:
        area.sort(key=lambda a: a.get("jarak", float("inf")))
    else:
        area.sort(key=lambda a: a["nama"])
    return area, log


def ke_halaman(nama):
    st.session_state["menu"] = nama


def banner_tutup(area):
    tutup = [a["nama"] for a in area if tutup_hari_ini(a)]
    if tutup:
        buka = [a["nama"] for a in area if not tutup_hari_ini(a)]
        st.warning(f"Hari ini ({hari_ini().capitalize()}) parkiran tutup: {', '.join(tutup)}. "
                   f"Yang buka: {', '.join(buka)}.")


def header():
        um = gambar("logo_um")
    logo_um = f"<img src='{um}'>" if um else "<div class='logo-ph'>UM</div>"
    logo_sp = "<div class='logo-ph'>🚗</div>"
    kiri, tengah, kanan = st.columns([1.5, 1.6, 1.1])
    with kiri:
        tampil_html(f"""
        <div class='sp brand'>{logo_um}<div class='brand-sep'></div>{logo_sp}
        <span class='brand-name'>SiParkir</span></div>
        """)
    with tengah:
        st.pills("Menu", ["Beranda", "Area Parkir", "Panduan"], key="menu", label_visibility="collapsed")
    with kanan:
        tampil_html("<div class='sp motto'>Memayu Hayuning Bawana</div>")


@st.fragment(run_every=REFRESH)
def stat_cards():
    area, _ = baca()
    if area is None:
        return
    buka = [a for a in area if not tutup_hari_ini(a)]
    total = sum(a["kosong"] for a in buka)
    terakhir = waktu_lengkap(max(area, key=lambda a: datetime.fromisoformat(a["diperbarui"]))["diperbarui"])
    tampil_html(f"""
    <div class='sp stats'>
    <div class='card'><div class='ico blue'>🚗</div><div><div class='lbl'>Area Parkir</div>
    <div class='val'>{len(area)} Lokasi</div></div></div>
    <div class='card'><div class='ico green'>🅿️</div><div><div class='lbl'>Slot Tersedia</div>
    <div class='val'>{total} Slot</div></div></div>
    <div class='card'><div class='ico amber'>🕒</div><div><div class='lbl'>Pembaruan Terakhir</div>
    <div class='val'>{terakhir}</div></div></div>
    </div>
    """)


@st.fragment(run_every=REFRESH)
def daftar_terdekat():
    area, _ = baca()
    if area is None:
        return
    pos = st.session_state.get("pos")
    banner_tutup(area)
    baris = []
    for a in area:
        s, kelas, _, terisi = status(a)
        kode = escape(KODE.get(a["id"], a["nama"][:1].upper()))
        if tutup_hari_ini(a):
            sub = f"Tutup hari ini · diperbarui {jam(a['diperbarui'])}"
        else:
            jarak = f"{fmt_jarak(a['jarak'])} dari kamu · " if "jarak" in a else ""
            sub = f"📍 {jarak}{a['kosong']}/{a['kapasitas']} slot kosong ({terisi:.0f}% terisi)"
        baris.append(
            f"<div class='row'><div class='kode'>{kode}</div>"
            f"<div class='info'><div class='nama'>{escape(a['nama'])}</div><div class='sub'>{sub}</div></div>"
            f"<span class='pill {kelas}'>● {s}</span><span class='chev'>›</span></div>"
        )
    judul = "Area Parkir Terdekat" if pos else "Area Parkir"
    tampil_html(
        f"<div class='sp panel'><div class='panel-head'>📍 {judul}"
        f"<span class='live'><span class='dot'>●</span> Live Update</span></div>{''.join(baris)}</div>"
    )
    if not pos:
        st.caption("Aktifkan lokasi (tombol di bagian atas) untuk mengurutkan dari yang terdekat.")


@st.fragment(run_every=REFRESH)
def peta():
    area, _ = baca()
    if area is None:
        return
    pos = st.session_state.get("pos")
    banner_tutup(area)

    if pos:
        dekat = [a for a in area if a["kosong"] > 0 and not tutup_hari_ini(a) and "jarak" in a][:3]
        st.markdown("**Rekomendasi parkir terdekat**")
        if not dekat:
            st.write("Tidak ada area yang buka dan masih punya slot kosong.")
        for a in dekat:
            st.write(f"📍 **{a['nama']}** · {fmt_jarak(a['jarak'])} · {a['kosong']} slot kosong")
    else:
        st.info("Aktifkan lokasi (tombol di bagian atas) untuk melihat rekomendasi dan jarak.")

    m = folium.Map(location=PUSAT, zoom_start=17)
    for a in area:
        if a.get("lat") is None or a.get("lon") is None:
            continue
        s, _, warna, _ = status(a)
        deteksi = a.get("sumber") == "deteksi"
        jarak = f"<br>{fmt_jarak(a['jarak'])} dari kamu" if "jarak" in a else ""
        isi = (f"<b>{escape(a['nama'])}</b><br>{a['kosong']}/{a['kapasitas']} slot kosong"
               f"<br>{s}{jarak}<br>{'Deteksi otomatis' if deteksi else 'Data contoh'}")
        ikon = folium.Icon(color=warna, icon="video-camera", prefix="fa") if deteksi else folium.Icon(color=warna)
        folium.Marker([a["lat"], a["lon"]], tooltip=a["nama"],
                      popup=folium.Popup(isi, max_width=250), icon=ikon).add_to(m)
    if pos:
        folium.Marker(list(pos), tooltip="Lokasi kamu",
                      icon=folium.Icon(color="darkblue", icon="user", prefix="fa")).add_to(m)
    st_folium(m, height=450, use_container_width=True, returned_objects=[], key="peta")
    st.caption("🟢 Tersedia · 🔵 Terisi sebagian · 🟠 Hampir penuh · 🔴 Penuh · ⚫ Tutup hari ini.")


@st.fragment(run_every=REFRESH)
def riwayat():
    _, log = baca()
    if log is None:
        return
    st.caption("Dari area yang dihitung otomatis dari kamera.")
    if not log:
        st.info("Belum ada kendaraan terdeteksi.")
    else:
        baris = [{"Waktu": datetime.fromisoformat(l["waktu"]).astimezone(WIB).strftime("%d/%m %H:%M:%S"),
                  "Kejadian": "Motor masuk" if l["arah"] == "masuk" else "Motor keluar",
                  "Slot kosong": l["kosong_setelah"]} for l in log]
        st.dataframe(baris, hide_index=True, width="stretch")


def halaman_beranda():
    kiri, kanan = st.columns([1.05, 1])
    with kiri:
        tampil_html("""
        <div class='sp hero-text'>
        <h1>Temukan Area Parkir<br>dengan <span class='hl'>Lebih Mudah</span></h1>
        <p>SiParkir hadir untuk membantu sivitas akademika UM mencari ketersediaan parkir secara cepat dan real-time.</p>
        </div>
        """)
        st.button("🔍  Cek Ketersediaan Sekarang  →", key="cta", on_click=ke_halaman, args=("Area Parkir",))
    with kanan:
        foto = gambar("gedung_um")
        isi = f"<img src='{foto}'>" if foto else "<div class='hero-ph'>Taruh foto gedung UM di gambar/gedung_um.jpg</div>"
        tampil_html(f"<div class='sp hero-img'>{isi}<div class='salam'>Salam Cakrawala</div></div>")

    stat_cards()

    kol1, kol2 = st.columns([2.1, 1])
    with kol1:
        daftar_terdekat()
    with kol2:
        tampil_html("""
        <div class='sp tips'><h3>💡 Tips Penggunaan</h3>
        <p>Gunakan SiParkir untuk menemukan parkir terdekat dari lokasi Anda.</p></div>
        """)
        st.button("Lihat Panduan  →", key="panduan", on_click=ke_halaman, args=("Panduan",))
    tampil_html("<div class='sp infobar'>ⓘ Informasi ketersediaan parkir diperbarui secara berkala untuk kenyamanan Anda.</div>")


def halaman_area():
    tampil_html("<div class='sp judul-hal'>Area Parkir</div>")
    peta()
    st.markdown("&nbsp;")
    daftar_terdekat()
    with st.expander("Riwayat deteksi terbaru"):
        riwayat()


def halaman_panduan():
    tampil_html("<div class='sp judul-hal'>Panduan Penggunaan</div>")
    langkah = [
        ("Aktifkan lokasi", "Tekan tombol lokasi di bagian atas halaman, lalu pilih Izinkan saat browser meminta akses. Tanpa lokasi, jarak dan rekomendasi tidak tampil."),
        ("Lihat slot di Beranda", "Beranda menampilkan jumlah slot tersedia dan daftar area parkir beserta statusnya. Data diperbarui otomatis."),
        ("Cek peta dan rekomendasi", "Buka Area Parkir untuk melihat peta, marker berwarna sesuai status, dan tiga rekomendasi parkir terdekat."),
        ("Pahami status warna", "Hijau: Tersedia. Biru: Terisi Sebagian. Oranye: Hampir Penuh. Merah: Penuh. Abu-abu: Tutup hari ini."),
        ("Perhatikan peringatan tutup", "Jika ada parkiran yang tutup pada hari tertentu (misalnya Jumat), peringatan muncul beserta area yang masih buka."),
        ("Lihat riwayat deteksi", "Di halaman Area Parkir, buka Riwayat deteksi terbaru untuk melihat motor masuk dan keluar yang terhitung kamera."),
    ]
    for i, (jud, isi) in enumerate(langkah, 1):
        tampil_html(f"<div class='sp langkah'><div class='no'>{i}</div>"
                    f"<div><div class='jud'>{jud}</div><div class='isi'>{isi}</div></div></div>")


st.markdown(CSS, unsafe_allow_html=True)
st.session_state.setdefault("menu", "Beranda")
header()

kol_gps, kol_info = st.columns([1, 5])
with kol_gps:
    lok = streamlit_geolocation()
if lok and lok.get("latitude") is not None and lok.get("longitude") is not None:
    st.session_state["pos"] = (lok["latitude"], lok["longitude"])
with kol_info:
    st.caption("✅ Lokasi aktif" if st.session_state.get("pos")
               else "📍 Tekan tombol di samping, lalu izinkan akses lokasi di browser.")

halaman = st.session_state.get("menu") or "Beranda"
if halaman == "Beranda":
    halaman_beranda()
elif halaman == "Area Parkir":
    halaman_area()
else:
    halaman_panduan()
