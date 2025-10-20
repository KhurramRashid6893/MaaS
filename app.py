import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import google.generativeai as genai
import itertools
import random
import json
import markdown
import sqlite3
from datetime import datetime

# --- Application Setup ---
app = Flask(__name__)
app.secret_key = 'supersecretkeyforhackathon-crud-final'

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect('maas_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db_if_needed():
    if not os.path.exists('maas_database.db'):
        print("Database not found, initializing...")
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                image TEXT,
                category TEXT,
                farmer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Add some initial sample data
        conn.execute("INSERT INTO products (title, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                     ('Organic Pearl Millet (Bajra)', 45.50, 'From Rajasthan, rich in magnesium.', 'bajra.jpg', 'Grains'))
        conn.execute("INSERT INTO products (title, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                     ('Premium Sorghum (Jowar)', 52.00, 'Gluten-free, sourced from Maharashtra.', 'jowar.jpg', 'Grains'))
        conn.execute("INSERT INTO products (title, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                     ('Malnad Finger Millet (Ragi)', 65.00, 'Calcium-rich Ragi from Karnataka.', 'ragi.jpg', 'Grains'))
        conn.commit()
        conn.close()
        print("Database initialized.")

# Call the function to initialize DB on startup if it doesn't exist
init_db_if_needed()

# --- Gemini AI Setup ---
API_KEYS = [
    "AIzaSyBZ_Mea6_FaJVcWTYhc4r1OAlGzjdQIkxw", "AIzaSyCyuyG-IxIyJYp4sw5BpJCPWUlUvG-M9lw",
    "AIzaSyA9rvL4I_VTJ6SPGZ19Ug-xbXfUxT5GZrU", "AIzaSyDZS2J4I02v_fogb47qbpFzUOiZFpt8-CI",
    "AIzaSyAfX5U8uu5fLpqTNEn9pvibUWh9PWLAFrk", "AIzaSyDdFU9MHjKf6Ga-cXzvE-niOnGACx8BQI4",
]
key_cycler = itertools.cycle(API_KEYS)

def get_gemini_model():
    api_key = next(key_cycler)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def generate_gemini_response(prompt):
    for _ in range(len(API_KEYS)):
        try:
            model = get_gemini_model()
            response = model.generate_content(prompt)
            return markdown.markdown(response.text)
        except Exception as e:
            print(f"API key failed: {e}. Trying next key.")
    return "<p>The AI service is currently unavailable. Please try again later.</p>"

# --- Simulated APIs ---
def get_govt_schemes():
    return [
        {"name": "PM-KISAN Scheme", "description": "Provides income support to all landholding farmer families.", "link": "#"},
        {"name": "Shree Anna Scheme", "description": "Promotes millet cultivation, procurement, and value-addition.", "link": "#"},
    ]
def get_shg_fpo_directory():
    return [
        {"name": "Annapurna SHG", "location": "Wardha, Maharashtra", "specialty": "Jowar Processing"},
        {"name": "Sahyadri FPO", "location": "Chikkamagaluru, Karnataka", "specialty": "Organic Ragi"},
    ]
def get_dummy_blockchain_tx():
    return { "tx_hash": f"0x{random.randbytes(32).hex()}", "status": "Confirmed" }

# --- Core Application Routes ---
@app.route('/')
def home():
    return render_template('home.html')

def get_location_from_request(req):
    return req.form.get('latitude'), req.form.get('longitude')

@app.route('/farmer', methods=['GET', 'POST'])
def farmer_dashboard():
    lat, lon = get_location_from_request(request)
    advisor_prompt = f"Act as an Agri-AI assistant for a millet farmer at lat {lat}, lon {lon} in India. Provide a bulleted list of actionable advice. Include: 1. A crop health tip. 2. A market price alert. 3. A government scheme reminder."
    ai_advisor = generate_gemini_response(advisor_prompt) if lat else "<p>Enable location for personalized advice.</p>"
    
    conn = get_db_connection()
    marketplace_items = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('farmer.html', 
                           ai_advisor=ai_advisor, 
                           blockchain_tx=get_dummy_blockchain_tx(),
                           marketplace_items=marketplace_items,
                           govt_schemes=get_govt_schemes())

@app.route('/buyer', methods=['GET', 'POST'])
def buyer_dashboard():
    conn = get_db_connection()
    marketplace_items = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('buyer.html', marketplace_items=marketplace_items, market_intel="Enable location for intel.", blockchain_tx=get_dummy_blockchain_tx(), shg_fpo_directory=get_shg_fpo_directory())

@app.route('/consumer', methods=['GET', 'POST'])
def consumer_dashboard():
    conn = get_db_connection()
    marketplace_items = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('consumer.html', marketplace_items=marketplace_items, nutrition_plan="Enable location for a meal plan.", blockchain_tx=get_dummy_blockchain_tx())

# --- CRUD Routes for Products ---
@app.route('/products/manage')
def manage_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('manage_products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        title, price, description, category = request.form['title'], request.form['price'], request.form['description'], request.form['category']
        if not title or not price:
            flash('Title and Price are required!', 'danger')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO products (title, price, description, category, image) VALUES (?, ?, ?, ?, ?)',
                         (title, float(price), description, category, 'millet_placeholder.jpg'))
            conn.commit()
            conn.close()
            flash('Product added successfully!', 'success')
            return redirect(url_for('manage_products'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        title, price, description, category = request.form['title'], request.form['price'], request.form['description'], request.form['category']
        if not title or not price:
            flash('Title and Price are required!', 'danger')
        else:
            conn.execute('UPDATE products SET title = ?, price = ?, description = ?, category = ? WHERE id = ?',
                         (title, float(price), description, category, id))
            conn.commit()
            conn.close()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('manage_products'))
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('manage_products'))

# --- API Endpoints ---
@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get("message", "")
    prompt = f"You are 'Millet AI Assistant', a helpful chatbot for the MaaS platform in India. Answer the user's query concisely and using Markdown: \"{user_message}\""
    response = generate_gemini_response(prompt)
    return jsonify({"response": response})

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    file = request.files['file']
    filename = secure_filename(file.filename)
    analysis_result = {
        "status": "success", "fileName": filename,
        "ai_result": generate_gemini_response(f"Act as a plant pathologist AI. A farmer has uploaded an image of a millet plant. Provide a simulated analysis. Identify a common potential issue (e.g., stem borer, downy mildew) and give a confidence score and a brief, actionable recommendation.")
    }
    return jsonify(analysis_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)