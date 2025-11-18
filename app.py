import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DB_PATH = "database.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    # يتأكد إن الجداول موجودة
    conn = get_connection()
    cur = conn.cursor()
    required = {"persons", "adds", "contracts", "contract_add"}
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {r[0] for r in cur.fetchall()}
    missing = required - existing
    if missing:
        st.error(f"❌ قاعدة البيانات لا تحتوي على الجداول المطلوبة: {', '.join(missing)}")
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

st.set_page_config(page_title="نظام تسجيل الحملات", layout="wide")
init_db()

st.sidebar.title("📊 نظام تسجيل الحملات")
page = st.sidebar.radio(
    "اختر الصفحة",
    ["إدارة العملاء", "تسجيل الإعلانات", "العقود", "التقارير"],
)

st.title("📊 نظام تسجيل الحملات الإعلانية")

# ------------- إدارة العملاء -------------
if page == "إدارة العملاء":
    st.subheader("👥 إضافة / إدارة العملاء")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("اسم العميل *")
        location = st.text_input("العنوان / المنطقة")
        phone = st.text_input("رقم الهاتف")

    with col2:
        bank_number = st.text_input("رقم الحساب البنكي")
        check_name = st.text_input("اسم المستفيد على الشيك")

    if st.button("💾 حفظ العميل"):
        if not name.strip():
            st.warning("رجاءً أدخل اسم العميل.")
        else:
            execute(
                "INSERT INTO persons (name, location, bank_number, check_name, phone) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), location.strip(), bank_number.strip(), check_name.strip(), phone.strip()),
            )
            st.success("✅ تم حفظ العميل بنجاح.")

    st.markdown("---")
    st.subheader("📋 قائمة العملاء")

    search = st.text_input("بحث بالاسم")
    if search:
        df_persons = fetch_df(
            "SELECT id, name, location, phone, bank_number, check_name FROM persons WHERE name LIKE ? ORDER BY id DESC",
            (f"%{search}%",),
        )
    else:
        df_persons = fetch_df(
            "SELECT id, name, location, phone, bank_number, check_name FROM persons ORDER BY id DESC"
        )

    st.dataframe(df_persons, use_container_width=True)

