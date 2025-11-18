import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

DB_PATH = "database.db"

# ---------------------- قاعدة البيانات ---------------------- #
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # جدول الشركات لو مش موجود
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            notes TEXT
        )
    """)

    conn.commit()

def fetch_df(query, params=()):
    conn = get_connection()
    return pd.read_sql_query(query, conn, params=params)

def execute(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    return cur

# ---------------------- شكل الصفحة العام ---------------------- #
st.set_page_config(page_title="نظام تسجيل الحملات الإعلانية", layout="wide")

def inject_css():
    st.markdown(
        """
        <style>
        .main, .stApp {
            direction: rtl;
            text-align: right;
            font-family: "Tahoma", "Arial", sans-serif;
        }
        h1, h2, h3 { text-align: center; }
        .section-card {
            background-color: #111827;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #1f2937;
        }
        .menu-btn { width: 100%; margin-bottom: 0.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()
init_db()

# ---------------------- نظام الصفحات (منيو يمين) ---------------------- #
if "page" not in st.session_state:
    st.session_state.page = "إضافة عملاء"

def set_page(p):
    st.session_state.page = p

st.markdown("## 📊 نظام إدارة الإعلانات والعقود")

content_col, menu_col = st.columns([4, 1])

with menu_col:
    st.markdown("### القائمة")
    st.button("إضافة عملاء", key="m_clients", on_click=set_page, args=("إضافة عملاء",), use_container_width=True)
    st.button("إضافة إعلان", key="m_ads", on_click=set_page, args=("إضافة إعلان",), use_container_width=True)
    st.button("إضافة عقود", key="m_contracts", on_click=set_page, args=("إضافة عقود",), use_container_width=True)
    st.button("تقارير الإعلانات", key="m_ads_reports", on_click=set_page, args=("تقارير الإعلانات",), use_container_width=True)
    st.button("تقارير العقود", key="m_contracts_reports", on_click=set_page, args=("تقارير العقود",), use_container_width=True)
    st.button("بحث بالعناوين", key="m_search_addresses", on_click=set_page, args=("بحث بالعناوين",), use_container_width=True)
    st.button("إضافة شركات", key="m_companies", on_click=set_page, args=("إضافة شركات",), use_container_width=True)
    st.button("استيراد (إعلانات / عقود)", key="m_import", on_click=set_page, args=("استيراد",), use_container_width=True)

# ---------------------- دوال مساعدة للتقارير بإكسل ---------------------- #
def export_report_style(df, title, company_name=None, file_name="report.xlsx"):
    """
    ينشئ ملف Excel بالشكل:
    - سطر عنوان مدموج (اسم التقرير + اسم الشركة)
    - هيدر منسق
    - بيانات
    - سطر إجمالي المبلغ في الآخر
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # هنستخدم نفس أسماء الأعمدة الحالية
        df.to_excel(writer, sheet_name="Report", startrow=4, index=False, header=False)
        workbook = writer.book
        ws = writer.sheets["Report"]

        col_count = df.shape[1]

        # عنوان أعلى التقرير
        header_text = title
        if company_name and company_name != "الكل":
            header_text = f"{title} - {company_name}"

        title_fmt = workbook.add_format(
            {"bold": True, "align": "center", "valign": "vcenter", "font_size": 14}
        )
        ws.merge_range(0, 0, 0, col_count - 1, header_text, title_fmt)

        # هيدر الأعمدة
        header_fmt = workbook.add_format(
            {"bold": True, "border": 1, "align": "center", "bg_color": "#DDDDDD"}
        )
        for col_num, col_name in enumerate(df.columns):
            ws.write(3, col_num, col_name, header_fmt)

        # تنسيقات أرقام
        money_fmt = workbook.add_format({"num_format": "#,##0.00", "border": 1})
        text_fmt = workbook.add_format({"border": 1})

        # تطبيق فورمات على الجدول
        for row_idx in range(len(df)):
            for col_idx, col_name in enumerate(df.columns):
                value = df.iloc[row_idx, col_idx]
                if isinstance(value, (int, float)) and col_name.strip().startswith("المبلغ"):
                    ws.write(4 + row_idx, col_idx, value, money_fmt)
                else:
                    ws.write(4 + row_idx, col_idx, value, text_fmt)

        # سطر إجمالي
        if "المبلغ" in df.columns:
            total = df["المبلغ"].sum()
            total_row = 4 + len(df)
            label_fmt = workbook.add_format(
                {"bold": True, "border": 1, "align": "right"}
            )
            total_fmt = workbook.add_format(
                {"bold": True, "border": 1, "num_format": "#,##0.00"}
            )
            ws.write(total_row, 0, "إجمالي", label_fmt)
            money_col = df.columns.get_loc("المبلغ")
            ws.write(total_row, money_col, total, total_fmt)

        # توسيع الأعمدة
        for i in range(col_count):
            ws.set_column(i, i, 18)

    output.seek(0)
    return output, file_name

# ---------------------- محتوى الصفحات ---------------------- #
with content_col:
    page = st.session_state.page

    # ========= إضافة عملاء ========= #
    if page == "إضافة عملاء":
        st.markdown("### 👥 إضافة / تعديل عملاء")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)

            search_name = st.text_input("بحث بالاسم", key="client_search")
            if search_name:
                df_clients = fetch_df(
                    "SELECT id, name, location, phone, bank_number, check_name FROM persons WHERE name LIKE ? ORDER BY id DESC",
                    (f"%{search_name}%",),
                )
            else:
                df_clients = fetch_df(
                    "SELECT id, name, location, phone, bank_number, check_name FROM persons ORDER BY id DESC"
                )

            st.dataframe(df_clients, use_container_width=True, height=250)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم *")
                location = st.text_input("العنوان")       # ← العنوان للعميل الجديد
                phone = st.text_input("رقم التواصل")
            with col2:
                bank_number = st.text_input("رقم الحساب")
                check_name = st.text_input("اسم إصدار الشيك")
                client_id_to_edit = st.number_input("رقم العميل للتعديل (اختياري)", min_value=0, step=1)

            save_col, edit_col = st.columns(2)
            with save_col:
                if st.button("حفظ عميل جديد"):
                    if not name.strip():
                        st.warning("رجاءً أدخل الاسم.")
                    else:
                        execute(
                            "INSERT INTO persons (name, location, bank_number, check_name, phone) VALUES (?, ?, ?, ?, ?)",
                            (name.strip(), location.strip(), bank_number.strip(), check_name.strip(), phone.strip()),
                        )
                        st.success("✅ تم حفظ العميل.")
            with edit_col:
                if st.button("تعديل عميل موجود"):
                    if client_id_to_edit > 0:
                        execute(
                            "UPDATE persons SET name=?, location=?, bank_number=?, check_name=?, phone=? WHERE id=?",
                            (name.strip(), location.strip(), bank_number.strip(), check_name.strip(), phone.strip(), int(client_id_to_edit)),
                        )
                        st.success("✅ تم التعديل.")
                    else:
                        st.warning("أدخل رقم عميل صحيح للتعديل.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= إضافة شركات ========= #
    elif page == "إضافة شركات":
        st.markdown("### 🏢 إضافة / تعديل شركات")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)

            df_companies = fetch_df("SELECT id, name, address, phone, notes FROM companies ORDER BY id ASC")
            st.dataframe(df_companies, use_container_width=True, height=250)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("اسم الشركة *")
                c_address = st.text_input("العنوان")
            with col2:
                c_phone = st.text_input("رقم التواصل")
                c_notes = st.text_area("ملاحظات عن الشركة", height=80)

            col3, col4 = st.columns(2)
            with col3:
                if st.button("حفظ شركة جديدة"):
                    if not c_name.strip():
                        st.warning("أدخل اسم الشركة.")
                    else:
                        execute(
                            "INSERT INTO companies (name, address, phone, notes) VALUES (?, ?, ?, ?)",
                            (c_name.strip(), c_address.strip(), c_phone.strip(), c_notes.strip()),
                        )
                        st.success("✅ تم حفظ الشركة.")
            with col4:
                company_id = st.number_input("رقم الشركة للتعديل / الحذف", min_value=0, step=1)
                if st.button("تعديل الشركة"):
                    if company_id > 0:
                        execute(
                            "UPDATE companies SET name=?, address=?, phone=?, notes=? WHERE id=?",
                            (c_name.strip(), c_address.strip(), c_phone.strip(), c_notes.strip(), int(company_id)),
                        )
                        st.success("✅ تم التعديل.")
                if st.button("حذف الشركة"):
                    if company_id > 0:
                        execute("DELETE FROM companies WHERE id=?", (int(company_id),))
                        st.success("✅ تم الحذف.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= إضافة إعلان ========= #
    elif page == "إضافة إعلان":
        st.markdown("### 📝 إضافة إعلان جديد")

        companies_df = fetch_df("SELECT id, name FROM companies ORDER BY name ASC")
        company_options = ["اكتب اسم الشركة يدويًا"] + companies_df["name"].tolist()

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                company_choice = st.selectbox("الشركة", company_options)
                manual_company = ""
                if company_choice == "اكتب اسم الشركة يدويًا":
                    manual_company = st.text_input("اسم الشركة (يدوي)")
                client_name = st.text_input("اسم العميل (اختياري)")  # ← اسم العميل
                location = st.text_input("العنوان")
                bank_number = st.text_input("رقم الحساب")
            with col2:
                check_name = st.text_input("اسم إصدار الشيك")
                ad_date = st.date_input("تاريخ الإعلان", value=date.today())
                status = st.selectbox("حالة الإعلان", ["لم يتم", "تم", "ملغي"])
                money = st.number_input("المبلغ", min_value=0.0, step=100.0)
            notes = st.text_area("ملاحظات", height=80)

            save_col, edit_col = st.columns(2)
            with save_col:
                if st.button("حفظ الإعلان"):
                    company_final = manual_company.strip() if company_choice == "اكتب اسم الشركة يدويًا" else company_choice
                    execute(
                        """
                        INSERT INTO adds (company, name, location, bank_number, check_name, status, date, money, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            company_final,
                            client_name.strip() if client_name.strip() else None,
                            location.strip(),
                            bank_number.strip(),
                            check_name.strip(),
                            status,
                            ad_date.isoformat(),
                            money,
                            notes.strip(),
                        ),
                    )
                    st.success("✅ تم حفظ الإعلان.")
            with edit_col:
                ad_id = st.number_input("رقم الإعلان للتعديل", min_value=0, step=1)
                if st.button("تعديل الإعلان"):
                    if ad_id > 0:
                        company_final = manual_company.strip() if company_choice == "اكتب اسم الشركة يدويًا" else company_choice
                        execute(
                            """
                            UPDATE adds
                            SET company=?, name=?, location=?, bank_number=?, check_name=?, status=?, date=?, money=?, notes=?
                            WHERE id=?
                            """,
                            (
                                company_final,
                                client_name.strip() if client_name.strip() else None,
                                location.strip(),
                                bank_number.strip(),
                                check_name.strip(),
                                status,
                                ad_date.isoformat(),
                                money,
                                notes.strip(),
                                int(ad_id),
                            ),
                        )
                        st.success("✅ تم التعديل.")
            st.markdown('</div>', uns
