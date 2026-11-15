import os, re, sqlite3
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "portfolio.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "koushik123")  # change on Render via env var


def db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, name TEXT, email TEXT, message TEXT, sent_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    con.execute("CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY, n INTEGER)")
    con.execute("INSERT OR IGNORE INTO visits VALUES (1, 0)")
    return con


@app.route("/")
def home():
    con = db()
    con.execute("UPDATE visits SET n = n + 1 WHERE id = 1")
    con.commit()
    count = con.execute("SELECT n FROM visits WHERE id = 1").fetchone()[0]
    con.close()
    return render_template("index.html", visits=count)


@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}
    name, email, msg = (str(data.get(k, "")).strip() for k in ("name", "email", "message"))
    if not (name and email and msg):
        return jsonify(ok=False, error="Please fill in your name, email and message."), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify(ok=False, error="That email address doesn't look right."), 400
    con = db()
    con.execute("INSERT INTO messages(name, email, message) VALUES (?,?,?)", (name[:100], email[:120], msg[:2000]))
    con.commit()
    con.close()
    return jsonify(ok=True)


@app.route("/messages")
def messages():
    if request.args.get("key") != ADMIN_KEY:
        abort(404)
    con = db()
    rows = con.execute("SELECT name, email, message, sent_at FROM messages ORDER BY id DESC").fetchall()
    con.close()
    return jsonify([dict(name=r[0], email=r[1], message=r[2], sent_at=r[3]) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)
