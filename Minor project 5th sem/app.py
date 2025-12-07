import os
import uuid
import qrcode
from io import BytesIO
from flask import (
    Flask, render_template,
    request, redirect, url_for, session, send_file
)
from flask_mysqldb import MySQL

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates")
)
app.secret_key = "your-super-secret-key"

# Base URL used inside QR codes – use your PC's LAN IP shown in the Flask log
# Example log line: Running on http://192.168.29.238:5000
BASE_URL = "http://192.168.29.238:5000"

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Kavyansh@123'
app.config['MYSQL_DB'] = 'fakeproductdb'
mysql = MySQL(app)

# ---------- AUTH & RESET ----------

@app.route("/")
def home():
    return redirect(url_for('auth'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    login_error = ""
    register_error = ""
    register_msg = ""
    if request.method == "POST":
        # LOGIN SUBMIT
        if 'login_submit' in request.form:
            company = request.form.get("company_login", "").strip()
            password = request.form.get("password_login", "").strip()
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT password FROM companies WHERE company = %s",
                (company,)
            )
            row = cur.fetchone()
            cur.close()
            if row and row[0] == password:
                session['company'] = company
                return redirect(url_for("dashboard"))
            else:
                login_error = "Invalid login. Please try again!"
        # REGISTER SUBMIT
        elif 'register_submit' in request.form:
            company = request.form.get("company_register", "").strip()
            password = request.form.get("password_register", "").strip()
            if not company or not password:
                register_error = "Both fields are required."
            else:
                cur = mysql.connection.cursor()
                try:
                    cur.execute(
                        'INSERT INTO companies (company, password) VALUES (%s, %s)',
                        (company, password)
                    )
                    mysql.connection.commit()
                    cur.close()
                    register_msg = "Company successfully registered! Please log in."
                except Exception:
                    cur.close()
                    register_error = "Company name already exists."
    return render_template(
        'auth.html',
        login_error=login_error,
        register_error=register_error,
        register_msg=register_msg
    )

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    error = ""
    msg = ""
    if request.method == 'POST':
        company = request.form.get('company', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if not company or not new_password:
            error = "Both fields are required."
        else:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT id FROM companies WHERE company = %s",
                (company,)
            )
            row = cur.fetchone()
            if not row:
                error = "Company not found."
            else:
                cur.execute(
                    "UPDATE companies SET password = %s WHERE company = %s",
                    (new_password, company)
                )
                mysql.connection.commit()
                cur.close()
                msg = "Password reset successful! Please log in."
    return render_template('reset_password.html', error=error, msg=msg)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # clear login session and go back to auth
    session.pop('company', None)
    return redirect(url_for('auth'))

# ---------- DASHBOARD & PRODUCTS ----------

@app.route('/dashboard')
def dashboard():
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    cur = mysql.connection.cursor()
    query = """
        SELECT id, name, brand, batch, category, unique_code
        FROM products
        WHERE registered_by = %s
        ORDER BY id DESC
    """
    cur.execute(query, (company,))
    rows = cur.fetchall()
    cur.close()

    products = rows  # tuples: (id, name, brand, batch, category, unique_code)
    total_brands = None
    today_scans = 0

    return render_template(
        'dashboard.html',
        company=company,
        products=products,
        total_brands=total_brands,
        today_scans=today_scans
    )

@app.route("/products")
def products_page():
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT id, name, brand, batch, category, unique_code
        FROM products
        WHERE registered_by = %s
        ORDER BY id DESC
        """,
        (company,)
    )
    products = cur.fetchall()
    cur.close()

    return render_template("products.html", company=company, products=products)

# ---------- REGISTER / UPDATE / DELETE PRODUCT ----------

@app.route('/register-product', methods=['GET', 'POST'])
def register_product():
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    error = ""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        brand = request.form.get('brand', '').strip()
        batch = request.form.get('batch', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            error = "Please provide the product name."
        else:
            unique_code = str(uuid.uuid4())
            cur = mysql.connection.cursor()
            try:
                query = """
                    INSERT INTO products
                        (name, brand, batch, category, description, unique_code, registered_by)
                    VALUES (%s,   %s,   %s,   %s,       %s,          %s,         %s)
                """
                cur.execute(
                    query,
                    (name, brand, batch, category, description, unique_code, company)
                )
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('dashboard'))
            except Exception:
                cur.close()
                error = "An error occurred, possibly duplicate unique code."
    return render_template('register_product.html', error=error)

@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM products WHERE id = %s AND registered_by = %s",
        (product_id, company)
    )
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))

@app.route('/update-product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT name, brand, batch, category, description
        FROM products
        WHERE id = %s AND registered_by = %s
        """,
        (product_id, company)
    )
    row = cur.fetchone()
    error = ""
    if not row:
        cur.close()
        return redirect(url_for('dashboard'))

    name, brand, batch, category, description = row

    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        new_brand = request.form.get('brand', '').strip()
        new_batch = request.form.get('batch', '').strip()
        new_category = request.form.get('category', '').strip()
        new_description = request.form.get('description', '').strip()

        if not new_name:
            error = "Product name cannot be empty."
        else:
            cur.execute(
                """
                UPDATE products
                SET name = %s,
                    brand = %s,
                    batch = %s,
                    category = %s,
                    description = %s
                WHERE id = %s AND registered_by = %s
                """,
                (new_name, new_brand, new_batch, new_category, new_description, product_id, company)
            )
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('dashboard'))

    cur.close()
    return render_template(
        'update_product.html',
        name=name,
        brand=brand,
        batch=batch,
        category=category,
        description=description,
        error=error,
        product_id=product_id
    )

# ---------- VERIFY & QR ----------

@app.route("/verify/<unique_code>")
def verify(unique_code):
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT name, brand, batch, category
        FROM products
        WHERE unique_code = %s
        """,
        (unique_code,)
    )
    product = cur.fetchone()
    cur.close()

    if product:
        prod_dict = {
            "name": product[0],
            "brand": product[1],
            "batch": product[2],
            "category": product[3],
            "code": unique_code
        }
        return render_template("verify.html", status="genuine", product=prod_dict)
    else:
        return render_template("verify.html", status="fake", product=None)

@app.route('/product/<int:product_id>/qr')
def show_qr(product_id):
    company = session.get('company')
    if not company:
        return redirect(url_for('auth'))

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT unique_code, registered_by FROM products WHERE id = %s",
        (product_id,)
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return "Product not found", 404

    unique_code, registered_by = row
    if registered_by != company:
        return "Unauthorized", 403

    verify_url = f"{BASE_URL}/verify/{unique_code}"

    img = qrcode.make(verify_url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ---------- TEST DB ----------

@app.route('/testdb')
def testdb():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return "Database connection SUCCESSFUL!"
    except Exception as e:
        return f"Database connection FAILED: {e}"

if __name__ == "__main__":
    # host=0.0.0.0 allows phone on same Wi‑Fi to reach the app
    app.run(host="0.0.0.0", port=5000, debug=True)
