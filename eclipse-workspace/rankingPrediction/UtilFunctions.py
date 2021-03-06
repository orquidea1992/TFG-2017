import operator
from RecMvRepl import RecMvRepl
import pandas as pd
from time import time
from sklearn.model_selection import train_test_split
from statistics import mean

def compute_accMargin(y_pred, y_test):
    multi_samples = type(y_pred) == type(pd.DataFrame())
            
    if multi_samples:
        df_diff = abs(y_pred - y_test)
        n_match = (df_diff<=2).sum().sum()
        length = y_pred.shape[0] * y_pred.shape[1]
        accuracy = n_match / float(length)
        return accuracy
    
    else:
        diff = abs(y_pred-y_test)
        n_match = (diff<=2).sum()
        return n_match
    
    
def compute_accuracy(y_pred, y_test): 
    multi_samples = type(y_pred) == type(pd.DataFrame())
            
    if multi_samples:      
        df_diff = abs(y_pred - y_test)
        n_match = (df_diff==0).sum().sum()
        length = y_pred.shape[0] * y_pred.shape[1]
        accuracy = n_match / float(length)
        return accuracy
    
    else:
        diff = abs(y_pred-y_test)
        n_match = (diff==0).sum()
        return n_match
    

def compute_mae(y_pred, y_test):
    multi_samples = type(y_pred) == type(pd.DataFrame())
            
    if multi_samples:        
        df_diff = abs(y_pred-y_test)
        error = df_diff.sum().sum()
        length = df_diff.shape[0] * df_diff.shape[1]
        mae = error / float(length)
        return mae
    
    else:
        diff = abs(y_pred-y_test)
        error = diff.sum()
        return error


def compute_std(y_pred, y_test):
    multi_samples = type(y_pred) == type(pd.DataFrame())
            
    if multi_samples:        
        return 0
    else:
        return 0

#===============================================================================
# Calculo de la puntuancion de cross validation
# clf: BaseEstimator, el clasificador
# X: DataFrame, data
# y: DataFrame, target
# kf: Kfold, iterador de cross validation
#===============================================================================
def cross_validation(clf, X, y, kf, qual=False, keepMv=False):
    yPair_list = []
    splits = kf.split(X)
    
    t0 = time()
    for i, index in enumerate(splits):
        print("Fold", i)
        
        train_index = index[0]
        test_index = index[1]
    
        clf.fit(X.iloc[train_index], y.iloc[train_index])
        
        X_test = X.iloc[test_index]
        y_pred = clf.predict(X_test)
        y_test = y.iloc[test_index]  
        
        if qual and not keepMv:
            y_test = score2ranking(y_test)
            
        yPair_list.append((y_pred, y_test))
    
    t_used = time()-t0
    print("time used for the prediction is:", t_used)
    list_mae, list_acc, list_accMargin = [], [], []
    
    if keepMv:
        for yp, yt in yPair_list:
            error, n_match_acc, n_match_accM = 0, 0, 0
            length = 0
            for i in range(len(yp)):
                row_yp = yp.iloc[i]
                row_yt = yt.iloc[i]
                
                df_concat = pd.concat([row_yp, row_yt], axis=1)
                df_concat.dropna(how="any", inplace=True)
                
                s1 = df_concat.T.iloc[0]
                s2 = df_concat.T.iloc[1]
                
                s1 = score2ranking(s1, False)
                s2 = score2ranking(s2)
            
                error += compute_mae(s1, s2)
                n_match_acc += compute_accuracy(s1, s2)
                n_match_accM += compute_accMargin(s1, s2)
                
                length += len(s1)
                
            mae = error / float(length)
            accuracy = n_match_acc / float(length)
            accMargin = n_match_accM /float(length)
            
            list_mae.append(mae)
            list_acc.append(accuracy)
            list_accMargin.append(accMargin)
                
    else:
        for yp, yt in yPair_list:
            mae = compute_mae(yp, yt)
            accuracy = compute_accuracy(yp, yt)
            accMargin = compute_accMargin(yp, yt)
            list_mae.append(mae)
            list_acc.append(accuracy)
            list_accMargin.append(accMargin)
        
    print("Cross validation:", \
          "\nmae is: ", mean(list_mae), \
          "\naccuracy is: ", mean(list_acc), \
          "\naccMargin is: ", mean(list_accMargin))
    

