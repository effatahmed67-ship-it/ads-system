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

    # إنشاء جدول الشركات إذا غير موجود
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
        [data-testid="stSidebar"] { display: none; } /* نخفي السايدبار */
        h1, h2, h3 { text-align: center; }
        .section-card {
            background-color: #111827;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #1f2937;
        }
        .menu-btn {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()
init_db()

# ---------------------- نظام الصفحات ---------------------- #
if "page" not in st.session_state:
    st.session_state.page = "إضافة عملاء"

def set_page(p):
    st.session_state.page = p

st.markdown("## 📊 نظام إدارة الإعلانات والعقود")

# تخطيط يشبه البرنامج القديم: محتوى يسار / منيو يمين
content_col, menu_col = st.columns([4, 1])

with menu_col:
    st.markdown("### القائمة")
    st.button("إضافة عملاء", key="m_clients", on_click=set_page, args=("إضافة عملاء",), help="صفحة العملاء", use_container_width=True)
    st.button("إضافة إعلان", key="m_ads", on_click=set_page, args=("إضافة إعلان",), use_container_width=True)
    st.button("إضافة عقود", key="m_contracts", on_click=set_page, args=("إضافة عقود",), use_container_width=True)
    st.button("تقارير الإعلانات", key="m_ads_reports", on_click=set_page, args=("تقارير الإعلانات",), use_container_width=True)
    st.button("تقارير العقود", key="m_contracts_reports", on_click=set_page, args=("تقارير العقود",), use_container_width=True)
    st.button("بحث بالعناوين", key="m_search_addresses", on_click=set_page, args=("بحث بالعناوين",), use_container_width=True)
    st.button("إضافة شركات", key="m_companies", on_click=set_page, args=("إضافة شركات",), use_container_width=True)
    st.button("استيراد (إعلانات / عقود)", key="m_import", on_click=set_page, args=("استيراد",), use_container_width=True)

# ---------------------- محتوى الصفحات ---------------------- #
with content_col:
    page = st.session_state.page

    # ========= صفحة إضافة عملاء ========= #
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
                location = st.text_input("العنوان")
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

    # ========= صفحة إضافة شركات ========= #
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

    # ========= صفحة إضافة إعلان ========= #
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
                location = st.text_input("العنوان")
                bank_number = st.text_input("رقم الحساب")
                check_name = st.text_input("اسم إصدار الشيك")
            with col2:
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
                            None,
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
                            UPDATE adds SET company=?, location=?, bank_number=?, check_name=?, status=?, date=?, money=?, notes=?
                            WHERE id=?
                            """,
                            (
                                company_final,
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
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= صفحة إضافة عقود ========= #
    elif page == "إضافة عقود":
        st.markdown("### 📄 إضافة عقد جديد")

        try:
            row = fetch_df("SELECT MAX(invoke_number) AS max_no FROM contracts").iloc[0]
            next_invoke = int(row["max_no"] + 1) if row["max_no"] is not None else 1
        except Exception:
            next_invoke = 1

        st.info(f"رقم العقد المقترح: {next_invoke}")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                invoke_number = st.number_input("رقم العقد", min_value=1, value=next_invoke, step=1)
                company = st.text_input("الشركة")
                name = st.text_input("الاسم")
                location = st.text_input("العنوان")
            with col2:
                bank_number = st.text_input("رقم الحساب")
                check_name = st.text_input("اسم إصدار الشيك")
                date_start = st.date_input("تاريخ بداية العقد", value=date.today())
                date_finish = st.date_input("تاريخ نهاية العقد", value=date.today())
                money = st.number_input("المبلغ الكامل", min_value=0.0, step=100.0)

            notes = st.text_area("ملاحظات", height=80)

            save_col, edit_col = st.columns(2)
            with save_col:
                if st.button("حفظ عقد جديد"):
                    execute(
                        """
                        INSERT INTO contracts (invoke_number, company, name, location, bank_number, check_name,
                                               date_start, date_finish, money, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            int(invoke_number),
                            company.strip(),
                            name.strip(),
                            location.strip(),
                            bank_number.strip(),
                            check_name.strip(),
                            date_start.isoformat(),
                            date_finish.isoformat(),
                            money,
                            notes.strip(),
                        ),
                    )
                    st.success("✅ تم حفظ العقد.")
            with edit_col:
                contract_id = st.number_input("رقم العقد (ID) للتعديل", min_value=0, step=1)
                if st.button("تعديل عقد"):
                    if contract_id > 0:
                        execute(
                            """
                            UPDATE contracts SET invoke_number=?, company=?, name=?, location=?, bank_number=?, check_name=?,
                                date_start=?, date_finish=?, money=?, notes=? WHERE id=?
                            """,
                            (
                                int(invoke_number),
                                company.strip(),
                                name.strip(),
                                location.strip(),
                                bank_number.strip(),
                                check_name.strip(),
                                date_start.isoformat(),
                                date_finish.isoformat(),
                                money,
                                notes.strip(),
                                int(contract_id),
                            ),
                        )
                        st.success("✅ تم التعديل.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("#### قائمة العقود")
        df_contracts = fetch_df(
            "SELECT id, invoke_number AS رقم_العقد, company AS الشركة, name AS الاسم, date_start AS بداية, date_finish AS نهاية, money AS المبلغ, notes AS ملاحظات FROM contracts ORDER BY id DESC"
        )
        st.dataframe(df_contracts, use_container_width=True, height=250)

    # ========= تقارير الإعلانات ========= #
    elif page == "تقارير الإعلانات":
        st.markdown("### 📊 تقارير الإعلانات")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                from_date = st.date_input("من تاريخ", value=date.today())
            with col2:
                to_date = st.date_input("إلى تاريخ", value=date.today())
            with col3:
                status_filter = st.selectbox("حالة الإعلان", ["الكل", "لم يتم", "تم", "ملغي"])

            names_df = fetch_df("SELECT DISTINCT company FROM adds ORDER BY company")
            company_filter = st.selectbox(
                "الشركة", ["الكل"] + names_df["company"].fillna("").tolist()
            )

            query = "SELECT company AS الشركة, location AS العنوان, status AS الحالة, date AS التاريخ, money AS المبلغ, notes AS ملاحظات FROM adds WHERE date BETWEEN ? AND ?"
            params = [from_date.isoformat(), to_date.isoformat()]
            if status_filter != "الكل":
                query += " AND status = ?"
                params.append(status_filter)
            if company_filter != "الكل":
                query += " AND company = ?"
                params.append(company_filter)

            df = fetch_df(query, tuple(params))
            st.dataframe(df, use_container_width=True, height=300)

            total = df["المبلغ"].sum() if not df.empty else 0
            st.success(f"إجمالي المبلغ في النتائج: {total:.2f}")

            if st.button("⬇️ تصدير النتائج إلى Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="ads_report", index=False)
                output.seek(0)
                st.download_button(
                    label="تحميل ملف Excel",
                    data=output,
                    file_name="ads_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= تقارير العقود ========= #
    elif page == "تقارير العقود":
        st.markdown("### 📊 تقارير العقود")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            companies_df = fetch_df("SELECT DISTINCT company FROM contracts ORDER BY company")
            sel_company = st.selectbox("الشركة", ["الكل"] + companies_df["company"].fillna("").tolist())
            search_name = st.text_input("بحث بالاسم")

            query = "SELECT invoke_number AS رقم_العقد, company AS الشركة, name AS الاسم, date_start AS بداية, date_finish AS نهاية, money AS المبلغ, notes AS ملاحظات FROM contracts WHERE 1=1"
            params = []
            if sel_company != "الكل":
                query += " AND company = ?"
                params.append(sel_company)
            if search_name:
                query += " AND name LIKE ?"
                params.append(f"%{search_name}%")

            df_c = fetch_df(query, tuple(params))
            st.dataframe(df_c, use_container_width=True, height=300)

            total_c = df_c["المبلغ"].sum() if not df_c.empty else 0
            st.success(f"إجمالي قيمة العقود: {total_c:.2f}")

            st.markdown("---")
            st.markdown("#### جدول raw لإعلانات العقود (contract_add) إن وجد")
            try:
                df_ca = fetch_df("SELECT * FROM contract_add")
                st.dataframe(df_ca, use_container_width=True, height=200)
            except Exception:
                st.info("لا يوجد جدول contract_add أو لا يحتوي بيانات بعد.")

            if st.button("⬇️ تصدير العقود إلى Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_c.to_excel(writer, sheet_name="contracts_report", index=False)
                output.seek(0)
                st.download_button(
                    label="تحميل ملف Excel",
                    data=output,
                    file_name="contracts_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= بحث بالعناوين ========= #
    elif page == "بحث بالعناوين":
        st.markdown("### 🔍 بحث بالعناوين (العملاء)")

        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            search_text = st.text_input("بحث بالاسم أو العنوان أو رقم الحساب")
            query = "SELECT name AS الاسم, location AS العنوان, phone AS رقم_التواصل, bank_number AS رقم_الحساب, check_name AS اسم_إصدار_الشيك FROM persons WHERE 1=1"
            params = []
            if search_text:
                query += " AND (name LIKE ? OR location LIKE ? OR bank_number LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

            df = fetch_df(query, tuple(params))
            st.dataframe(df, use_container_width=True, height=300)

            if st.button("⬇️ تصدير إلى Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="clients_addresses", index=False)
                output.seek(0)
                st.download_button(
                    label="تحميل ملف Excel",
                    data=output,
                    file_name="clients_addresses.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # ========= استيراد بيانات ========= #
    elif page == "استيراد":
        st.markdown("### ⬆️ استيراد (إعلانات / عقود) من ملف Excel أو CSV")

        import_type = st.selectbox("نوع البيانات", ["إعلانات", "عقود"])
        uploaded = st.file_uploader("اختر ملف", type=["xlsx", "xls", "csv"])

        if import_type == "إعلانات":
            st.info("الأعمدة المتوقعة: company, name, location, bank_number, check_name, status, date, money, notes")
        else:
            st.info("الأعمدة المتوقعة: invoke_number, company, name, location, bank_number, check_name, date_start, date_finish, money, notes")

        if uploaded is not None:
            if uploaded.name.endswith(".csv"):
                df_import = pd.read_csv(uploaded)
            else:
                df_import = pd.read_excel(uploaded)

            st.markdown("#### معاينة البيانات")
            st.dataframe(df_import.head(), use_container_width=True, height=250)

            if st.button("🚀 تنفيذ الاستيراد"):
                count = 0
                if import_type == "إعلانات":
                    for _, row in df_import.iterrows():
                        execute(
                            """
                            INSERT INTO adds (company, name, location, bank_number, check_name, status, date, money, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(row.get("company", "")),
                                str(row.get("name", "")),
                                str(row.get("location", "")),
                                str(row.get("bank_number", "")),
                                str(row.get("check_name", "")),
                                str(row.get("status", "")),
                                str(row.get("date", "")),
                                float(row.get("money", 0) or 0),
                                str(row.get("notes", "")),
                            ),
                        )
                        count += 1
                else:
                    for _, row in df_import.iterrows():
                        execute(
                            """
                            INSERT INTO contracts (invoke_number, company, name, location, bank_number, check_name,
                                                   date_start, date_finish, money, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                int(row.get("invoke_number", 0) or 0),
                                str(row.get("company", "")),
                                str(row.get("name", "")),
                                str(row.get("location", "")),
                                str(row.get("bank_number", "")),
                                str(row.get("check_name", "")),
                                str(row.get("date_start", "")),
                                str(row.get("date_finish", "")),
                                float(row.get("money", 0) or 0),
                                str(row.get("notes", "")),
                            ),
                        )
                        count += 1

                st.success(f"✅ تم استيراد {count} صف بنجاح.")
