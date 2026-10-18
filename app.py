from datetime import datetime, timedelta, timezone
import folium
import streamlit as st
from streamlit_folium import st_folium
from supabase import create_client

st.set_page_config(page_title="SiParkir Deteksi", page_icon="📹")

AREA_ID = "uji-1"
REFRESH = 5  # detik
WIB = timezone(timedelta(hours=7))


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


def baca():
    try:
        area = klien().table("deteksi_area").select("*").eq("id", AREA_ID).execute().data[0]
        log = klien().table("deteksi_log").select("*").order("id", desc=True).limit(20).execute().data
        return area, log
    except Exception:
        st.error("Gagal membaca database. Cek Secrets dan tabel di Supabase.")
        return None, None


@st.fragment(run_every=REFRESH)
def beranda():
    area, log = baca()
    if area is None:
        return

    s, ikon, _, terisi = status(area["kosong"], area["kapasitas"])
    st.subheader(area["nama"])
    c1, c2 = st.columns(2)
    c1.metric("Slot kosong", area["kosong"])
    c2.metric("Keterisian", f"{terisi:.0f}%")
    st.markdown(f"{ikon} **{s}**: {area['kosong']} dari {area['kapasitas']} slot kosong")
    st.progress(min(max(terisi / 100, 0), 1))
    st.caption(f"Terakhir diperbarui {ke_wib(area['diperbarui'])} WIB")

    st.markdown("**Riwayat deteksi terbaru**")
    if not log:
        st.info("Belum ada kendaraan terdeteksi.")
    else:
        baris = [{"Waktu": ke_wib(l["waktu"]),
                  "Kejadian": "Motor masuk" if l["arah"] == "masuk" else "Motor keluar",
                  "Slot kosong": l["kosong_setelah"]} for l in log]
        st.dataframe(baris, hide_index=True, width="stretch")


@st.fragment(run_every=REFRESH)
def peta():
    area, _ = baca()
    if area is None:
        return
    if area.get("lat") is None or area.get("lon") is None:
        st.info("Koordinat area belum diisi di Supabase (kolom lat dan lon).")
        return

    s, _, warna, _ = status(area["kosong"], area["kapasitas"])
    isi = (f"<b>{area['nama']}</b><br>{area['kosong']}/{area['kapasitas']} slot kosong"
           f"<br>{s} · diperbarui {ke_wib(area['diperbarui'])}")
    m = folium.Map(location=[area["lat"], area["lon"]], zoom_start=18)
    folium.Marker([area["lat"], area["lon"]], tooltip=area["nama"],
                  popup=folium.Popup(isi, max_width=250),
                  icon=folium.Icon(color=warna)).add_to(m)
    st_folium(m, height=450, use_container_width=True, returned_objects=[], key="peta")
    st.caption("🟢 Tersedia · 🟠 Hampir penuh · 🔴 Penuh. Peta diperbarui otomatis.")


st.title("📹 SiParkir Deteksi")
st.caption("Prototipe uji coba terpisah: slot kosong dihitung otomatis dari video oleh program deteksi motor.")

tab1, tab2 = st.tabs(["Beranda", "Peta"])
with tab1:
    beranda()
with tab2:
    peta()
