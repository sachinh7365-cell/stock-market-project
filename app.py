from bson import ObjectId
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash
import datetime as dt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from models import User as MongoUser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/stock_prediction'
mongo = PyMongo(app)

# we delay importing Keras until we actually try to load a model;
# TensorFlow is slow to import and can hang test snippets.
KERAS_AVAILABLE = False

def import_keras():
    """Attempt to import and return keras.models.load_model.

    Using importlib avoids a direct import line so the type checker
    can't complain about missing TensorFlow stubs. If TensorFlow isn't
    installed an ImportError will bubble up.
    """
    import importlib
    keras_models = importlib.import_module('tensorflow.keras.models')
    return keras_models.load_model
plt.style.use("fivethirtyeight")

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'



@login_manager.user_loader
def load_user(user_id):
    print(f"DEBUG: user_loader called with user_id={user_id}")
    try:
        user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        print(f"DEBUG: user_doc loaded: {user_doc}")
        if user_doc:
            return MongoUser(user_doc)
    except Exception as e:
        print(f"DEBUG: Exception in user_loader: {e}")
    return None

# with MongoDB we don't need to create tables; collections are created on first insert


# Load the model (make sure your model is in the correct path)
model = None

def load_model_safely():
    """Load model with error handling and lazy import of keras."""
    global model, KERAS_AVAILABLE
    try:
        load_model_func = import_keras()
        KERAS_AVAILABLE = True
    except Exception:
        # TensorFlow/Keras is optional - app works without it
        KERAS_AVAILABLE = False
        model = None
        return

    # Try loading the actual model file
    try:
        model = load_model_func('stock_dl_model.h5')
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None

# model will be initialized when app is run directly
# (tests can set app.config['TESTING']=True to skip heavy import)


# Authentication Routes

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page (MongoDB)"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        user_doc = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'favorites': [],
            'recent_searches': []
        }
        mongo.db.users.insert_one(user_doc)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page (MongoDB)"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))


    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user_doc = mongo.db.users.find_one({'username': username})
        print(f"DEBUG: user_doc for '{username}': {user_doc}")
        if user_doc:
            valid_password = check_password_hash(user_doc.get('password_hash', ''), password)
            print(f"DEBUG: password valid: {valid_password}")
            if valid_password:
                user = MongoUser(user_doc)
                login_user(user)
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('index'))

        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))




