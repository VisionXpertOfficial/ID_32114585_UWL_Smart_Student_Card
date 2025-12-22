#!/usr/bin/env python3
import argparse, os, json
import pandas as pd
from collections import Counter
from math import sqrt

def detect_input_dir(user_dir: str | None):
    if user_dir and os.path.isdir(user_dir):
        return user_dir
    candidates = [
        "/kaggle/input/elliptic-data-set/elliptic_bitcoin_dataset",
        "elliptic_bitcoin_dataset",
        "./elliptic_bitcoin_dataset",
        os.getcwd(),
    ]
    for p in candidates:
        if all(os.path.isfile(os.path.join(p, f)) for f in [
            "elliptic_txs_features.csv",
            "elliptic_txs_classes.csv",
            "elliptic_txs_edgelist.csv"
        ]):
            return p
    raise FileNotFoundError("Could not find the three Elliptic CSVs. Use --in-dir to set the folder.")

def feature_columns():
    colNames1 = {0: "txId", 1: "Time step"}
    colNames2 = {i: f"local_{i-1}" for i in range(2, 95)}
    colNames3 = {i: f"agg_{i-94}" for i in range(95, 167)}
    return {**colNames1, **colNames2, **colNames3}

def compute_class_weights(y_series: pd.Series):
    counts = Counter(y_series.tolist())
    total = sum(counts.values())
    # simple inverse frequency normalized to mean=1.0
    weights = {cls: (total / (len(counts) * cnt)) for cls, cnt in counts.items()}
    return weights, counts

def balance_df(df_sup: pd.DataFrame, method: str):
    # expects columns: ['label', features...]
    if method == "none":
        return df_sup
    maj = df_sup[df_sup["label"] == 0]
    mino = df_sup[df_sup["label"] == 1]
    if method == "undersample":
        maj_sampled = maj.sample(n=len(mino), random_state=42, replace=False)
        return pd.concat([maj_sampled, mino], axis=0).sample(frac=1, random_state=42).reset_index(drop=True)
    if method == "oversample":
        mino_sampled = mino.sample(n=len(maj), random_state=42, replace=True)
        return pd.concat([maj, mino_sampled], axis=0).sample(frac=1, random_state=42).reset_index(drop=True)
    return df_sup

def main():
    ap = argparse.ArgumentParser(description="Create ONE clean CSV from Elliptic dataset.")
    ap.add_argument("--in-dir", type=str, default=None)
    ap.add_argument("--out-dir", type=str, default="elliptic_onefile")
    ap.add_argument("--include-unknown", action="store_true", help="Include class 3 with label=-1")
    ap.add_argument("--balance", choices=["none","undersample","oversample"], default="none", help="Class-imbalance handling for supervised rows")
    args = ap.parse_args()

    in_dir = detect_input_dir(args.in_dir)
    os.makedirs(args.out_dir, exist_ok=True)

    # Load
    df_c = pd.read_csv(os.path.join(in_dir, "elliptic_txs_classes.csv"))
    df_c["class"] = df_c["class"].replace({"unknown":3,"1":1,"2":2}).astype(int)
    df_f = pd.read_csv(os.path.join(in_dir, "elliptic_txs_features.csv"), header=None).rename(columns=feature_columns())

    # Merge
    df = pd.merge(df_c, df_f, on="txId", how="inner")

    # Supervised mapping
    sup = df[df["class"].isin([1,2])].copy()
    sup["label"] = sup["class"].map({1:1, 2:0}).astype(int)
    sup = sup.drop(columns=["class"])

    # Compute class weights on supervised set
    weights, counts = compute_class_weights(sup["label"])

    # Optional balancing
    sup_bal = balance_df(sup, args.balance)

    # Unknown
    if args.include_unknown:
        unk = df[df["class"]==3].copy()
        unk["label"] = -1
        unk = unk.drop(columns=["class"])
        out_df = pd.concat([sup_bal, unk], axis=0, ignore_index=True)
    else:
        out_df = sup_bal

    # Reorder cols: txId,label,Time step,features...
    cols = ["txId","label","Time step"] + [c for c in out_df.columns if c not in ["txId","label","Time step"]]
    out_df = out_df[cols]

    # Save ONE file + weights
    out_csv = os.path.join(args.out_dir, "elliptic_clean.csv")
    out_df.to_csv(out_csv, index=False)

    with open(os.path.join(args.out_dir, "class_weights.json"), "w") as f:
        json.dump({"weights": weights, "counts": {int(k): int(v) for k,v in counts.items()}}, f, indent=2)

    # Minimal report
    print(json.dumps({
        "input_dir": in_dir,
        "rows": len(out_df),
        "supervised_rows_after_balance": int(len(sup_bal)),
        "included_unknown": bool(args.include_unknown),
        "balance": args.balance,
        "class_counts_supervised": {int(k): int(v) for k,v in counts.items()},
        "class_weights": weights,
        "output_csv": out_csv
    }, indent=2))

if __name__ == "__main__":
    main()
