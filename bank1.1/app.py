import os, uuid, json, requests
from decimal import Decimal, ROUND_DOWN
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG, GATEWAY_MODE, SIMULATOR_URL, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def money_round(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account_no = request.form.get("account_no", "").strip()
        password = request.form.get("password", "")
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        try:
            cur.execute("SELECT * FROM users WHERE account_no=%s", (account_no,))
            user = cur.fetchone()

            if user and check_password_hash(user['password'], password):
                # Correction: Changed 'account_np' to 'account_no'
                session['user'] = {
                    "id": user['id'],
                    "account_no": user['account_no'],
                    "email": user["email"],
                    "username": user["username"]
                }
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid account number or password. Please try again.", "danger")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        account_no = request.form.get("account_no", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password","")
        balance = request.form.get("balance", "0") or "0"

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        try:
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html")
            
            hashed_password = generate_password_hash(password)
            
            cur.execute("SELECT * FROM users WHERE account_no=%s OR email=%s", (account_no, email))
            existing_user = cur.fetchone()
            if existing_user:
                flash("An account with this account number or email already exists.", "danger")
                return render_template("register.html")
            
            cur.execute(
                "INSERT INTO users (username, account_no, email, password, balance) VALUES (%s, %s, %s, %s, %s)",
                (username, account_no, email, hashed_password, balance)
            )
            conn.commit()
            
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f"An error occurred during registration: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        account_no = request.form.get("account_no", "").strip()
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", ""),
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("Password do not match", "danger")
            return redirect(url_for("forgot_password"))
        if len(new_password) < 6:
            flash("Password must be at least 6 chars", "danger")
            return redirect(url_for("forgot_password"))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE account_np=%s AND email=%s", (account_no, email))
        if not cur.fetchone():
            cur.close()
            conn.close()
            flash("Account with this email not found", "danger")
            return redirect(url_for("forgot_password"))
        
        cur.execute("UPDATE users SET password=%s WHERE account_no=%s AND email=%s", (generate_password_hash(new_password), account_no, email))
        conn.commit()
        cur.close()
        conn.close()

        flash("Password reset, please login", "success")
        return redirect(url_for('login'))
    return render_template("forgot_passowrd.html")


@app.route("/logout")
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to view the dashboard.", "info")
        return redirect(url_for("login"))
    user = session['user']
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT * FROM users WHERE account_no = %s", (user['account_no'],))
        db_user = cur.fetchone()

        if db_user:
            session['user']['balance'] = db_user['balance']
        
        cur.execute("SELECT * FROM transactions WHERE from_account=%s OR to_account=%s ORDER BY timestamp DESC LIMIT 5",(user['account_no'], user['account_no']))
        transactions = cur.fetchall()
        
        return render_template("dashboard.html", user=session['user'], transactions=transactions)
    
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('login'))
    finally:
        cur.close()
        conn.close()



@app.route("/transaction", methods=["GET","POST"])
def transactions():
    if 'user' not in session:
        flash("Please log in to perform transactions. ", "info")
        return redirect(url_for("login"))
    
    user = session['user']
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    

    if request.method == "POST":
        
        to_account = request.form.get("to_account", "").strip()
        amount = Decimal(request.form.get("amount", "0"))
        try:
            cur.execute("SELECT balanec FROM users WHERE account_np=%s", (user['account_no'],))
            current_balance = cur.fetchall()['balance']

            if current_balance < amount:
                flash("Insufficient balance.", "danger")
                return redirect(url_for('transactions'))
            
            cur.execute("UPDATE users SET balance = balance - %s WHERE account_no=%s", (amount, user['account_np']))
            cur.execute("UPDATE users SET balance = balance + %s WHERE account_no=%s", (amount, to_account))

            cur.execute(
                "INSERT INTO transactions (transaction_id, from_account, to_account, amount, note) VALUES (%s, %s, %s, %s, %s)", 
                (str(uuid.uuid4()), user['account_no'], to_account, amount,"Internal Transfer")
            )
            conn.commit()
            flash("Transfer successful!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"An error occured: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('dashboard'))

        
    cur.execute("SELECT * FROM transactions WHERE from_account=%s OR to_account=%s BRDER BY timestamp DESC",
                (user['account_no'], user['account_no']))
    transactions = cur.fetchall()
    cur.close()
    conn.close()

    
    return render_template("transaction.html", transactions=transactions)

@app.route("/interbank_transfer", methods=["POST"])
def interbank_transfer():
    if 'user' not in session:
        flash("Please log in to perform transactions.", "info")
        return redirect(url_for('login'))
    
    user = session['user']
    data = request.form
    beneficiary_account = data.get("beneficiary_account")
    amount_str = data.get("amount")
    
    if not amount_str:
        flash("Amount is required.", "danger")
        return redirect(url_for('transactions'))

    amount = money_round(amount_str)

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT balance FROM users WHERE account_no=%s", (user['account_no'],))
        current_balance = cur.fetchone()['balance']
        
        if current_balance < amount:
            flash("Insufficient balance.", "danger")
            return redirect(url_for('transactions'))

        transfer_ref = str(uuid.uuid4())
        
        
        cur.execute(
            "INSERT INTO money_transfer_record (transfer_ref, from_account, to_account, amount, status) VALUES (%s, %s, %s, %s, %s)",
            (transfer_ref, user['account_no'], beneficiary_account, amount, "PENDING")
        )
        
        
        cur.execute("UPDATE users SET balance = balance - %s WHERE account_no=%s", (amount, user['account_no']))
        conn.commit()

        gateway_payload = {
            "transfer_ref": transfer_ref,
            "amount": float(amount),
            "callback_url": url_for('gateway_callback', _external=True)
        }
        
        
        if GATEWAY_MODE == "SIMULATOR":
            requests.post(f"{SIMULATOR_URL}/api/initiate_transfer", json=gateway_payload)
            flash("Interbank transfer initiated. Awaiting confirmation from gateway.", "info")
        else:
            flash("Interbank transfers are currently in SIMULATOR mode.", "info")
            
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred during transfer: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('dashboard'))



