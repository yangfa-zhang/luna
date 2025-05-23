from .base_model import BaseModel
from typing import Union, Optional, List, Dict
import pandas as pd
import numpy as np
from tabulate import tabulate
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import (
    root_mean_squared_error, r2_score, mean_squared_error, mean_absolute_error,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

# 交叉验证训练
def _cross_validate(model: BaseModel, X: pd.DataFrame, y: pd.Series, k_fold: int, 
                   is_classifier: bool = False) -> None:
    """
    执行k折交叉验证
    
    参数：
        model: 模型实例
        X: 特征数据
        y: 目标变量
        k_fold: 交叉验证折数
        is_classifier: 是否为分类模型
    """
    # 选择合适的交叉验证方式
    if is_classifier:
        kf = StratifiedKFold(n_splits=k_fold, shuffle=True, random_state=42)
        split_data = kf.split(X, y)
    else:
        kf = KFold(n_splits=k_fold, shuffle=True, random_state=42)
        split_data = kf.split(X)
        
    fold_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(split_data, 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        if is_classifier:
            acc = accuracy_score(y_val, y_pred)
            f1 = f1_score(y_val, y_pred, average='weighted')
            fold_scores.append({'accuracy': acc, 'f1': f1})
            print(f"[lunax]> Fold {fold}/{k_fold} - Accuracy: {acc:.4f}, F1: {f1:.4f}")
        else:
            mse = mean_squared_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)
            fold_scores.append({'mse': mse, 'r2': r2})
            print(f"[lunax]> Fold {fold}/{k_fold} - MSE: {mse:.4f}, R2: {r2:.4f}")
    
    # 计算平均分数
    if is_classifier:
        avg_acc = np.mean([score['accuracy'] for score in fold_scores])
        avg_f1 = np.mean([score['f1'] for score in fold_scores])
        print(f"[lunax]> Average scores - Accuracy: {avg_acc:.4f}, F1: {avg_f1:.4f}")
    else:
        avg_mse = np.mean([score['mse'] for score in fold_scores])
        avg_r2 = np.mean([score['r2'] for score in fold_scores])
        print(f"[lunax]> Average scores - MSE: {avg_mse:.4f}, R2: {avg_r2:.4f}")

def reg_evaluate(y_true: pd.Series, y_pred: np.ndarray, log_info: bool = True) -> Dict[str, float]:
    """
    回归模型评估
    
    参数：
        y_true: 真实值
        y_pred: 预测值
    返回：
        包含评估指标的字典
    """
    # 计算评估指标
    rmse = root_mean_squared_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    if log_info:
        # 打印目标值的范围信息
        print("[lunax]> target value description:")
        stats_table = [["min", "max", "mean", "std", "median"],
                    [f"{y_true.min():.2f}", f"{y_true.max():.2f}", f"{y_true.mean():.2f}", 
                    f"{y_true.std():.2f}", f"{y_true.median():.2f}"]]
        print(tabulate(stats_table, headers="firstrow", tablefmt="grid"))
        # 打印评估结果
        print("[lunax]> model evaluation results:")
        metrics_table = [["metrics", "rmse", "mse", "mae", "r2"],
                        ["values", f"{rmse:.2f}", f"{mse:.2f}", f"{mae:.2f}", f"{r2:.2f}"]]
        print(tabulate(metrics_table, headers="firstrow", tablefmt="grid"))
    
    return {
        "rmse": rmse,
        "mse": mse,
        "mae": mae,
        "r2": r2
    }

def clf_evaluate(y_true: pd.Series, y_pred: np.ndarray, y_pred_proba: Optional[np.ndarray] = None, 
                log_info: bool = True) -> Dict[str, float]:
    """
    分类模型评估
    
    参数：
        y_true: 真实标签
        y_pred: 预测标签
        y_pred_proba: 预测概率，用于计算 AUC
        log_info: 是否打印评估信息
    返回：
        包含评估指标的字典
    """
    # 计算评估指标
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    # 计算 AUC
    auc = None
    if y_pred_proba is not None:
        try:
            # 对于二分类问题
            if y_pred_proba.shape[1] == 2:
                auc = roc_auc_score(y_true, y_pred_proba[:, 1])
            # 对于多分类问题
            else:
                auc = roc_auc_score(y_true, y_pred_proba, multi_class='ovr', average='weighted')
        except:
            auc = None
    
    if log_info:
        # 打印标签信息
        print("[lunax]> label information:")
        class_dist_table = [["label", "count"]]
        for label, count in y_true.value_counts().items():
            class_dist_table.append([label, count])
        print(tabulate(class_dist_table, headers="firstrow", tablefmt="grid"))
        # 打印评估结果
        print("[lunax]> model evaluation results:")
        metrics = ["metrics", "accuracy", "precision", "recall", "f1"]
        values = ["values", f"{accuracy:.2f}", f"{precision:.2f}", f"{recall:.2f}", f"{f1:.2f}"]
        
        if auc is not None:
            metrics.append("auc")
            values.append(f"{auc:.2f}")
            
        metrics_table = [metrics, values]
        print(tabulate(metrics_table, headers="firstrow", tablefmt="grid"))
    
    result = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
    
    if auc is not None:
        result["auc"] = auc
        
    return result
