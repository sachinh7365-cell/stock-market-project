# ============================================================
#  Stock Market Price Prediction using LSTM
#  Predicts multiple days ahead
#  Beginner Friendly - well commented!
# ============================================================

# ---- STEP 1: Install required libraries ----
# Run this in terminal first:
# pip install yfinance numpy pandas matplotlib scikit-learn tensorflow

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION - Change these settings as you like!
# ============================================================
STOCK_TICKER   = "AAPL"      # Stock symbol (e.g. AAPL, TSLA, GOOGL, RELIANCE.NS)
START_DATE     = "2018-01-01"
END_DATE       = "2024-12-31"
DAYS_TO_PREDICT = 30          # How many future days to predict
LOOK_BACK      = 60           # How many past days the model looks at
EPOCHS         = 50
BATCH_SIZE     = 32


# ============================================================
# STEP 2: Download Stock Data
# ============================================================
print(f"\n📥 Downloading {STOCK_TICKER} data...")
df = yf.download(STOCK_TICKER, start=START_DATE, end=END_DATE)
print(f"✅ Downloaded {len(df)} rows of data\n")

# We'll use the 'Close' price only
data = df[['Close']].copy()
data.dropna(inplace=True)

print(data.tail())


# ============================================================
# STEP 3: Visualize Raw Data
# ============================================================
plt.figure(figsize=(14, 5))
plt.plot(data['Close'], label=f"{STOCK_TICKER} Close Price", color='royalblue')
plt.title(f"{STOCK_TICKER} Historical Close Price")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.legend()
plt.tight_layout()
plt.savefig("1_raw_stock_data.png", dpi=150)
plt.show()
print("📊 Chart saved: 1_raw_stock_data.png")


# ============================================================
# STEP 4: Scale Data (LSTM works better with values 0-1)
# ============================================================
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)


# ============================================================
# STEP 5: Create Sequences for LSTM
# Each sample: last LOOK_BACK days → predict next day
# ============================================================
def create_sequences(dataset, look_back=60):
    X, y = [], []
    for i in range(look_back, len(dataset)):
        X.append(dataset[i - look_back:i, 0])
        y.append(dataset[i, 0])
    return np.array(X), np.array(y)


X, y = create_sequences(scaled_data, LOOK_BACK)

# Reshape X for LSTM input: (samples, timesteps, features)
X = X.reshape((X.shape[0], X.shape[1], 1))

# Train/Test split (80% train, 20% test)
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

print(f"\n🔢 Training samples : {len(X_train)}")
print(f"🔢 Testing  samples : {len(X_test)}")


# ============================================================
# STEP 6: Build the LSTM Model
# ============================================================
print("\n🏗️  Building LSTM model...")

model = Sequential([
    LSTM(units=64, return_sequences=True, input_shape=(LOOK_BACK, 1)),
    Dropout(0.2),

    LSTM(units=64, return_sequences=False),
    Dropout(0.2),

    Dense(units=32, activation='relu'),
    Dense(units=1)   # Output: next day price
])

model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()


# ============================================================
# STEP 7: Train the Model
# ============================================================
print("\n🚀 Training...")

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

# Plot training loss
plt.figure(figsize=(10, 4))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.title("Model Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.tight_layout()
plt.savefig("2_training_loss.png", dpi=150)
plt.show()
print("📊 Chart saved: 2_training_loss.png")


# ============================================================
# STEP 8: Evaluate on Test Data
# ============================================================
print("\n📈 Evaluating on test data...")

y_pred_scaled = model.predict(X_test)

# Reverse the scaling to get actual prices
y_pred = scaler.inverse_transform(y_pred_scaled)
y_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

mae  = mean_absolute_error(y_actual, y_pred)
rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
print(f"📉 MAE  (Mean Absolute Error) : ${mae:.2f}")
print(f"📉 RMSE (Root Mean Sq Error)  : ${rmse:.2f}")

# Plot actual vs predicted
plt.figure(figsize=(14, 5))
plt.plot(y_actual, label="Actual Price", color='royalblue')
plt.plot(y_pred,   label="Predicted Price", color='orange', linestyle='--')
plt.title(f"{STOCK_TICKER} - Actual vs Predicted (Test Set)")
plt.xlabel("Days")
plt.ylabel("Price (USD)")
plt.legend()
plt.tight_layout()
plt.savefig("3_actual_vs_predicted.png", dpi=150)
plt.show()
print("📊 Chart saved: 3_actual_vs_predicted.png")


# ============================================================
# STEP 9: Predict Future Days
# ============================================================
print(f"\n🔮 Predicting next {DAYS_TO_PREDICT} days...")

# Start with the last LOOK_BACK days from the full dataset
last_sequence = scaled_data[-LOOK_BACK:]
future_predictions = []

current_seq = last_sequence.copy()

for _ in range(DAYS_TO_PREDICT):
    input_seq = current_seq.reshape(1, LOOK_BACK, 1)
    next_price_scaled = model.predict(input_seq, verbose=0)
    future_predictions.append(next_price_scaled[0, 0])
    # Slide the window: drop first, add new prediction
    current_seq = np.append(current_seq[1:], next_price_scaled, axis=0)

# Reverse scaling
future_prices = scaler.inverse_transform(
    np.array(future_predictions).reshape(-1, 1)
)

# Create future dates
last_date = data.index[-1]
future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=DAYS_TO_PREDICT)

future_df = pd.DataFrame({'Date': future_dates, 'Predicted Price': future_prices.flatten()})
future_df.set_index('Date', inplace=True)

print("\n📅 Future Price Predictions:")
print(future_df.to_string())

# Plot future predictions
plt.figure(figsize=(14, 5))
plt.plot(data['Close'].tail(120), label="Historical Price", color='royalblue')
plt.plot(future_df['Predicted Price'], label="Future Prediction", color='green', linestyle='--', marker='o', markersize=4)
plt.axvline(x=data.index[-1], color='red', linestyle=':', label='Prediction Start')
plt.title(f"{STOCK_TICKER} - {DAYS_TO_PREDICT}-Day Future Price Prediction")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.legend()
plt.tight_layout()
plt.savefig("4_future_predictions.png", dpi=150)
plt.show()
print("📊 Chart saved: 4_future_predictions.png")

print("\n✅ All done! Check the 4 chart images saved in your folder.")