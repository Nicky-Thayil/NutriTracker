from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from datetime import date, datetime
import logging

from app import app, db
from models import User, Food, FoodLog, WeightEntry
from replit_auth import require_login, make_replit_blueprint
from services.food_api import OpenFoodFactsAPI, FoodRecognitionAPI
from services.nutrition_calculator import NutritionCalculator

# Register authentication blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

logger = logging.getLogger(__name__)

@app.before_request
def make_session_permanent():
    from flask import session
    session.permanent = True

@app.route('/')
def index():
    """Landing page for logged out users, dashboard for logged in users"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard showing nutrition overview"""
    # Get today's nutrition summary
    nutrition_summary = NutritionCalculator.get_daily_nutrition_summary(current_user)
    
    # Get weight progress
    weight_progress = NutritionCalculator.get_weight_progress(current_user, days=30)
    
    # Get fitness recommendations
    recommendations = NutritionCalculator.get_fitness_recommendations(current_user)
    
    return render_template('dashboard.html', 
                         nutrition=nutrition_summary,
                         weight_progress=weight_progress,
                         recommendations=recommendations)

@app.route('/food-log')
@require_login
def food_log():
    """Food logging page"""
    target_date = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    # Get food logs for the target date
    logs = db.session.query(FoodLog).filter_by(
        user_id=current_user.id,
        log_date=target_date
    ).join(Food).order_by(FoodLog.logged_at.desc()).all()
    
    # Get nutrition summary for the date
    nutrition_summary = NutritionCalculator.get_daily_nutrition_summary(current_user, target_date)
    
    return render_template('food_log.html', 
                         logs=logs, 
                         target_date=target_date,
                         nutrition=nutrition_summary)