# ------------- تسجيل الإعلانات -------------
elif page == "تسجيل الإعلانات":
    st.subheader("📝 تسجيل إعلان جديد")

    persons_df = fetch_df("SELECT id, name FROM persons ORDER BY name ASC")
    person_names = ["بدون"] + persons_df["name"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("الشركة / الجهة المعلنة")
        person_name = st.selectbox("اسم العميل المرتبط", person_names)
        location = st.text_input("مكان الإعلان / المنصة")
        status = st.selectbox("حالة الإعلان", ["قيد التنفيذ", "منتهي", "ملغي"])

    with col2:
        bank_number = st.text_input("رقم الحساب البنكي")
        check_name = st.text_input("اسم المستفيد على الشيك")
        ad_date = st.date_input("تاريخ الإعلان", value=date.today())
        money = st.number_input("قيمة الحملة", min_value=0.0, step=100.0)
    notes = st.text_area("ملاحظات")

    if st.button("💾 حفظ الإعلان"):
        execute(
            """
            INSERT INTO adds (company, name, location, bank_number, check_name, status, date, money, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company.strip(),
                None if person_name == "بدون" else person_name,
                location.strip(),
                bank_number.strip(),
                check_name.strip(),
                status,
                ad_date.isoformat(),
                money,
                notes.strip(),
            ),
        )
        st.success("✅ تم حفظ الإعلان بنجاح.")

    st.markdown("---")
    st.subheader("📋 قائمة الإعلانات")

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        search_company = st.text_input("بحث باسم الشركة")
    with colf2:
        search_person = st.text_input("بحث باسم العميل")
    with colf3:
        status_filter = st.selectbox("تصفية بالحالة", ["الكل", "قيد التنفيذ", "منتهي", "ملغي"])

    query = "SELECT id, company, name, location, status, date, money, notes FROM adds WHERE 1=1"
    params = []
    if search_company:
        query += " AND company LIKE ?"
        params.append(f"%{search_company}%")
    if search_person:
        query += " AND name LIKE ?"
        params.append(f"%{search_person}%")
    if status_filter != "الكل":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY date DESC, id DESC"
    df_adds = fetch_df(query, tuple(params))
    st.dataframe(df_adds, use_container_width=True)

# ------------- العقود -------------
elif page == "العقود":
    st.subheader("📄 العقود")

    # حساب رقم إذن جديد
    row = fetch_df("SELECT MAX(invoke_number) AS max_no FROM contracts").iloc[0]
    next_invoke = int(row["max_no"] + 1) if row["max_no"] is not None else 1
    st.info(f"رقم الإذن الجديد المقترح: {next_invoke}")

    col1, col2 = st.columns(2)
    with col1:
        invoke_number = st.number_input("رقم الإذن", min_value=1, value=next_invoke)
        company = st.text_input("الشركة")
        name = st.text_input("اسم العميل")
        location = st.text_input("الموقع / المنطقة")

    with col2:
        bank_number = st.text_input("رقم الحساب البنكي")
        check_name = st.text_input("اسم المستفيد")
        date_start = st.date_input("تاريخ بداية العقد", value=date.today())
        date_finish = st.date_input("تاريخ نهاية العقد", value=date.today())
        money = st.number_input("قيمة العقد", min_value=0.0, step=100.0)

    notes = st.text_area("ملاحظات العقد")

    if st.button("💾 حفظ العقد"):
        execute(
            """
            INSERT INTO contracts (invoke_number, company, name, location, bank_number, check_name,
                                   date_start, date_finish, money, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoke_number,
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
        st.success("✅ تم حفظ العقد بنجاح.")

    st.markdown("---")
    st.subheader("📋 قائمة العقود")

    df_contracts = fetch_df(
        "SELECT id, invoke_number, company, name, location, date_start, date_finish, money, notes FROM contracts ORDER BY id DESC"
    )
    st.dataframe(df_contracts, use_container_width=True)

# ------------- التقارير -------------
elif page == "التقارير":
    st.subheader("📈 التقارير والإجماليات")

    st.markdown("### إجمالي قيمة الإعلانات حسب الشركة")
    df1 = fetch_df("SELECT company AS الشركة, SUM(money) AS اجمالي_الإعلانات FROM adds GROUP BY company ORDER BY اجمالي_الإعلانات DESC")
    st.dataframe(df1, use_container_width=True)

    st.markdown("### إجمالي قيمة الإعلانات حسب العميل")
    df2 = fetch_df("SELECT name AS العميل, SUM(money) AS اجمالي_الإعلانات FROM adds GROUP BY name ORDER BY اجمالي_الإعلانات DESC")
    st.dataframe(df2, use_container_width=True)

    st.markdown("### إجمالي العقود")
    df3 = fetch_df("SELECT company AS الشركة, SUM(money) AS اجمالي_العقود FROM contracts GROUP BY company ORDER BY اجمالي_العقود DESC")
    st.dataframe(df3, use_container_width=True)

    # تنزيل كل البيانات كملف Excel واحد
    if st.button("⬇️ تحميل نسخة Excel لكل الجداول"):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            fetch_df("SELECT * FROM persons").to_excel(writer, sheet_name="clients", index=False)
            fetch_df("SELECT * FROM adds").to_excel(writer, sheet_name="adds", index=False)
            fetch_df("SELECT * FROM contracts").to_excel(writer, sheet_name="contracts", index=False)
            fetch_df("SELECT * FROM contract_add").to_excel(writer, sheet_name="contract_add", index=False)
        output.seek(0)
        st.download_button(
            label="⬇️ تحميل ملف Excel",
            data=output,
            file_name="ads_system_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
