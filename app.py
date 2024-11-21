from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "VercelでデプロイされたFlaskアプリ！"

@app.route('/api', methods=['GET'])
def api():
    return jsonify({"message": "Hello from Vercel!"})

if __name__ == "__main__":
    app.run(debug=True)
