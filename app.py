from datetime import datetime, timedelta, timezone
import streamlit as st
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
        return "Penuh", "🔴", terisi
    if terisi >= 85:
        return "Hampir Penuh", "🟠", terisi
    return "Tersedia", "🟢", terisi


def ke_wib(teks):
    return datetime.fromisoformat(teks).astimezone(WIB).strftime("%d/%m %H:%M:%S")


@st.fragment(run_every=REFRESH)
def tampil():
    try:
        area = klien().table("deteksi_area").select("*").eq("id", AREA_ID).execute().data[0]
        log = klien().table("deteksi_log").select("*").order("id", desc=True).limit(20).execute().data
    except Exception:
        st.error("Gagal membaca database. Cek Secrets dan tabel di Supabase.")
        return

    s, ikon, terisi = status(area["kosong"], area["kapasitas"])
    st.subheader(area["nama"])
    c1, c2 = st.columns(2)
    c1.metric("Slot kosong", area["kosong"])
    c2.metric("Keterisian", f"{terisi:.0f}%")
    st.markdown(f"{ikon} **{s}**: {area['kosong']} dari {area['kapasitas']} slot kosong")
    st.progress(terisi / 100)
    st.caption(f"Terakhir diperbarui {ke_wib(area['diperbarui'])} WIB")

    st.markdown("**Riwayat deteksi terbaru**")
    if not log:
        st.info("Belum ada kendaraan terdeteksi.")
    else:
        baris = [{"Waktu": ke_wib(l["waktu"]),
                  "Kejadian": "Motor masuk" if l["arah"] == "masuk" else "Motor keluar",
                  "Slot kosong": l["kosong_setelah"]} for l in log]
        st.dataframe(baris, hide_index=True, use_container_width=True)


st.title("📹 SiParkir Deteksi")
st.caption("Prototipe uji coba terpisah: slot kosong dihitung otomatis dari video oleh program deteksi motor.")
tampil()
