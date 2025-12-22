import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump

rng = np.random.default_rng(42)

n = 800
normal = pd.DataFrame({
    'hour': rng.integers(7, 22, size=n),
    'dist_km': rng.normal(2, 1, size=n).clip(0, 50),
    'fail_cnt': rng.poisson(0.3, size=n),
    'device_change': rng.binomial(1, 0.05, size=n)
})

anoms = pd.DataFrame({
    'hour': rng.integers(0, 24, size=40),
    'dist_km': rng.normal(500, 80, size=40),
    'fail_cnt': rng.poisson(5, size=40),
    'device_change': 1
})

X = pd.concat([normal, anoms], ignore_index=True)

model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
model.fit(X)

dump(model, 'model.joblib')
print('saved model.joblib; features:', list(X.columns))
