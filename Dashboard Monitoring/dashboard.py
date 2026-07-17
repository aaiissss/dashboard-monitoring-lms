import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import tempfile
import os
import re
from io import BytesIO

def convert_df_to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False
        )

    return output.getvalue()


# ======================
# CONFIG PAGE
# ======================

st.set_page_config(
    page_title="Dashboard Monitoring LMS",
    layout="wide"
)

# ======================
# LOAD CSS
# ======================

st.markdown("""
<link rel="stylesheet"
href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
""", unsafe_allow_html=True)

with open("style.css") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

# ======================
# SESSION STATE DATA
# ======================

if "df" not in st.session_state:

    st.session_state.df = pd.DataFrame(
        columns=[
            "semester",
            "course",
            "materi",
            "kategori",
            "status"
        ]
    )

df = st.session_state.df
if "semester_cache" not in st.session_state:
    st.session_state.semester_cache = {}

# ======================
# SIDEBAR
# ======================

st.sidebar.title("📚 Dashboard LMS")

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "📈 Progress Aktivitas",
        "📄 Detail Aktivitas",
        "📥 Export Excel"
    ]
)


# ======================
# DASHBOARD
# ======================

if menu == "🏠 Dashboard":

    st.markdown("""
    <h1 class="dashboard-title">
        📚 Dashboard Monitoring Aktivitas Pembelajaran
    </h1>
    """, unsafe_allow_html=True)

    uploaded_zip = st.file_uploader(
        "📂 Upload Data Semester",
        type=["zip"]
    )

    if uploaded_zip is not None:
        st.session_state.uploaded_zip = uploaded_zip

    uploaded_zip = st.session_state.get("uploaded_zip")
    
    # ======================
    # JIKA FILE DIUPLOAD
    # ======================

    if uploaded_zip:

        try:

            # buat folder sementara
            temp_dir = tempfile.mkdtemp()

            # ekstrak zip
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            # ======================
            # DETEKSI FOLDER SEMESTER
            # ======================

            semester_list = []

            for root, dirs, files in os.walk(temp_dir):
                for d in dirs:
                    if d.lower().startswith("semester"):
                        semester_list.append(d)

            semester_list = sorted(list(set(semester_list)))

            semester_input = st.selectbox(
                "📚 Pilih Semester",
                semester_list
            )

            # folder semester
            semester_path = None
            for root, dirs, files in os.walk(temp_dir):
                if os.path.basename(root) == semester_input:
                    semester_path = root
                    break

            if semester_path is None:
                st.error(f"{semester_input} tidak ditemukan dalam ZIP")
                st.stop()

            all_monitoring = []

            if os.path.exists(semester_path):

                courses = os.listdir(semester_path)

                for course in courses:

                        #st.write("Course ditemukan:", course)

                        course_path = os.path.join(
                            semester_path,
                            course
                        )

                        files = os.listdir(course_path)

                        #st.write("Isi folder", course, ":", files)

                        csv_file = None

                        for file in files:
                            if file.lower().endswith(".csv"):
                                csv_file = file
                                break

                        if csv_file is None:
                            #st.warning(f"Tidak ada CSV pada {course}")
                            continue

                        csv_path = os.path.join(
                            course_path,
                            csv_file
                        )

                        #st.success(f"CSV ditemukan: {csv_file}")

                        try:
                            new_df = pd.read_csv(
                                csv_path,
                                sep="\t",
                                encoding="utf-16"
                            )
                        except:
                            try:
                                new_df = pd.read_csv(
                                    csv_path,
                                    sep="\t",
                                    encoding="utf-8"
                                )
                            except Exception as e:
                                st.error(f"Gagal membaca CSV: {e}")
                                continue

                        #st.write("Kolom CSV:", list(new_df.columns))
                        headers = list(new_df.columns)
                        #st.write("Kolom yang ditemukan:")
                        #st.write(headers)

                        materi_list = []

                        ignore_columns = [
                            "username",
                            "id number",
                            "email address",
                            "mobile phone",
                            "first name",
                            "last name",
                            "full name"
                        ]

                        for col in headers:

                            col_lower = str(col).lower()

                            if col_lower.strip() in ignore_columns:
                                continue

                            if "unnamed" in col_lower:
                                continue

                            if re.match(
                                r"\d{4}-\d{2}-\d{2}",
                                str(col).strip()
                            ):
                                continue

                            materi_list.append(col)

                        materi_keywords = [
                            "materi",
                            "slide",
                            "presentasi",
                            "modul",
                            "pengantar"
                        ]

                        evaluasi_keywords = [
                            "tugas",
                            "quiz",
                            "kuis",
                            "uts",
                            "uas",
                            "project",
                            "praktikum"
                        ]

                        for materi in materi_list:

                            nama = str(materi).lower()

                            if any(k in nama for k in evaluasi_keywords):
                                kategori = "Tugas & Evaluasi"

                            else:
                                kategori = "Materi"

                            all_monitoring.append({
                                "semester": semester_input,
                                "course": course,
                                "materi": materi,
                                "kategori": kategori,
                                "status": "Terunggah"
                            })
                #st.write("Jumlah data monitoring:", len(all_monitoring))

                if len(all_monitoring) == 0:
                    st.error("Tidak ada materi yang berhasil dikenali")

                monitoring_df = pd.DataFrame(all_monitoring)
        
                #st.dataframe(
                    #pd.DataFrame(all_monitoring)
                #)

                st.session_state.df = monitoring_df

                df = st.session_state.df

                st.success("✅ Data semester berhasil dimuat")

                #st.write("Folder Semester:", semester_path)
                #st.write("Jumlah Course:", len(courses))
                #st.write("Jumlah Aktivitas:", len(monitoring_df))

                #st.dataframe(
                    #monitoring_df.head()
                #)

        except Exception as e:
                st.error(f"❌ Error: {e}")

    # ======================
    # AMBIL DATA TERBARU
    # ======================

    df = st.session_state.df

    # ======================
    # JIKA DATA KOSONG
    # ======================

    if df.empty:
        st.warning("⚠️ Silakan upload data LMS terlebih dahulu.")

    else:
        # card
        # grafik
        # tabel

        # ======================
        # HITUNG KATEGORI
        # ======================

        jumlah_course = df["course"].nunique()

        materi_count = len(
            df[df["kategori"] == "Materi"]
        )

        evaluasi_count = len(
            df[df["kategori"] == "Tugas & Evaluasi"]
        )

        total_aktivitas = len(df)
        # ======================
        # CARD
        # ======================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="card-box blue">
                <i class="fa-solid fa-book icon-bg"></i>
                <div class="card-title">Jumlah Mata Kuliah</div>
                <div class="card-value">{jumlah_course}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card-box purple">
                <i class="fa-solid fa-book-open icon-bg"></i>
                <div class="card-title">Materi Pembelajaran</div>
                <div class="card-value">{materi_count}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card-box green">
                <i class="fa-solid fa-clipboard-check icon-bg"></i>
                <div class="card-title">Tugas & Evaluasi</div>
                <div class="card-value">{evaluasi_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="card-box orange">
                <i class="fa-solid fa-chart-line icon-bg"></i>
                <div class="card-title">Total Aktivitas</div>
                <div class="card-value">{total_aktivitas}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ======================
        # VISUALISASI AKTIVITAS
        # ======================

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:

            st.markdown("### 📊 Distribusi Aktivitas LMS")

            course_count = (
            df.groupby("course")
            .size()
            .reset_index(name="Jumlah Aktivitas")
            .sort_values(
                by="Jumlah Aktivitas",
                ascending=False
            )
        )

            fig_bar = px.bar(
                course_count,
                x=course_count.index,
                y="Jumlah Aktivitas",
                text="Jumlah Aktivitas",
                hover_name="course"
            )
            
            fig_bar.update_layout(
                xaxis_title="Mata Kuliah",
                yaxis_title="Jumlah Aktivitas",
                height=450
            )

            fig_bar.update_xaxes(
                showticklabels=False
            )

            fig_bar.update_traces(
                hovertemplate=
                "<b>%{customdata[0]}</b><br>" +
                "Jumlah Aktivitas: %{y}<extra></extra>",
                customdata=course_count[["course"]]
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        with col_chart2:

            st.markdown("### 🥧 Komposisi Aktivitas")

            kategori_count = (
                df["kategori"]
                .value_counts()
                .reset_index()
            )

            kategori_count.columns = [
                "Kategori",
                "Jumlah"
            ]

            fig_pie = px.pie(
                kategori_count,
                names="Kategori",
                values="Jumlah",
                hole=0.45
            )

            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label"
            )

            fig_pie.update_layout(
                height=400
            )

            st.plotly_chart(
                fig_pie,
                use_container_width=True
            )

        # ======================
        # TABEL REKAP
        # ======================

        st.markdown("### 📋 Rekap Monitoring")

        df_display = df.copy()

        df_display["materi"] = (
            df_display["materi"]
            .astype(str)
            .str.slice(0, 35)
        )

        df_display["materi"] = df_display["materi"].apply(
            lambda x: x + "..." if len(x) >= 50 else x
        )

        df_display.index = range(
            1,
            len(df_display) + 1
        )

        df_display = df_display.rename(
            columns={
                "course": "Mata Kuliah",
                "materi": "Aktivitas",
                "kategori": "Kategori",
                "status": "Status"
            }
        )

        st.dataframe(
            df_display[
                [
                    "Mata Kuliah",
                    "Aktivitas",
                    "Kategori",
                    "Status"
                ]
            ],
            use_container_width=True
        )     
# ======================
# PROGRESS MATERI
# ======================

elif menu == "📈 Progress Aktivitas":

    df = st.session_state.df

    st.markdown("## 📈 Progress Aktivitas")

    if df.empty:
        st.warning("⚠️ Silakan upload data terlebih dahulu")
        st.stop()

    course_filter = st.selectbox(
        "Pilih Course",
        df["course"].unique()
    )

    progress_df = (
        df[df["course"] == course_filter]
        .reset_index(drop=True)
    )

    # Mulai penomoran dari 1
    progress_df.index = range(1, len(progress_df) + 1)

    total_aktivitas = len(progress_df)

    materi_count = len(
        progress_df[
            progress_df["kategori"] == "Materi"
        ]
    )

    evaluasi_count = len(
        progress_df[
            progress_df["kategori"] == "Tugas & Evaluasi"
        ]
    )

    st.markdown(f"""
    ### 📚 {course_filter}

    - Total Aktivitas : **{total_aktivitas}**
    - Materi Pembelajaran : **{materi_count}**
    - Tugas & Evaluasi : **{evaluasi_count}**
    """)

    st.progress(1.0)

    st.success(
        f"{total_aktivitas} aktivitas berhasil dimonitor"
    )

    st.markdown("### 📋 Detail Aktivitas")

    st.dataframe(
        progress_df[
            [
                "materi",
                "kategori",
                "status"
            ]
        ],
        use_container_width=True
    )

# ======================
# DETAIL MATERI
# ======================

elif menu == "📄 Detail Aktivitas":
    
    df = st.session_state.df

    st.markdown("## 📄 Detail Aktivitas")

    if df.empty:

        st.warning(
            "⚠️ Silakan upload data terlebih dahulu"
        )

        st.stop()

    search_materi = st.text_input(
        "🔍 Cari Aktivitas"
    )

    materi_filter = df[
        df["materi"].str.contains(
            search_materi,
            case=False,
            na=False
        )
    ]["materi"].unique()

    materi_pilih = st.selectbox(
        "📚 Pilih Aktivitas",
        materi_filter
    )

    detail = df[
        df["materi"] == materi_pilih
    ]

    if not detail.empty:

        data = detail.iloc[0]

        st.markdown(f"""
        <div class="chart-box">

        <h3 style="
        margin-bottom:25px;
        ">
        📘 Informasi Materi
        </h3>

        <div style="
        display:grid;
        grid-template-columns:180px 20px 1fr;
        gap:18px;
        ">

        <div><b>Course</b></div>
        <div>:</div>
        <div>{data['course']}</div>

        <div><b>Materi</b></div>
        <div>:</div>
        <div>{data['materi']}</div>

        <div><b>Kategori</b></div>
        <div>:</div>
        <div>{data['kategori']}</div>

        <div><b>Status</b></div>
        <div>:</div>
        <div>{data['status']}</div>

        <div><b>Semester</b></div>
        <div>:</div>
        <div>{data['semester']}</div>

        </div>

        </div>
        """, unsafe_allow_html=True)

# ======================
# EXPORT EXCEL
# ======================

elif menu == "📥 Export Excel":

    st.markdown("## 📥 Export Data Monitoring")

    df = st.session_state.df
    if df.empty:
        st.warning("⚠️ Silakan upload data terlebih dahulu")
        st.stop()

    jenis_export = st.radio(
        "Pilih Jenis Export",
        [
            "Semua Data Semester",
            "Per Mata Kuliah"
        ]
    )

    if jenis_export == "Semua Data Semester":

        export_df = df.copy()

        nama_file = (
            df["semester"].iloc[0]
            .replace(" ", "_")
            .lower()
        )

        st.download_button(
            label="📥 Download Semua Data Semester",
            data=convert_df_to_excel(export_df),
            file_name=f"{nama_file}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:

        course_export = st.selectbox(
            "📚 Pilih Mata Kuliah",
            sorted(df["course"].unique())
        )

        export_df = df[
            df["course"] == course_export
        ]

        nama_file = (
            course_export[:30]
            .replace(" ", "_")
            .replace("/", "_")
        )

        st.download_button(
            label="📥 Download Data Mata Kuliah",
            data=convert_df_to_excel(export_df),
            file_name=f"{nama_file}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
