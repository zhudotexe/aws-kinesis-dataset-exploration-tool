#!/usr/bin/env python
"""This script will run logistic regression on a training dataset and output 
training and validation metrics, and predictions for an unlabeled dataset."""
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
from sklearn import preprocessing
from sklearn.metrics import f1_score, accuracy_score, classification_report
parser = argparse.ArgumentParser(description="Fits a Logistic Regression model and predicts labels for a dataset")
parser.add_argument("train", help="csv file with training dataset")
parser.add_argument("unlabeled", help="csv file with unlabeled dataset")
parser.add_argument("--train_out", type=str, \
    help="output file for training metrics", default="train_metrics.txt") #TODO: Change to separate train and val files
parser.add_argument("--val_out", type=str, \
    help="output file", default="val_metrics.txt")
parser.add_argument("--predictions_base", \
    help="prefix for files to output predictions", default="predictions")
# parser.add_argument("--train_predictions_base", \
    # help="prefix for files to output predictions on training set", default="X_pred.csv")
parser.add_argument("--classifier", help="classifier to use", default="log_reg", choices=["log_reg", "svm","naive_bayes"])
parser.add_argument("--penalty", help="penalty for the model", default="l2")
parser.add_argument("--Cs", \
    help="values to test for C, the inverse strength of regularization", default=[.01,.1,1,10,100])
parser.add_argument("--class_weight", \
    help="class weight for logisitic regression", default='balanced')
parser.add_argument("--metric", type=str, \
    help="Evaluation metric", default="f1", choices=["f1","accuracy"])
parser.add_argument("--splits", help="number of splits to use for cross-validation, -1 for leave-one-out", default=5)
args = parser.parse_args()

def main(args):
    # Data Loading 
    data = pd.read_csv(args.train, header=0, index_col=0)
    targets = ["RP to CMD", "CMD to NARR", "RP to CMD or CMD to NARR", "RP to CMD and CMD to NARR"]
    X = data.drop(targets, axis=1)
    splits = len(X) if args.splits == -1 else args.splits
    kf = StratifiedKFold(shuffle=True, random_state=23, n_splits=splits)
    ys = {target : data[target] for target in targets}
    if args.classifier in ["log_reg", "svm"]:
        best_Cs = {}
        val_scores = {target : {C : [] for C in args.Cs} for target in targets} 
    else: # for classifiers without a C parameter
        val_scores = {target : [] for target in targets}
    scaler = preprocessing.StandardScaler().fit(X)
    X_scaled = scaler.transform(X)
    metric = f1_score if args.metric == "f1" else accuracy_score
    # Run K-Fold CV, tracking total validation predictions and labels
    y_val_total = {target : [] for target in targets}
    y_val_pred_total = {target : [] for target in targets}
    for target in targets:
        for train_index, val_index in kf.split(X, ys[target]):
            X_train, X_val = X.iloc[train_index], X.iloc[val_index]
            scaler = preprocessing.StandardScaler().fit(X_train)
            X_train_scaled = scaler.transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            y_train = ys[target].iloc[train_index]
            y_val = ys[target].iloc[val_index]
            if args.classifier in ["log_reg", "svm"]:
                for C in args.Cs:
                    if args.classifier == "log_reg":
                        model = LogisticRegression(C=C, class_weight=args.class_weight, \
                            penalty=args.penalty).fit(X_train_scaled, y_train)
                    elif args.classifier == "svm":
                        model = SVC(C=C, class_weight=args.class_weight, \
                            kernel='linear').fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_val_scaled)
                    y_val_total[target] += y_val.tolist()
                    y_val_pred_total[target] += y_pred.toList()
                    val_scores[target][C].append(metric(y_val, y_pred))
            elif args.classifier == "naive_bayes":
                model = GaussianNB().fit(X_train_scaled, y_train)
                y_pred = model.predict(X_val_scaled)
                y_val_total[target] += y_val.tolist()
                y_val_pred_total[target] += y_pred.tolist()
                val_scores[target].append(metric(y_val, y_pred))

                

    # Find best C for each target by mean validation accuracy
    y_val_total = {target : pd.DataFrame(y_val_total[target]).fillna(-1) for target in targets}
    y_val_pred_total = {target : pd.DataFrame(y_val_pred_total[target]).fillna(-1) for target in targets}
    for target in targets:
        print(len(y_val_total[target]))
        print(len(y_val_pred_total[target]))
    with open(args.classifier+"_"+args.val_out, 'w') as f:
        for target in targets:
            best_val_report = classification_report(y_val_total[target], y_val_pred_total[target])
            f.write("Validation Report for "+target+":\n")
            f.write(best_val_report)
            best_val_score = 0
            if args.classifier in ["log_reg", "svm"]:
                for C in args.Cs:
                    t_val_score = np.mean(val_scores[target]) if args.classifier == 'naive_bayes' else np.mean(val_scores[target][C])
                    if t_val_score > best_val_score:
                        best_C = C
                        best_val_score = t_val_score
                        best_Cs[target] = best_C
                        # f.write("Best C for {} is {} with mean {} score of {}\n".format(target, best_C, args.metric, best_val_score))
           
          
    # Run Logistic Regression over the whole dataset with selected C values
    full = pd.read_csv(args.unlabeled, header=0, index_col=0)
    X_full = full.copy()
    scaler = scaler.fit(X_full)
    X_full_scaled = scaler.transform(X_full)
    with open(args.classifier+"_"+args.train_out, 'w') as f:
        for target in targets:
            if args.classifier == "log_reg":
                model = LogisticRegression(C=best_Cs[target], class_weight=args.class_weight, \
                    penalty=args.penalty).fit(X_scaled, ys[target])
            elif args.classifier == "svm":
                model = SVC(C=best_Cs[target], class_weight=args.class_weight, \
                    kernel='linear').fit(X_scaled, ys[target])
            elif args.classifier == "naive_bayes":
                model = GaussianNB().fit(X_scaled, ys[target])
            full[f"{target}_pred"] = model.predict(X_full_scaled)
            if args.classifier != "svm":
                full[f"{target}_pred_prob"] = model.predict_proba(X_full_scaled)[:,1]
                out = full[[f"{target}_pred",f"{target}_pred_prob"]]
            else:
                out = full[[f"{target}_pred"]]
            out.to_csv(args.classifier+"_"+args.predictions_base+f"_{target}.csv")
            f.write(f"Train {args.metric} score for {target}: {metric(model.predict(X_scaled),ys[target])}\n")
            f.write(classification_report(model.predict(X_scaled),ys[target]))
if __name__ == "__main__":
    main(args)
    # log validation metrics, add F1, metrics for each class DONE
    # try class weights DONE, improved F1
    # stratified k-fold DONE
    # output list of instance ids DONE
    # Automate train data generation
    # Try SVM, NaiveBayes DONE
    # PCA?
