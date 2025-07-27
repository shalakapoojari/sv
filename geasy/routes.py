import calendar
from datetime import datetime
from flask import Blueprint, flash, jsonify, render_template, request, redirect, url_for
import pymysql
from flask import session
from app.database import get_db_connection, get_db
from . import geasy_bp

#LOGIN PAGE
@geasy_bp.route("/", methods=["GET", "POST"])
def admin_login():
    print("admin_login route triggered")  # <--- debug print

    if request.method == "POST":
        emp_id = request.form.get("emp_id")
        password = request.form.get("password")
        print("POST received:", emp_id, password)

        if not emp_id or not password:
            flash("Missing ID or password", "danger")
            return redirect(url_for("geasy_bp.admin_login"))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT emp_id, password FROM gadmin WHERE emp_id = %s", (emp_id,))
            admin = cur.fetchone()
            cur.close()
            conn.close()
            print("Fetched admin:", admin)

            if not admin:
                flash("Invalid ID", "danger")
                return redirect(url_for("geasy_bp.admin_login"))

            db_emp_id = admin["emp_id"]
            db_password = admin["password"]


            if db_password != password:
                flash("Incorrect password", "danger")
                return redirect(url_for("geasy_bp.admin_login"))

            # ✅ Set session properly
            session["admin_logged_in"] = True
            session["admin_emp_id"] = db_emp_id
            print("Session set, redirecting to dashboard")
            return redirect("/geasy/dashboard")


        except Exception as e:
            print("DB error during login:", e)
            flash("Internal error", "danger")
            return redirect(url_for("geasy_bp.admin_login"))

    return render_template("geasy/g_login.html")



@geasy_bp.route("/dashboard")
def admin_dashboard():
    print("admin_dashboard route triggered")  # <--- debug print
    print("session contents:", session)  # <--- debug print

    if not session.get("admin_logged_in"):
        flash("Please login first", "warning")
        return redirect(url_for("geasy_bp.admin_login"))

    return render_template("geasy/g_dashboard.html")

@geasy_bp.route('/logout')
def logout():
    session.clear()   
    return redirect(url_for("geasy_bp.admin_login"))




#DASHBOARD ROUTES

#APP USERS
@geasy_bp.route('/manage_users')
def manage_users():
    # Placeholder for user management logic
    return redirect(url_for('geasy_bp.manage_requests'))

#PENDING USERS
@geasy_bp.route("/manage/requests", methods=["GET"])
def manage_requests():
    search = request.args.get("search", "").strip()
    filter_status = request.args.get("status", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM pending_users WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE %s OR email LIKE %s OR login_id LIKE %s)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]

    if filter_status:
        query += " AND status = %s"
        params.append(filter_status)

    cursor.execute(query, tuple(params))
    users = cursor.fetchall()
    conn.close()

    return render_template("geasy/approve_requests.html", users=users, search=search, filter_status=filter_status)

