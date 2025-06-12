from flask import Flask, jsonify
from bsedata.bse import BSE
from threading import Thread
from datetime import datetime
import time

app = Flask(__name__)
bse = BSE(update_codes=True)

# Global in-memory storage
all_stock_data = {}
last_updated = None

def is_market_open():
    now = datetime.now()
    # Market open: Mon–Fri, 9:15 AM – 3:30 PM IST
    return (
        now.weekday() < 5 and
        (now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and
        (now.hour < 15 or (now.hour == 15 and now.minute <= 30))
    )

def fetch_stock_data():
    global all_stock_data, last_updated

    def fetch_once():
        global all_stock_data, last_updated
        print("🔁 Fetching stock data...")
        try:
            print('hello')
            stocks = bse.getScripCodes()
            for i, (code, name) in enumerate(stocks.items(), start=1):
                print(stocks[500002])
                try:
                    quote = bse.getQuote(code)
                    if 'currentValue' not in quote:
                        continue
                    all_stock_data[code] = {
                        'code': code,
                        'name': name,
                        'currentValue': quote['currentValue'],
                        'previousClose': quote['previousClose'],
                        'change': quote['change'],
                        'pChange': quote['pChange'],
                        'updatedAt': datetime.now().isoformat()
                    }
                    if i % 100 == 0:
                        print(f"✅ Fetched {i} stocks so far...")
                except Exception as e:
                    print(f"❌ Error fetching {code}: {e}")
            last_updated = datetime.now().isoformat()
            print(f"✅ Finished fetching {len(all_stock_data)} stocks.")
        except Exception as e:
            print(f"⚠️ Initial fetch error: {e}")

    # 🔹 Run one-time fetch immediately at startup
    fetch_once()

    # 🔁 Loop to refresh data periodically when market is open
    while True:
        if is_market_open():
            print("⏳ Market open — updating data...")
            fetch_once()
        else:
            print("📴 Market closed — keeping old data.")
        time.sleep(120)  # Wait 5 minutes

# API Endpoints

@app.route('/')
def home():
    return (
        "📈 <b>BSE Live Stock API is running</b><br>"
        "Use <code>/all-stocks</code> to get all data<br>"
        "Use <code>/stock/&lt;code&gt;</code> to get specific stock"
    )

@app.route('/all-stocks', methods=['GET'])
def get_all_stocks():
    if not all_stock_data:
        return jsonify({"message": "Data not yet available. Please wait."}), 503
    return jsonify({
        "lastUpdated": last_updated,
        "totalStocks": len(all_stock_data),
        "data": all_stock_data
    })

@app.route('/stock/<code>', methods=['GET'])
def get_stock_by_code(code):
    stock = all_stock_data.get(code)
    if stock:
        return jsonify(stock)
    return jsonify({"error": "Stock code not found"}), 404

# Run the app
if __name__ == '__main__':
    fetch_thread = Thread(target=fetch_stock_data, daemon=True)
    fetch_thread.start()

    app.run(host='0.0.0.0', port=5000)
