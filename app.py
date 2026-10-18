import math
from datetime import datetime, timedelta, timezone
import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from supabase import create_client

st.set_page_config(page_title="SiParkir Deteksi", page_icon="📹")

REFRESH = 5  # detik
WIB = timezone(timedelta(hours=7))
PUSAT = [-7.9604, 112.6183]


@st.cache_resource
def klien():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def status(kosong, kapasitas):
    terisi = 100 * (kapasitas - kosong) / kapasitas
    if kosong == 0:
        return "Penuh", "🔴", "red", terisi
    if terisi >= 85:
        return "Hampir Penuh", "🟠", "orange", terisi
    return "Tersedia", "🟢", "green", terisi


def ke_wib(teks):
    return datetime.fromisoformat(teks).astimezone(WIB).strftime("%d/%m %H:%M:%S")


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


@st.fragment(run_every=REFRESH)
def beranda():
    area, _ = baca()
    if area is None:
        return
    pos = st.session_state.get("pos")
    st.subheader("Area parkir terdekat" if pos else "Area parkir")
    if not pos:
        st.info("Aktifkan lokasi (tombol di atas) untuk mengurutkan dari yang terdekat.")
    for a in area:
        s, ikon, _, terisi = status(a["kosong"], a["kapasitas"])
        jarak = f" · {fmt_jarak(a['jarak'])} dari kamu" if "jarak" in a else ""
        sumber = "📹 Deteksi otomatis" if a.get("sumber") == "deteksi" else "Data contoh"
        with st.container(border=True):
            st.markdown(f"**{a['nama']}**{jarak}  \n{sumber} · diperbarui {ke_wib(a['diperbarui'])}")
            st.markdown(f"{ikon} {s}: **{a['kosong']}** dari {a['kapasitas']} slot kosong ({terisi:.0f}% terisi)")
            st.progress(min(max(terisi / 100, 0), 1))


@st.fragment(run_every=REFRESH)
def peta():
    area, _ = baca()
    if area is None:
        return
    pos = st.session_state.get("pos")

    if pos:
        dekat = [a for a in area if a["kosong"] > 0 and "jarak" in a][:3]
        st.markdown("**Rekomendasi parkir terdekat**")
        if not dekat:
            st.write("Semua titik sedang penuh.")
        for a in dekat:
            st.write(f"📍 **{a['nama']}** · {fmt_jarak(a['jarak'])} · {a['kosong']} slot kosong")
    else:
        st.info("Aktifkan lokasi (tombol di atas) untuk melihat rekomendasi dan jarak.")

    m = folium.Map(location=PUSAT, zoom_start=17)
    for a in area:
        if a.get("lat") is None or a.get("lon") is None:
            continue
        s, _, warna, _ = status(a["kosong"], a["kapasitas"])
        deteksi = a.get("sumber") == "deteksi"
        jarak = f"<br>{fmt_jarak(a['jarak'])} dari kamu" if "jarak" in a else ""
        isi = (f"<b>{a['nama']}</b><br>{a['kosong']}/{a['kapasitas']} slot kosong"
               f"<br>{s}{jarak}<br>{'Deteksi otomatis' if deteksi else 'Data contoh'}")
        ikon = folium.Icon(color=warna, icon="video-camera", prefix="fa") if deteksi else folium.Icon(color=warna)
        folium.Marker([a["lat"], a["lon"]], tooltip=a["nama"],
                      popup=folium.Popup(isi, max_width=250), icon=ikon).add_to(m)
    if pos:
        folium.Marker(list(pos), tooltip="Lokasi kamu",
                      icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    st_folium(m, height=450, use_container_width=True, returned_objects=[], key="peta")
    st.caption("🟢 Tersedia · 🟠 Hampir penuh · 🔴 Penuh. Peta diperbarui otomatis.")


@st.fragment(run_every=REFRESH)
def riwayat():
    _, log = baca()
    if log is None:
        return
    st.subheader("Riwayat deteksi terbaru")
    st.caption("Dari area uji coba yang dihitung otomatis dari video.")
    if not log:
        st.info("Belum ada kendaraan terdeteksi.")
    else:
        baris = [{"Waktu": ke_wib(l["waktu"]),
                  "Kejadian": "Motor masuk" if l["arah"] == "masuk" else "Motor keluar",
                  "Slot kosong": l["kosong_setelah"]} for l in log]
        st.dataframe(baris, hide_index=True, width="stretch")


st.title("📹 SiParkir Deteksi")
st.caption("Prototipe uji coba: slot area uji coba dihitung otomatis dari video oleh program deteksi motor.")

lok = streamlit_geolocation()
if lok and lok.get("latitude") is not None and lok.get("longitude") is not None:
    st.session_state["pos"] = (lok["latitude"], lok["longitude"])
st.caption("✅ Lokasi aktif" if st.session_state.get("pos")
           else "📍 Tekan tombol di atas, lalu izinkan akses lokasi di browser.")

tab1, tab2, tab3 = st.tabs(["Beranda", "Peta", "Riwayat"])
with tab1:
    beranda()
with tab2:
    peta()
with tab3:
    riwayat()