# @app.route("/transfer/interbank", methods=["POST"])
# def interbank_transfer():
#     if "user" not in session: return redirect(url_for("login"))
#     from_acc = session["user"]["account_no"]
#     beneficiary_account = request.form.get("beneficiary_account", "").strip()
#     beneficiary_ifsc = request.form.get("beneficiary_ifsc", "").strip()
#     beneficiary_bank = request.form.get("beneficiary_bank", "").strip()
#     try:
#         amount = money_round(request.form.get("amount", "0"))
#     except Exception:
#         flash("Invalid amount", "danger"); return redirect(url_for("dashboard"))
#     if amount <= 0:
#         flash("Amount must be positive", "danger"); return redirect(url_for("dashboard"))

#     transfer_ref = str(uuid.uuid4())
#     conn = get_db(); cur = conn.cursor(dictionary=True)
#     try:
#         cur.execute("SELECT * FROM users WHERE account_no=%s FOR UPDATE", (from_acc,))
#         sender = cur.fetchone()
#         if Decimal(sender["balance"]) < amount:
#             flash("Insufficient funds", "danger")
#             cur.close(); conn.close(); return redirect(url_for("dashboard"))

#         # debit temporarily
#         cur.execute("UPDATE users SET balance=%s WHERE account_no=%s",
#                     (str(money_round(Decimal(sender["balance"]) - amount)), from_acc))
#         cur.execute("INSERT INTO money_transfer_record (transfer_ref, from_account, beneficiary_account, beneficiary_ifsc, beneficiary_bank, amount, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
#                     (transfer_ref, from_acc, beneficiary_account, beneficiary_ifsc, beneficiary_bank, str(amount), "PENDING"))
#         conn.commit()
#     except Exception as e:
#         conn.rollback(); flash("Failed to initiate transfer: "+str(e), "danger")
#         cur.close(); conn.close(); return redirect(url_for("dashboard"))
#     finally:
#         cur.close(); conn.close()

#     # Call simulator
#     try:
#         requests.post(SIMULATOR_URL + "/api/initiate_transfer", json={
#             "transfer_ref": transfer_ref,
#             "amount": str(amount),
#             "callback_url": request.url_root + "gateway/callback"
#         }, timeout=5)
#         flash("Transfer initiated via simulator. Ref: " + transfer_ref, "info")
#     except Exception as e:
#         # Refund
#         conn2 = get_db(); cur2 = conn2.cursor()
#         cur2.execute("UPDATE users SET balance = balance + %s WHERE account_no=%s", (str(amount), from_acc))
#         cur2.execute("UPDATE money_transfer_record SET status=%s, gateway_response=%s WHERE transfer_ref=%s",
#                      ("FAILED", json.dumps({"error": str(e)}), transfer_ref))
#         conn2.commit(); cur2.close(); conn2.close()
#         flash("Simulator unreachable, refunded", "danger")
#     return redirect(url_for("dashboard"))

@app.route("/gateway/callback", methods=["POST"])
def gateway_callback():
    data = request.get_json(force=True)
    transfer_ref = data.get("transfer_ref")
    status = data.get("status")
    gateway_id = data.get("gateway_id", "")

    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM money_transfer_record WHERE transfer_ref=%s FOR UPDATE", (transfer_ref,))
        rec = cur.fetchone()
        if not rec:
            cur.close(); conn.close(); return jsonify({"error":"not_found"}), 404
        if rec["status"] in ("SUCCESS","FAILED","REVERSED"):
            cur.close(); conn.close(); return jsonify({"ok":"duplicate"}), 200

        if status == "SUCCESS":
            cur.execute("UPDATE money_transfer_record SET status=%s, gateway_response=%s WHERE transfer_ref=%s",
                        ("SUCCESS", json.dumps(data), transfer_ref))
            conn.commit()
        else:
            # refund
            cur.execute("UPDATE users SET balance = balance + %s WHERE account_no=%s",
                        (str(rec["amount"]), rec["from_account"]))
            cur.execute("UPDATE money_transfer_record SET status=%s, gateway_response=%s WHERE transfer_ref=%s",
                        ("FAILED", json.dumps(data), transfer_ref))
            cur.execute("INSERT INTO transactions (transaction_id, from_account, to_account, amount, note) VALUES (%s,%s,%s,%s,%s)",
                        (str(uuid.uuid4()), rec["from_account"], rec["from_account"], str(rec["amount"]), "Refund for failed interbank"))
            conn.commit()
        cur.close(); conn.close()
        return jsonify({"ok": True}), 200
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
