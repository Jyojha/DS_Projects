import os.path
from glob import glob

from django.conf import settings

import numpy as np
import pandas as pd
import patsy
from sklearn.externals import joblib
from sklearn.preprocessing import StandardScaler

MODELS_DIR = settings.MODELS_DIR
MODELS = {}

for model_path in glob(os.path.join(MODELS_DIR, "*.pkl")):
    city, _ = os.path.splitext(os.path.basename(model_path))
    dataset_path = os.path.join(MODELS_DIR, '%s.csv' % city)

    model = joblib.load(model_path)
    dataset = pd.read_csv(dataset_path)

    MODELS[city] = (dataset, model)

def preprocess(X, neighborhood, bedrooms, bathrooms, room_type):
    X1 = X[0:1]
    X1.loc[0,:] = 0.
    x = X1[[i for i in X1.columns if 'neighborhood' in i]]

    tmp = [n for n in x.columns if neighborhood in n]
    #print tmp[0]

    #print X1.loc[0,tmp[0]]

    X1.loc[0,tmp[0]] = 1.
    #print X1.loc[0,tmp[0]]
    X1.loc[0,'bathrooms'] = bathrooms
    X1.loc[0,'bedrooms'] = bedrooms
    X1.loc[0,'dist_arprt'] = np.mean(X['dist_arprt'][X[tmp[0]] == 1])
    X1.loc[0,'host_count'] = np.mean(X['host_count'][X[tmp[0]] == 1])
    X1.loc[0,'metrostn_count'] = np.mean(X['metrostn_count'][X[tmp[0]] == 1])
    X1.loc[0,'minstay'] = np.mean(X['minstay'][X[tmp[0]] == 1])
    X1.loc[0,'overall_satisfaction'] = np.mean(X['overall_satisfaction'][X[tmp[0]] == 1])
    X1.loc[0,'rest_count'] = np.mean(X['rest_count'][X[tmp[0]] == 1])
    X1.loc[0,'review_count'] = np.mean(X['review_count'][X[tmp[0]] == 1])
    X1.loc[0,'reviews'] = np.mean(X['reviews'][X[tmp[0]] == 1])

    if room_type == 'Private room':
        X1.loc[0,'room_type[T.Private room]'] = 1.
    elif room_type == 'Shared room':
        X1.loc[0,'room_type[T.Shared room]'] = 1.
    elif room_type == 'Entire home/apt':
        X1.loc[0,'room_type[T.Private room]'] = 0.
        X1.loc[0,'room_type[T.Shared room]'] = 0.


    #print X1
    return X1

def predict_price(city, neighborhood, bedrooms, bathrooms, room_type):
    df, enet = MODELS[city]
    X = df[[x for x in df.columns
            if x not in ['bhk', 'price', 'latitude',
                         'longitude', 'room_id', 'residuals']]]
    target = np.log(df.price)
    formula = "target ~ "+' + '.join(X)+' -1'
    y, X = patsy.dmatrices(formula, data=df, return_type='dataframe')
    Xn = pd.DataFrame(StandardScaler().fit_transform(X), columns = X.columns)
    #print type(Xn)

    X_final = preprocess(Xn, neighborhood, bedrooms, bathrooms, room_type)
    #print X_final.shape
    yhat = enet.predict(X_final)
    return np.exp(yhat)[0]
