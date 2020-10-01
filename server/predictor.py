import config as cfg

import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelBinarizer

# Connect to MongoDB
conn = MongoClient(cfg.MONGO_IP, cfg.MONGO_PORT)
db = conn[cfg.MONGO_DBNAME]
sensor_e1 = db[cfg.MONGO_CNAME]

print('Predictor connected to DB!')

# Load Data From DB
cursor = sensor_e1.find()
df = pd.DataFrame(list(cursor))

# Drop _ids
del df['_id']
del df['dayOfMonth']
del df['is_weekend']

# One-Hot Encode
dow_encoder = LabelBinarizer()
dow = pd.DataFrame(dow_encoder.fit_transform(df['dayOfWeek']))

hour_encoder = LabelBinarizer()
hour = pd.DataFrame(hour_encoder.fit_transform(df['hour']))

oh_df = pd.concat([df, dow, hour], axis=1).drop(['dayOfWeek', 'hour'], axis=1)

# define independent / dependent variables
X = oh_df.drop("packetEvents", axis=1)
y = oh_df["packetEvents"]

# Establish model
model = RandomForestRegressor(n_jobs=-1)

# train the model
model.set_params(n_estimators=50)
model.fit(X, y)

print(X.head())

print("Predictor ready !")


def predict(pdata):
    k = pd.DataFrame.from_records(pdata)
    k = k.drop("dayOfMonth", axis=1)
    dow = pd.DataFrame(dow_encoder.transform(k['dayOfWeek']))
    hour = pd.DataFrame(hour_encoder.transform(k['hour']))
    oh_k = pd.concat([k, dow, hour], axis=1).drop(['dayOfWeek', 'hour'], axis=1)
    return model.predict(oh_k)