@app.route('/add-food', methods=['POST'])
@require_login
def add_food():
    """Add food to log"""
    try:
        food_id = request.form.get('food_id')
        quantity = float(request.form.get('quantity', 100))
        meal_type = request.form.get('meal_type', 'snack')
        log_date = request.form.get('log_date', date.today().isoformat())
        
        # Parse date
        try:
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
        except ValueError:
            log_date = date.today()
        
        # Get food item
        food = Food.query.get(food_id)
        if not food:
            flash('Food item not found', 'error')
            return redirect(url_for('food_log'))
        
        # Calculate nutrition values based on quantity
        multiplier = quantity / 100  # nutrition is per 100g
        
        food_log = FoodLog(
            user_id=current_user.id,
            food_id=food_id,
            quantity=quantity,
            meal_type=meal_type,
            log_date=log_date,
            calories=(food.calories_per_100g or 0) * multiplier,
            protein=(food.protein_per_100g or 0) * multiplier,
            carbs=(food.carbs_per_100g or 0) * multiplier,
            fat=(food.fat_per_100g or 0) * multiplier,
            fiber=(food.fiber_per_100g or 0) * multiplier,
            sugar=(food.sugar_per_100g or 0) * multiplier,
            sodium=(food.sodium_per_100g or 0) * multiplier
        )
        
        db.session.add(food_log)
        db.session.commit()
        
        flash('Food added successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error adding food: {str(e)}")
        flash('Error adding food. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('food_log', date=log_date.isoformat()))

@app.route('/search-food')
@require_login
def search_food():
    """Search for food items"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Search in database first
    db_foods = Food.query.filter(Food.name.ilike(f'%{query}%')).limit(10).all()
    
    results = []
    for food in db_foods:
        results.append({
            'id': food.id,
            'name': food.name,
            'brand': food.brand,
            'calories_per_100g': food.calories_per_100g,
            'source': 'database'
        })
    
    # If we have less than 5 results, search Open Food Facts
    if len(results) < 5:
        api_results = OpenFoodFactsAPI.search_products(query, page_size=10)
        for food_data in api_results[:10-len(results)]:
            # Check if food already exists in database
            existing_food = Food.query.filter_by(barcode=food_data['barcode']).first()
            if not existing_food and food_data['barcode']:
                # Add to database
                food = Food(**food_data)
                db.session.add(food)
                db.session.commit()
                food_id = food.id
            elif existing_food:
                food_id = existing_food.id
            else:
                continue
            
            results.append({
                'id': food_id,
                'name': food_data['name'],
                'brand': food_data['brand'],
                'calories_per_100g': food_data['calories_per_100g'],
                'source': 'api'
            })
    
    return jsonify(results)

@app.route('/scan-barcode', methods=['POST'])
@require_login
def scan_barcode():
    """Process barcode scan"""
    barcode = request.json.get('barcode')
    if not barcode:
        return jsonify({'error': 'No barcode provided'}), 400
    
    # Check if food exists in database
    food = Food.query.filter_by(barcode=barcode).first()
    
    if not food:
        # Fetch from Open Food Facts API
        food_data = OpenFoodFactsAPI.get_product_by_barcode(barcode)
        if food_data:
            food = Food(**food_data)
            db.session.add(food)
            db.session.commit()
        else:
            return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': food.id,
        'name': food.name,
        'brand': food.brand,
        'calories_per_100g': food.calories_per_100g,
        'protein_per_100g': food.protein_per_100g,
        'carbs_per_100g': food.carbs_per_100g,
        'fat_per_100g': food.fat_per_100g
    })

@app.route('/recognize-food', methods=['POST'])
@require_login
def recognize_food():
    """Process food image recognition"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        # Read image data
        image_data = image_file.read()
        
        # Use food recognition service
        recognized_food = FoodRecognitionAPI.recognize_food_from_image(image_data)
        
        if recognized_food:
            # Search for the recognized food in our database
            suggestions = FoodRecognitionAPI.get_food_suggestions(recognized_food)
            return jsonify({
                'recognized': recognized_food,
                'suggestions': suggestions[:5]
            })
        else:
            return jsonify({'error': 'Could not recognize food in image'}), 400
            
    except Exception as e:
        logger.error(f"Error in food recognition: {str(e)}")
        return jsonify({'error': 'Error processing image'}), 500

@app.route('/weight-tracker')
@require_login
def weight_tracker():
    """Weight tracking page"""
    # Get weight progress for different time periods
    weight_7d = NutritionCalculator.get_weight_progress(current_user, days=7)
    weight_30d = NutritionCalculator.get_weight_progress(current_user, days=30)
    weight_90d = NutritionCalculator.get_weight_progress(current_user, days=90)
    
    return render_template('weight_tracker.html',
                         weight_7d=weight_7d,
                         weight_30d=weight_30d,
                         weight_90d=weight_90d)

@app.route('/add-weight', methods=['POST'])
@require_login
def add_weight():
    """Add weight entry"""
    try:
        weight = float(request.form.get('weight'))
        entry_date = request.form.get('entry_date', date.today().isoformat())
        
        # Parse date
        try:
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        except ValueError:
            entry_date = date.today()
        
        # Check if entry already exists for this date
        existing_entry = WeightEntry.query.filter_by(
            user_id=current_user.id,
            entry_date=entry_date
        ).first()
        
        if existing_entry:
            existing_entry.weight = weight
        else:
            weight_entry = WeightEntry(
                user_id=current_user.id,
                weight=weight,
                entry_date=entry_date
            )
            db.session.add(weight_entry)
        
        db.session.commit()
        flash('Weight recorded successfully!', 'success')
        
    except ValueError:
        flash('Please enter a valid weight', 'error')
    except Exception as e:
        logger.error(f"Error adding weight: {str(e)}")
        flash('Error recording weight. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('weight_tracker'))

@app.route('/profile')
@require_login
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@app.route('/update-profile', methods=['POST'])
@require_login
def update_profile():
    """Update user profile"""
    try:
        current_user.age = int(request.form.get('age')) if request.form.get('age') else None
        current_user.gender = request.form.get('gender')
        current_user.height = float(request.form.get('height')) if request.form.get('height') else None
        current_user.activity_level = request.form.get('activity_level')
        current_user.goal = request.form.get('goal')
        current_user.daily_calorie_goal = int(request.form.get('daily_calorie_goal', 2000))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        flash('Error updating profile. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile'))

@app.route('/delete-food-log/<int:log_id>', methods=['POST'])
@require_login
def delete_food_log(log_id):
    """Delete a food log entry"""
    try:
        food_log = FoodLog.query.filter_by(id=log_id, user_id=current_user.id).first()
        if food_log:
            log_date = food_log.log_date
            db.session.delete(food_log)
            db.session.commit()
            flash('Food entry deleted successfully!', 'success')
            return redirect(url_for('food_log', date=log_date.isoformat()))
        else:
            flash('Food entry not found', 'error')
    except Exception as e:
        logger.error(f"Error deleting food log: {str(e)}")
        flash('Error deleting food entry. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('food_log'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
