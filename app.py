from flask import Flask, render_template

app = Flask(__name__)

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("dashboard.html")

# تشغيل التطبيق لو محلياً
if __name__ == "__main__":
    app.run(debug=True)