# Approve Pending User
from geopy.geocoders import Nominatim
@geasy_bp.route("/manage/requests/approve", methods=["POST"])
def approve_pending_user():
    pending_id = request.form.get("pending_id")
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    role = request.form.get("role")
    status = request.form.get("status", "active")

    if not (login_id and password and role and pending_id):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # Fetch pending user
        cursor.execute("SELECT * FROM pending_users WHERE id = %s", (pending_id,))
        pending = cursor.fetchone()

        if not pending:
            return jsonify({"success": False, "message": "Pending user not found"}), 404

        # Reverse geocode coordinates to short address
        address = ""
        try:
            location_str = pending.get("location", "")
            if location_str:
                lat, lon = map(float, location_str.split(","))
                geolocator = Nominatim(user_agent="geasy-approver")
                location = geolocator.reverse((lat, lon), language='en')
                if location and location.raw and 'address' in location.raw:
                    addr = location.raw['address']
                    # Pick the most relevant short field
                    address = addr.get('neighbourhood') or \
                              addr.get('suburb') or \
                              addr.get('road') or \
                              addr.get('city_district') or \
                              addr.get('village') or \
                              addr.get('town') or \
                              addr.get('city') or ''
        except Exception as geo_err:
            print(f"Geocoding error: {geo_err}")
            address = ""

        # Insert into users table
        cursor.execute("""
            INSERT INTO users (
                name, email, password, role, login_id,
                mobile, mobile2, city, state, location,
                machine_id, status, address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            pending["name"],
            pending["email"],
            password,
            role,
            login_id,
            pending["mobile"],
            pending.get("mobile2", ""),
            pending["city"],
            pending["state"],
            pending["location"],
            pending.get("machine_id", ""),
            "active",
            address
        ))

        # Delete approved user from pending_users
        cursor.execute("DELETE FROM pending_users WHERE id = %s", (pending_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "User approved successfully",
            "login_id": login_id,
            "address": address
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        conn.close()

#Feych Location of Pending User
@geasy_bp.route("/manage/requests/location/<int:user_id>")
def view_location(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT location FROM pending_users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user and user["location"]:
        return jsonify({"success": True, "location": user["location"]})
    
    return jsonify({"success": False, "message": "Location not available"})

# Update User Status
@geasy_bp.route("/manage/requests/update-status", methods=["POST"])
def update_user_status():
    user_id = request.form.get("user_id")
    new_status = request.form.get("new_status")
    
    if not (user_id and new_status):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM pending_users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Update status and remark
        cursor.execute("""
            UPDATE pending_users 
            SET status = %s, remark = %s 
            WHERE id = %s
        """, (new_status, new_status, user_id))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Status updated successfully",
            "new_status": new_status
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

#EMPLOYEES ROUTES

# Manage Employees
@geasy_bp.route('/manage/employees', methods=['GET'])
def manage_employees():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        employees = cursor.fetchall()
    conn.close()
    
    print("DEBUG: Employees sent to template:", employees)  # Sanity check
    
    return render_template('geasy/employees.html', employees=employees)


#Fill the employee data for the DataTable
@geasy_bp.route("/manage/employees/data", methods=["POST"])
def manage_employees_data():
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 415

    data = request.get_json()
    search = data.get("search", "").strip()

    db = get_db_connection()
    cursor = db.cursor()
    query = """
        SELECT id, login_id, name, password, mobile, mobile2, status, address,
        FROM users
        WHERE name LIKE %s OR login_id LIKE %s
    """
    param = f"%{search}%"
    cursor.execute(query, (param, param))
    rows = cursor.fetchall()

    if not rows:
        return jsonify([])  # Empty list, handled on front-end

    columns = [desc[0] for desc in cursor.description]
    employees = [dict(zip(columns, row)) for row in rows]
    return jsonify(employees)

#Editing details of employee
@geasy_bp.route("/geasy/manage/employees/edit/<string:login_id>", methods=["GET", "POST"])
def edit_employee(login_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        new_login_id = request.form.get("login_id").strip()
        password = request.form.get("password").strip()
        name = request.form.get("name").strip()
        mobile = request.form.get("mobile").strip()
        mobile2 = request.form.get("mobile2").strip()
        status = request.form.get("status").strip()
        role = request.form.get("role").strip()

        # Update login_id too
        cursor.execute("""
            UPDATE users
            SET login_id = %s,
                password = %s,
                name = %s,
                mobile = %s,
                mobile2 = %s,
                status = %s,
                role = %s
            WHERE login_id = %s
        """, (new_login_id, password, name, mobile,mobile2, status, role, login_id))

        conn.commit()
        conn.close()
        flash("User updated successfully", "success")

        # Redirect using updated login_id to prevent confusion
        return redirect(url_for("geasy_bp.manage_employees"))

    # GET method – fetch user data
    cursor.execute("SELECT * FROM users WHERE login_id = %s", (login_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("geasy_bp.manage_employees"))

    return render_template("geasy/edit_employee.html", user=user)

# Delete Employee
@geasy_bp.route("/manage/employee/delete/<string:user_id>", methods=["POST"])
def delete_employee(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE login_id = %s", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("geasy_bp.manage_employees"))


#REPORTS ROUTES

@geasy_bp.route('/reports')
def reports():
    # Placeholder for reports logic
    return render_template("geasy/reports.html")   

@geasy_bp.route("/reports/monthly-recharge")
def monthly_recharge():
    return "Monthly Recharge Report"

# User App Search Report- Selects a date and a particular employee shows the car they accessed on that date
@geasy_bp.route("/reports/user-app-search", methods=["GET", "POST"])
def user_app_search():
    conn = get_db_connection()
    cursor = conn.cursor()  # Return results as dicts

    # Populate user dropdown
    cursor.execute("SELECT login_id, name, city, state FROM users ORDER BY login_id")
    users = cursor.fetchall()

    report = None
    selected_user = None
    selected_date = None

    if request.method == "POST":
        emp_id = request.form["emp_id"]
        search_date = request.form["search_date"]
        entire_month = request.form.get("entire_month")

        selected_user = emp_id
        selected_date = search_date

        if entire_month:
            query = """
                SELECT DATE(searched_at) AS search_day,
                       GROUP_CONCAT(chasis_no ORDER BY searched_at SEPARATOR ', ') AS chasis_no
                FROM car_search_logs
                WHERE emp_id = %s AND MONTH(searched_at) = MONTH(%s) AND YEAR(searched_at) = YEAR(%s)
                GROUP BY DATE(searched_at)
                ORDER BY search_day DESC
            """
            cursor.execute(query, (emp_id, search_date, search_date))
        else:
            query = """
                SELECT DATE(searched_at) AS search_day,
                       GROUP_CONCAT(chasis_no ORDER BY searched_at SEPARATOR ', ') AS chasis_no
                FROM car_search_logs
                WHERE emp_id = %s AND DATE(searched_at) = %s
                GROUP BY DATE(searched_at)
            """
            cursor.execute(query, (emp_id, search_date))

        report = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "geasy/user_app_search.html",
        users=users,
        report=report,
        selected_user=selected_user,
        selected_date=selected_date
    )


# All Users Search Report - Selects a month & year and shows all users who accessed cars on that date
@geasy_bp.route("/reports/all-users-search", methods=["GET", "POST"])
def all_users_search():
    conn = get_db_connection()
    cursor = conn.cursor()

    report = None
    selected_date = None
    entire_month = False

    if request.method == "POST":
        search_date = request.form["search_date"]
        entire_month = request.form.get("entire_month")
        selected_date = search_date

        if entire_month:
            query = """
                SELECT csl.emp_id,
                    csl.emp_name,
                    DATE(csl.searched_at) AS search_day,
                    GROUP_CONCAT(csl.chasis_no ORDER BY csl.searched_at SEPARATOR ', ') AS chasis_list,
                    MIN(csl.searched_at) AS first_search_time
                FROM car_search_logs csl
                WHERE MONTH(csl.searched_at) = MONTH(%s)
                AND YEAR(csl.searched_at) = YEAR(%s)
                GROUP BY csl.emp_id, csl.emp_name, DATE(csl.searched_at)
                HAVING chasis_list IS NOT NULL AND chasis_list != ''
                ORDER BY search_day DESC, csl.emp_id
            """
            cursor.execute(query, (search_date, search_date))

        else:
            query = """
                SELECT csl.emp_id,
                    csl.emp_name,
                    DATE(csl.searched_at) AS search_day,
                    GROUP_CONCAT(csl.chasis_no ORDER BY csl.searched_at SEPARATOR ', ') AS chasis_list,
                    MIN(csl.searched_at) AS first_search_time
                FROM car_search_logs csl
                WHERE DATE(csl.searched_at) = %s
                GROUP BY csl.emp_id, csl.emp_name, DATE(csl.searched_at)
                ORDER BY first_search_time DESC
            """
            cursor.execute(query, (search_date,))


        report = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("geasy/all_users_search.html", report=report, selected_date=selected_date, entire_month=entire_month)

# Search by Chassis Number Report - Selects a month & year and shows all users who searched for that number
@geasy_bp.route("/reports/number-search", methods=["GET", "POST"])
def report_by_number():
    report = []
    selected_date = None
    search_number = None
    month = year = ""

    if request.method == "POST":
        month = request.form.get("search_month")
        year = request.form.get("search_year")
        search_number = request.form.get("search_number", "").strip().upper()

        if not (month and year and search_number):
            flash("All fields are required.", "danger")
            return render_template("geasy/search_by_number.html", report=[], selected_date=None)

        if len(search_number) < 6:
            flash("Chassis number must be at least 6 characters.", "danger")
            return render_template("geasy/search_by_number.html", report=[], selected_date=None)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.emp_id AS login_id,
                e.name AS emp_name,
                DATE(csl.searched_at) AS search_date
            FROM car_search_logs csl
            JOIN employees e ON e.emp_id = csl.emp_id
            WHERE UPPER(csl.chasis_no) LIKE %s
              AND MONTH(csl.searched_at) = %s
              AND YEAR(csl.searched_at) = %s
            ORDER BY csl.searched_at DESC
        """
        search_like = f"%{search_number}%"
        print("Running query with:", search_like, month, year)
        cursor.execute(query, (search_like, int(month), int(year)))
        report = cursor.fetchall()
        print("Report rows:", report)  # ✅ Check this
        selected_date = f"{month}/{year}"

    return render_template("geasy/search_by_number.html",
                           report=report,
                           selected_date=selected_date,
                           search_number=search_number,
                           search_month=month,
                           search_year=year)




#LISTINGS ROUTES

@geasy_bp.route('/listings')
def listings():
    # Placeholder for listings logic
    return render_template("geasy/listings.html")

@geasy_bp.route("/listings/repulse")
def running_repulse():
    return "Running Repulse"

@geasy_bp.route("/listings/update-heading")
def update_list_heading():
    return "Update List Heading"

@geasy_bp.route("/listings/download")
def download_general():
    return "Download General Mobile"

@geasy_bp.route("/listings/mobile-add")
def mobile_add():
    return "Mobile Add"

@geasy_bp.route("/listings/add-xcs")
def add_new_xcs():
    return "Add New XCS"



#SETTINGS ROUTES

@geasy_bp.route('/settings')
def settings():
    # Placeholder for settings logic
    return render_template("geasy/settings.html")


#LOCATION ROUTES

@geasy_bp.route('/location')
def location():
    # Placeholder for location logic
    return render_template("geasy/location.html")

     