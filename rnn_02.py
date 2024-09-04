# -*- coding: utf-8 -*-
"""RNN 02.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1YW6uUF8oMMAo7ggfwNDPNmtKqQ0ruNy0

# IMPORT LIBRARIES
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams["figure.figsize"] = (12,5)
import warnings
warnings.filterwarnings('ignore')
from sklearn.metrics import mean_squared_error, explained_variance_score, max_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

"""# LOAD DATA"""

# Import the CSV file
df = pd.read_csv("/content/busan_dataset.csv")

df.head()

# remove spaces on the column
df.columns = df.columns.str.lstrip()
df.columns = df.columns.str.rstrip()

# Parse the "Date" column
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

"""# Data Exploration"""

df.shape
df.info()

df.head()

df.describe()

"""# Data Cleaning"""

df.isna().sum()

# fill the nan values by upper row value
#df = df.fillna(method='ffill')
#df.tail()

"""# Data Engineering"""

# Extracting features from the index before filtering the DataFrame
#df['hour'] = df.index.hour
#df['day_of_month'] = df.index.day
#df['day_of_week'] = df.index.dayofweek
#df['month'] = df.index.mont

# Now filter the DataFrame to include only the required columns and the new features
required_cols = ['GHI_Average', 'SunZenith_KMU', 'Ambient_Pressure', 'Water', 'AOD', 'wv_500', 'CI_Beyer']
df = df[required_cols]

# Display the first few rows to confirm the columns are present
print(df.head())

sns.lineplot(x=df.index, y='GHI_Average', data=df)
plt.show()

df_by_month = df.resample('M').sum()
sns.lineplot(x=df_by_month.index, y='GHI_Average', data=df_by_month)
plt.show()

# Check the list of column names in the DataFrame
#print(df.columns)

# Create a figure with 4 subplots (2 rows, 2 columns)
fig, axs = plt.subplots(2, 2, figsize=(18, 6))

# Ensure that axs is a flat array, in case it isn't already
if isinstance(axs, np.ndarray):
    axs = axs.flatten()

# Plot 1: Hourly GHI Average
sns.pointplot(x='hour', y='GHI_Average', data=df, ax=axs[0])
axs[0].set_title('Hourly GHI Average')

# Plot 2: GHI Average by Day of the Week
sns.pointplot(x='day_of_week', y='GHI_Average', data=df, ax=axs[1])
axs[1].set_title('GHI Average by Day of the Week')

# Plot 3: GHI Average by Day of the Month
sns.pointplot(x='day_of_month', y='GHI_Average', data=df, ax=axs[2])
axs[2].set_title('GHI Average by Day of the Month')

# Plot 4: GHI Average by Month
sns.pointplot(x='month', y='GHI_Average', data=df, ax=axs[3])
axs[3].set_title('GHI Average by Month')

# Show the plots
plt.tight_layout()
plt.show()

"""# Data Preprocessing"""

# Train & Test Datasest split
train_size = int(len(df) * 0.9)
test_size = len(df) - train_size
train, test = df.iloc[0:train_size], df.iloc[train_size:len(df)]
print('Train size:',len(train))
print('Test size:', len(test))

# Input Scaling
cols = ['SunZenith_KMU','Ambient_Pressure','Water','AOD','wv_500','CI_Beyer']

scaler = RobustScaler()
scaler = scaler.fit(np.asarray(train[cols]))

train.loc[:, cols] = scaler.transform(np.asarray(train[cols]))
test.loc[:, cols] = scaler.transform(np.asarray(test[cols]))

# scaling GHI
GHI_scaler = RobustScaler()
GHI_scaler = GHI_scaler.fit(train[['GHI_Average']])
train['GHI_Average'] = GHI_scaler.transform(train[['GHI_Average']])
test['GHI_Average'] = GHI_scaler.transform(test[['GHI_Average']])

print('Train shape:',train.shape)
print('Test shape:', test.shape)

"""# Model Building"""

def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

