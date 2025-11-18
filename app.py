import os
import sqlite3
from io import BytesIO

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    send_file,
    flash,
)
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
app.secret_key = "ads_system_2025"

# ============================
# PATHS
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================
# DATABASE CONNECTION
# ============================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================
# INIT DB
# ============================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            logo TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            account_number TEXT,
            bank_name TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            company_id INTEGER,
            title TEXT,
            notes TEXT,
            amount REAL,
            ad_status TEXT,
            ad_date TEXT,
            attachment TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            company_id INTEGER,
            contract_number TEXT,
            title TEXT,
            amount REAL,
            start_date TEXT,
            end_date TEXT,
            notes TEXT,
            attachment TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        """
    )

    conn.commit()
    conn.close()


init_db()

# ============================
# ROUTES
# ============================


@app.route("/")
def home():
    return render_template("index.html")


# ----------- Companies ----------
@app.route("/companies")
def companies():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies ORDER BY id DESC")
    return render_template("companies.html", companies=cur.fetchall())


@app.route("/add_company", methods=["POST"])
def add_company():
    name = request.form.get("company_name")
    file = request.files.get("logo")

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO companies (name, logo) VALUES (?, ?)", (name, filename))
    conn.commit()
    return redirect(url_for("companies"))


# ----------- Clients ----------
@app.route("/clients")
def clients():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id DESC")
    return render_template("add-client.html", clients=cur.fetchall())


@app.route("/add_client", methods=["POST"])
def add_client():
    name = request.form.get("name")
    address = request.form.get("address")
    phone = request.form.get("phone")
    account_number = request.form.get("account_number")
    bank_name = request.form.get("bank_name")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO clients (name, address, phone, account_number, bank_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, address, phone, account_number, bank_name),
    )
    conn.commit()
    return redirect(url_for("clients"))


# ----------- Ads ----------
@app.route("/add_ad")
def add_ad():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM companies")
    companies = cur.fetchall()

    cur.execute("SELECT * FROM clients")
    clients = cur.fetchall()

    return render_template("add-ad.html", clients=clients, companies=companies)


@app.route("/save_ad", methods=["POST"])
def save_ad():
    client_id = request.form.get("client")
    company_id = request.form.get("company")
    title = request.form.get("title")
    notes = request.form.get("notes")
    amount = request.form.get("amount")
    ad_status = request.form.get("ad_status")
    ad_date = request.form.get("ad_date")

    file = request.files.get("attachment")
    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ads (client_id, company_id, title, notes, amount, ad_status, ad_date, attachment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (client_id, company_id, title, notes, amount, ad_status, ad_date, filename),
    )

    conn.commit()
    return redirect(url_for("add_ad"))


# ----------- Contracts ----------
@app.route("/add_contract")
def add_contract():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM companies")
    companies = cur.fetchall()

    cur.execute("SELECT * FROM clients")
    clients = cur.fetchall()

    return render_template("add-contract.html", clients=clients, companies=companies)


@app.route("/save_contract", methods=["POST"])
def save_contract():
    client_id = request.form.get("client")
    company_id = request.form.get("company")
    contract_number = request.form.get("contract_number")
    title = request.form.get("title")
    notes = request.form.get("notes")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    amount = request.form.get("amount")

    file = request.files.get("attachment")
    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO contracts (
            client_id, company_id, contract_number, title,
            amount, start_date, end_date, notes, attachment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_id,
            company_id,
            contract_number,
            title,
            amount,
            start_date,
            end_date,
            notes,
            filename,
        ),
    )

    conn.commit()
    return redirect(url_for("add_contract"))


# ----------- Reports ----------
@app.route("/ads_report")
def ads_report():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ads.*, clients.name AS client_name, companies.name AS company_name
        FROM ads
        LEFT JOIN clients ON ads.client_id = clients.id
        LEFT JOIN companies ON ads.company_id = companies.id
        ORDER BY ads.id DESC
        """
    )
    return render_template("ads-report.html", ads=cur.fetchall())


@app.route("/contracts_report")
def contracts_report():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT contracts.*, clients.name AS client_name, companies.name AS company_name
        FROM contracts
        LEFT JOIN clients ON contracts.client_id = clients.id
        LEFT JOIN companies ON contracts.company_id = companies.id
        ORDER BY contracts.id DESC
        """
    )
    return render_template("contracts-report.html", contracts=cur.fetchall())


# ----------- Search (Clients) ----------
@app.route("/search", methods=["GET", "POST"])
def search():
    name = ""
    results = []

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()

        conn = get_db()
        cur = conn.cursor()

        if name:
            cur.execute(
                "SELECT * FROM clients WHERE name LIKE ? ORDER BY id DESC",
                ("%" + name + "%",),
            )
        else:
            cur.execute("SELECT * FROM clients ORDER BY id DESC")

        results = cur.fetchall()

    return render_template("search.html", results=results, search_name=name)


# ✅ Export search / all clients to Excel
@app.route("/export_clients")
def export_clients():
    name = (request.args.get("name") or "").strip()

    conn = get_db()
    cur = conn.cursor()

    if name:
        cur.execute(
            "SELECT * FROM clients WHERE name LIKE ? ORDER BY id DESC",
            ("%" + name + "%",),
        )
    else:
        cur.execute("SELECT * FROM clients ORDER BY id DESC")

    rows = cur.fetchall()
    data = [dict(r) for r in rows]
    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Clients")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="clients_search.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ----------- Import Ads (Excel) ----------
@app.route("/import_ads")
def import_ads():
    # صفحة فيها فورم رفع الملف + زر "تحميل القالب"
    return render_template("import_ads.html")


# ✅ تحميل قالب الاستيراد
@app.route("/import_ads/template")
def download_ads_template():
    # قالب بسيط بالأعمدة الأساسية
    df = pd.DataFrame(
        columns=[
            "name",   # اسم الإعلان (إجباري)
            "date",   # تاريخ الإعلان (إجباري)
            "company",
            "client",
            "amount",
            "notes",
        ]
    )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="AdsTemplate")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="ads_import_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/upload_ads", methods=["POST"])
def upload_ads():
    file = request.files.get("file")
    if not file:
        flash("لم يتم اختيار ملف")
        return redirect(url_for("import_ads"))

    # قراءة الملف
    df = pd.read_excel(file)

    conn = get_db()
    cur = conn.cursor()

    for _, row in df.iterrows():
        title = row.get("name")
        date = row.get("date")

        # لو الاسم أو التاريخ فاضيين نتخطى الصف
        if pd.isna(title) or pd.isna(date):
            continue

        notes = row.get("notes")
        amount = row.get("amount")

        cur.execute(
            """
            INSERT INTO ads (title, ad_date, notes, amount)
            VALUES (?, ?, ?, ?)
            """,
            (str(title), str(date), notes, amount),
        )

    conn.commit()
    flash("تم استيراد الإعلانات بنجاح")
    return redirect(url_for("ads_report"))


# ----------- Upload Static Files ----------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ----------- Run ----------
if __name__ == "__main__":
    # للتجربة محلياً
    app.run(debug=True)