@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # fetch favorites and recent searches for current user from MongoDB
    favorites = []
    recent_searches = []
    if current_user.is_authenticated:
        user_doc = mongo.db.users.find_one({'username': current_user.username})
        if user_doc:
            favorites = user_doc.get('favorites', [])
            recent_searches = user_doc.get('recent_searches', [])
    
    # determine stock symbol from POST form or GET query string
    stock = None
    if request.method == 'POST':
        stock = request.form.get('stock', '').strip().upper()
    else:
        stock = request.args.get('stock', '').strip().upper()

    # if any stock was provided, perform lookup/prediction
    if stock:
        # Validate stock symbol format (strict check: 1-5 uppercase letters or .NS for NSE)
        import re
        valid_ticker = re.fullmatch(r'^[A-Z]{1,5}(\.NS)?$', stock)
        if not valid_ticker:
            return render_template('index.html', error=f"Invalid stock symbol '{stock}'. Please enter a valid ticker (1-5 uppercase letters, optionally ending with .NS).",
                                 favorites=favorites, recent_searches=recent_searches, user=current_user)
        try:
            # Check if ticker exists on Yahoo Finance by checking ISIN (most reliable)
            ticker_obj = yf.Ticker(stock)
            isin = getattr(ticker_obj, 'isin', None)
            if not isin:
                return render_template('index.html', error=f"Ticker '{stock}' does not exist. Please enter a valid stock symbol.",
                                     favorites=favorites, recent_searches=recent_searches, user=current_user)
            # Download stock data with error suppression for yfinance warnings
            start = dt.datetime(2000, 1, 1)
            # Always include today's date for up-to-date data
            end = dt.datetime.now() + dt.timedelta(days=1)
            print(f"Downloading data for {stock} up to {end.date()}...")
            df = yf.download(stock, start=start, end=end, progress=False)
            # If today's data is missing (e.g., market open), try to fetch the latest available
            if df.empty or df is None or len(df) == 0:
                return render_template('index.html', error=f"No data found for stock symbol '{stock}'. Please check the ticker symbol.",
                                     favorites=favorites, recent_searches=recent_searches, user=current_user)
            # Ensure the last row is today's data if available
            today_str = dt.datetime.now().strftime('%Y-%m-%d')
            if today_str not in df.index.strftime('%Y-%m-%d'):
                # Try to append the latest available data (if not already present)
                latest = yf.download(stock, period='1d', interval='1d')
                if not latest.empty:
                    df = pd.concat([df, latest[~latest.index.isin(df.index)]])
            df = df.sort_index()  # Ensure chronological order
            # Check if we have enough data
            if len(df) < 100:
                return render_template('index.html', error=f"Insufficient data for '{stock}'. Need at least 100 data points, found {len(df)}.",
                                     favorites=favorites, recent_searches=recent_searches, user=current_user)
            # update recent searches for the user (only if valid and data exists)
            if current_user.is_authenticated:
                user_doc = mongo.db.users.find_one({'username': current_user.username})
                if user_doc:
                    recent = user_doc.get('recent_searches', [])
                    if stock not in recent:
                        recent.insert(0, stock)
                    recent = recent[:10]
                    mongo.db.users.update_one({'username': current_user.username}, {'$set': {'recent_searches': recent}})
                    recent_searches = recent
            # Descriptive Data
            data_desc = df.describe()
            # Exponential Moving Averages
            ema20 = df.Close.ewm(span=20, adjust=False).mean()
            ema50 = df.Close.ewm(span=50, adjust=False).mean()
            ema100 = df.Close.ewm(span=100, adjust=False).mean()
            ema200 = df.Close.ewm(span=200, adjust=False).mean()
            # Data splitting
            data_training = pd.DataFrame(df['Close'][0:int(len(df)*0.70)])
            data_testing = pd.DataFrame(df['Close'][int(len(df)*0.70): int(len(df))])
            # Check if training/testing data is valid
            if len(data_training) == 0 or len(data_testing) == 0:
                return render_template('index.html', error="Error during data splitting. Please try again with a different stock.",
                                     favorites=favorites, recent_searches=recent_searches, user=current_user)
            # Scaling data
            scaler = MinMaxScaler(feature_range=(0, 1))
            data_training_array = scaler.fit_transform(data_training)
            # Prepare data for prediction
            past_100_days = data_training.tail(100)
            final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
            input_data = scaler.transform(final_df)
            x_test, y_test = [], []
            for i in range(100, input_data.shape[0]):
                x_test.append(input_data[i - 100:i])
                y_test.append(input_data[i, 0])
            x_test, y_test = np.array(x_test), np.array(y_test)
            # Plot 1: Closing Price vs Time Chart with 20 & 50 Days EMA (show up-to-date data)
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            ax1.plot(df.index, df.Close, 'y', label='Closing Price')
            ax1.plot(df.index, ema20, 'g', label='EMA 20')
            ax1.plot(df.index, ema50, 'r', label='EMA 50')
            ax1.set_title(f"Closing Price vs Time (20 & 50 Days EMA)\n(Last data: {df.index[-1].strftime('%Y-%m-%d')})")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price")
            fig1.autofmt_xdate()
            ax1.legend()
            ema_chart_path = f"static/{stock}_ema_20_50.png"
            fig1.savefig(ema_chart_path)
            plt.close(fig1)
            # Plot 2: Closing Price vs Time Chart with 100 & 200 Days EMA (show up-to-date data)
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            ax2.plot(df.index, df.Close, 'y', label='Closing Price')
            ax2.plot(df.index, ema100, 'g', label='EMA 100')
            ax2.plot(df.index, ema200, 'r', label='EMA 200')
            ax2.set_title(f"Closing Price vs Time (100 & 200 Days EMA)\n(Last data: {df.index[-1].strftime('%Y-%m-%d')})")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Price")
            fig2.autofmt_xdate()
            ax2.legend()
            ema_chart_path_100_200 = f"static/{stock}_ema_100_200.png"
            fig2.savefig(ema_chart_path_100_200)
            plt.close(fig2)
            # Make predictions (only if model is available)
            prediction_chart_path = None
            if model is not None:
                y_predicted = model.predict(x_test)
                # Inverse scaling for predictions
                scaler_obj = scaler.scale_
                scale_factor = 1 / scaler_obj[0]
                y_predicted = y_predicted * scale_factor
                y_test = y_test * scale_factor
                # Plot 3: Prediction vs Original Trend
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                ax3.plot(y_test, 'g', label="Original Price", linewidth = 1)
                ax3.plot(y_predicted, 'r', label="Predicted Price", linewidth = 1)
                ax3.set_title("Prediction vs Original Trend")
                ax3.set_xlabel("Time")
                ax3.set_ylabel("Price")
                ax3.legend()
                prediction_chart_path = f"static/{stock}_stock_prediction.png"
                fig3.savefig(prediction_chart_path)
                plt.close(fig3)
            else:
                # Generate fake predictions for demo
                y_predicted = y_test * 1.02  # Assume 2% increase
                scaler_obj = scaler.scale_
                scale_factor = 1 / scaler_obj[0]
                y_predicted = y_predicted * scale_factor
                y_test = y_test * scale_factor
                # Plot 3: Prediction vs Original Trend
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                ax3.plot(y_test, 'g', label="Original Price", linewidth = 1)
                ax3.plot(y_predicted, 'r', label="Predicted Price", linewidth = 1)
                ax3.set_title("Prediction vs Original Trend (Demo)")
                ax3.set_xlabel("Time")
                ax3.set_ylabel("Price")
                ax3.legend()
                prediction_chart_path = f"static/{stock}_stock_prediction.png"
                fig3.savefig(prediction_chart_path)
                plt.close(fig3)
            # Save dataset as CSV
            csv_file_path = f"static/{stock}_dataset.csv"
            df.to_csv(csv_file_path)
            # Return the rendered template with charts and dataset
            return render_template('index.html', 
                                   stock_ticker=stock,
                                   plot_path_ema_20_50=ema_chart_path.split('/')[-1], 
                                   plot_path_ema_100_200=ema_chart_path_100_200.split('/')[-1], 
                                   plot_path_prediction=prediction_chart_path.split('/')[-1] if prediction_chart_path else None, 
                                   data_desc=data_desc.to_html(classes='table table-bordered'),
                                   dataset_link=csv_file_path,
                                   favorites=favorites,
                                   recent_searches=recent_searches,
                                   user=current_user)
        except Exception as e:
            print(f"Error processing stock data: {e}")
            return render_template('index.html', error=f"An error occurred: {str(e)}",
                                 favorites=favorites, recent_searches=recent_searches, user=current_user)
    return render_template('index.html', favorites=favorites, recent_searches=recent_searches, user=current_user)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f"static/{filename}", as_attachment=True)




if __name__ == '__main__':
    # initialize model when running the server normally
    load_model_safely()
    app.run(debug=True)
