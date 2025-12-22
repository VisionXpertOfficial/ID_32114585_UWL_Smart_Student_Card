from flask import Flask, request, jsonify
from joblib import load
import numpy as np

app = Flask(__name__)
model = load('model.joblib')

@app.get('/health')
def health():
    return jsonify(ok=True)

@app.post('/predict')
def predict():
    data = request.get_json(force=True) or {}
    feats = ['hour','dist_km','fail_cnt','device_change']
    x = np.array([[float(data.get(k, 0)) for k in feats]])
    score = model.decision_function(x)[0]  # higher = more normal
    anomaly = model.predict(x)[0] == -1
    return jsonify(ok=True, anomaly=bool(anomaly), score=float(score))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
    