#===============================================================================
# Calculo de la puntuancion de cross validation
# clf: BaseEstimator, el clasificador
# X: DataFrame, data
# y: DataFrame, target
# kf: Kfold, iterador de cross validation
#===============================================================================
def cross_validation_RF(clf, X, y, kf):
    yPair_list = []
    splits = kf.split(X)
    
    t0 = time()
    for i, index in enumerate(splits):
        print("Fold", i)
        
        train_index = index[0]
        test_index = index[1]
    
        clf.fit(X.iloc[train_index], y.iloc[train_index])
        
        X_test = X.iloc[test_index]
        
        
        y_pred = clf.predict(X_test)
        y_test = y.iloc[test_index] 
        
        y_pred = pd.DataFrame(y_pred, columns=y_test.columns, index=y_test.index)
        y_pred = score2ranking(y_pred, reverse=False)
             
        yPair_list.append((y_pred, y_test))
    
    t_used = time()-t0
    print("time used for the prediction is:", t_used)
    list_mae, list_acc, list_accMargin = [], [], []
    
    for yp, yt in yPair_list:
        mae = compute_mae(yp, yt)
        accuracy = compute_accuracy(yp, yt)
        accMargin = compute_accMargin(yp, yt)
        list_mae.append(mae)
        list_acc.append(accuracy)
        list_accMargin.append(accMargin)
        
    print("Cross validation:", \
          "\nmae is: ", mean(list_mae), \
          "\naccuracy is: ", mean(list_acc), \
          "\naccMargin is: ", mean(list_accMargin))
    

def fill_mv(df):
    mv_positions = []
    for i in range(len(df)):
        row = df.iloc[i]
        num_mv = row.isnull().sum()
        if (num_mv>0):
            mv_positions.append(i)
    
    if (len(mv_positions)>0):
        mv_index = df.index[mv_positions]
        mv_rows = df.loc[mv_index]
        training_rows = df.drop(mv_index)
        
        rmr = RecMvRepl()
        rmr.fit(training_rows)
        rmr.predict(mv_rows) #mv_rows is being updated
        df.loc[mv_index] = mv_rows
        

#===============================================================================
# Convertir los valores de un dataframe al ranking ordinal de 1 a 10 en filas
# 
# df_qual(pd.DataFrame): dataframe a convertir
#===============================================================================
def score2ranking(data, reverse=True):
    data_copy = data.copy()
    multi_samples = type(data_copy) == type(pd.DataFrame())
            
    if multi_samples: 
        rank_list = list(range(1,11))
        for index in range(len(data_copy)):
            qual_i = data_copy.iloc[index]
            sorted_i = sorted(dict(qual_i).items(), key=operator.itemgetter(1), reverse=reverse)
            
            sorted_asig_names = [x[0] for x in sorted_i]
            
            for i in range(len(qual_i)):
                asig_name = sorted_asig_names[i]
                rank = rank_list[i]
                qual_i[asig_name] = rank
                
        data_copy[data_copy.columns] = data_copy[data_copy.columns].astype(int)

    else:
        rank_list = list(range(1, len(data)+1))
        qual_i = data_copy
        sorted_i = sorted(dict(qual_i).items(), key=operator.itemgetter(1), reverse=reverse)
        sorted_asig_names = [x[0] for x in sorted_i]
        
        for i in range(len(qual_i)):
            asig_name = sorted_asig_names[i]
            rank = rank_list[i]
            qual_i[asig_name] = rank
        
        data_copy = qual_i.astype(int)
            
    return data_copy


#===============================================================================
# Evaluacion de prediccion del clasificador, test unitario
# clf: BaseEstimator, el clasificador
# X: DataFrame, data
# y: DataFrame, target
#===============================================================================
def single_validation(clf, X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=0)
    
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    
    df_error = abs(y_pred-y_test)
    error = df_error.sum().sum() / float(df_error.shape[0]*df_error.shape[1])
    print ("error=",error)
    
    return y_pred