time_steps = 10
# reshape to [samples, time_steps, features]
X_train, y_train = create_dataset(train, train.GHI_Average, time_steps)
X_test, y_test = create_dataset(test, test.GHI_Average, time_steps)
print(X_train.shape, y_train.shape)

"""# **RNN**"""

# RNN model building
rnn_model = tf.keras.Sequential()
rnn_model.add(tf.keras.layers.SimpleRNN(units=128, activation='relu', input_shape=(time_steps, X_train.shape[2])))
rnn_model.add(tf.keras.layers.Dropout(rate=0.2))
rnn_model.add(tf.keras.layers.Dense(units=1))

# Compile the model
rnn_model.compile(loss='mse', optimizer='adam')

# Train the model
rnn_history = rnn_model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.1, shuffle=False)

# Model summary
rnn_model.summary()

# model validation
plt.plot(rnn_history.history['loss'], label='train')
plt.plot(rnn_history.history['val_loss'], label='validation')
plt.title('RNN Model Training and Validation Loss')
plt.legend()
plt.show()

# inverse scaling

y_pred = rnn_model.predict(X_test)
y_train_inv = GHI_scaler.inverse_transform(y_train.reshape(1, -1))
y_test_inv = GHI_scaler.inverse_transform(y_test.reshape(1, -1))
y_pred_inv = GHI_scaler.inverse_transform(y_pred)

# visualize prediction
plt.plot(y_test_inv.flatten()[:200], marker='.', label='true')
plt.plot(y_pred_inv.flatten()[:200], 'r', label='predicted')
# Add title
plt.title('True vs Predicted GHI Values (RNN)')
plt.legend()
plt.show()

#evaluation metrics
from sklearn.metrics import mean_squared_error
from math import sqrt
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error

# Compute Metrics
r2 = r2_score(y_test_inv.flatten(), y_pred_inv.flatten())
print('R^2:', r2)

diff = y_test_inv.flatten() - y_pred_inv.flatten()

mae = mean_absolute_error(y_test_inv.flatten(), y_pred_inv.flatten())
print('MAE:', mae)

mse = mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten())
print('MSE:', mse)

rmse = np.sqrt(mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten()))
print('RMSE: %.3f' % rmse)

mbe = np.mean(diff)
print('MBE:', mbe)

rrmse = np.sqrt(mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten())) / np.mean(y_test_inv.flatten())
print('RRMSE:', rrmse)

rmbe = mbe / np.mean(y_test_inv.flatten())
print('RMBE:', rmbe)

# Create dictionary and DataFrame
metrics = {
    'Metric': ['R^2', 'MAE', 'MSE', 'RMSE', 'MBE', 'RRMSE', 'RMBE'],
    'Value': [r2, mae, mse, rmse, mbe, rrmse, rmbe]
}
df_metrics_RNN = pd.DataFrame(metrics)

# Display the DataFrame
df_metrics_RNN.head()

# Plot the table
fig, ax = plt.subplots(figsize=(6, 2))
ax.axis('tight')
ax.axis('off')

# Add title
title = 'RNN Performance Metrics'
ax.text(0.5, 1.1, title, ha='center', va='center', fontsize=14, weight='bold', transform=ax.transAxes)

# Create and display the table
table = ax.table(cellText=df_metrics_RNN.values, colLabels=df_metrics_RNN.columns, cellLoc='center', loc='center')

# Display the plot
plt.show()

# Assuming 'df' has a DateTime index and you want to keep the corresponding dates for the test set
dates = df.index[train_size + time_steps:].to_list()

# Combine the predicted and actual values with the dates
results_RNN_df = pd.DataFrame({
    'Time': dates,
    'Actual GHI': y_test_inv.flatten(),
    'Predicted GHI': y_pred_inv.flatten()
})

# Display the first few rows
results_RNN_df.head()

# Save the table to a CSV file
results_RNN_df.to_csv('RNN02_GHI_predictions.csv', index=False)