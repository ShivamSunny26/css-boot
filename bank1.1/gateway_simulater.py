from flask import Flask, request, jsonify, render_template, redirect
import threading, time, random, requests

app = Flask(__name__)

#in memory storage of transfer
transfers = {}
@app.route("/")
def home():
    return render_template("simulator_dashboard.html", transfers=transfers)

@app.route("/api/initiate_transfer", methods=["POST"])
def initiate_transfer():
    """
    Called by banking app when initialing inter bank tranfer.
    Expects JSON: {transfer_ref, amount, callback_url}
    """

    data = request.get_json(force=True)
    transfer_ref = data.get("transfer_ref")
    amount = data.get("amount")
    callback_url = data.get("callback_url")

    if not transfer_ref or not callback_url:
        return jsonify({"error": "Missing fields"}), 400
    
    gateway_id = f"SIM-{transfer_ref[:8]}"
    transfers[transfer_ref] = {
        "gateway_id": gateway_id,
        "amount": amount,
        "callback_url": callback_url,
        "status": "PENDING"
    }

    # Auto-mode
    def process():
        time.sleep(random.uniform(2,5))
        status = random.choice(['SUCCESS', "FAILED"])
        if transfers[transfer_ref]['status'] == "PENDING":
            transfers[transfer_ref]["status"] = status
            payload = {
                "transfer_ref": transfer_ref,
                "gateway_id": gateway_id,
                "status": status
            }
            try:
                requests.post(callback_url, json=payload, timeout=5)
                print(f"[SIM] Auto Callback sent: {transfer_ref} => {status}")
            except Exception as e:
                print("Simulator callback failed: ", e)

    threading.Thread(target=process, daemon=True).start()
    return jsonify({
        "status": "ACCEPTED", "gateway_id": gateway_id}), 200


@app.route("/manual/<tranfer_ref>/<action>")
def maual_action(transfer_ref, action):
    if transfer_ref not in transfers:
        return "Transfer not found", 404
    status = "SUCCESS" if action == "approve" else "Failed"
    transfers[transfer_ref]['status'] = status

    payload = {
        "transfer_ref": transfer_ref,
        "gateway_id": transfers[transfer_ref]["gateway_id"],
        "status": status
    }

    try:
        requests.post(transfers[transfer_ref]["callback_url"], json=payload, timeout=5)
        print(f"[SIM] MAnual override sent: {transfer_ref} => {status}")
    except Exception as e:
        print("Simulator manual callback failed: ",e)
    return redirect("/")

if __name__ == "__main__":
    app.run(port=6000, debug=True)