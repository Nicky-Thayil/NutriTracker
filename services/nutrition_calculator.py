from typing import Dict, Any, Optional
from datetime import date, datetime, timedelta
from models import User, FoodLog, WeightEntry
from sqlalchemy import func

class NutritionCalculator:
    """
    Calculate nutrition metrics and provide recommendations
    """
    
    @staticmethod
    def calculate_bmr(user: User, current_weight: float = None) -> float:
        """
        Calculate Basal Metabolic Rate using Harris-Benedict equation
        """
        if not user.age or not user.gender or not user.height:
            return 2000  # Default value
        
        weight = current_weight or NutritionCalculator.get_latest_weight(user)
        if not weight:
            return 2000
        
        if user.gender.lower() == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * user.height) - (5.677 * user.age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * user.height) - (4.330 * user.age)
        
        return bmr
    
    @staticmethod
    def calculate_tdee(user: User, current_weight: float = None) -> float:
        """
        Calculate Total Daily Energy Expenditure
        """
        bmr = NutritionCalculator.calculate_bmr(user, current_weight)
        
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        
        multiplier = activity_multipliers.get(user.activity_level, 1.375)
        return bmr * multiplier
    
    @staticmethod
    def get_daily_nutrition_summary(user: User, target_date: date = None) -> Dict[str, Any]:
        """
        Get nutrition summary for a specific date
        """
        if target_date is None:
            target_date = date.today()
        
        from app import db
        
        # Get all food logs for the target date
        food_logs = db.session.query(FoodLog).filter_by(
            user_id=user.id,
            log_date=target_date
        ).all()
        
        total_calories = sum(log.calories or 0 for log in food_logs)
        total_protein = sum(log.protein or 0 for log in food_logs)
        total_carbs = sum(log.carbs or 0 for log in food_logs)
        total_fat = sum(log.fat or 0 for log in food_logs)
        total_fiber = sum(log.fiber or 0 for log in food_logs)
        total_sugar = sum(log.sugar or 0 for log in food_logs)
        total_sodium = sum(log.sodium or 0 for log in food_logs)
        
        # Get current weight and calculate targets
        current_weight = NutritionCalculator.get_latest_weight(user)
        tdee = NutritionCalculator.calculate_tdee(user, current_weight)
        
        # Adjust calorie goal based on user's goal
        goal_adjustments = {
            'lose_weight': -500,  # 500 calorie deficit
            'maintain': 0,
            'gain_weight': 300   # 300 calorie surplus
        }
        
        calorie_goal = tdee + goal_adjustments.get(user.goal, 0)
        
        # Calculate macro targets (protein: 25%, carbs: 45%, fat: 30%)
        protein_goal = (calorie_goal * 0.25) / 4  # 4 calories per gram
        carbs_goal = (calorie_goal * 0.45) / 4    # 4 calories per gram
        fat_goal = (calorie_goal * 0.30) / 9      # 9 calories per gram
        
        return {
            'date': target_date,
            'totals': {
                'calories': round(total_calories, 1),
                'protein': round(total_protein, 1),
                'carbs': round(total_carbs, 1),
                'fat': round(total_fat, 1),
                'fiber': round(total_fiber, 1),
                'sugar': round(total_sugar, 1),
                'sodium': round(total_sodium, 1)
            },
            'goals': {
                'calories': round(calorie_goal),
                'protein': round(protein_goal, 1),
                'carbs': round(carbs_goal, 1),
                'fat': round(fat_goal, 1)
            },
            'percentages': {
                'calories': round((total_calories / calorie_goal) * 100, 1) if calorie_goal > 0 else 0,
                'protein': round((total_protein / protein_goal) * 100, 1) if protein_goal > 0 else 0,
                'carbs': round((total_carbs / carbs_goal) * 100, 1) if carbs_goal > 0 else 0,
                'fat': round((total_fat / fat_goal) * 100, 1) if fat_goal > 0 else 0
            },
            'meal_breakdown': NutritionCalculator.get_meal_breakdown(user, target_date)
        }
    
    @staticmethod
    def get_meal_breakdown(user: User, target_date: date) -> Dict[str, Dict[str, float]]:
        """
        Get nutrition breakdown by meal type
        """
        from app import db
        
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        breakdown = {}
        
        for meal_type in meal_types:
            logs = db.session.query(FoodLog).filter_by(
                user_id=user.id,
                log_date=target_date,
                meal_type=meal_type
            ).all()
            
            breakdown[meal_type] = {
                'calories': sum(log.calories or 0 for log in logs),
                'protein': sum(log.protein or 0 for log in logs),
                'carbs': sum(log.carbs or 0 for log in logs),
                'fat': sum(log.fat or 0 for log in logs)
            }
        
        return breakdown
    
    @staticmethod
    def get_latest_weight(user: User) -> Optional[float]:
        """
        Get the user's most recent weight entry
        """
        from app import db
        
        latest_weight = db.session.query(WeightEntry).filter_by(
            user_id=user.id
        ).order_by(WeightEntry.entry_date.desc()).first()
        
        return latest_weight.weight if latest_weight else None
    
    @staticmethod
    def get_weight_progress(user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get weight progress over specified number of days
        """
        from app import db
        
        start_date = date.today() - timedelta(days=days)
        
        weight_entries = db.session.query(WeightEntry).filter(
            WeightEntry.user_id == user.id,
            WeightEntry.entry_date >= start_date
        ).order_by(WeightEntry.entry_date).all()
        
        if not weight_entries:
            return {'entries': [], 'trend': 'no_data', 'change': 0}
        
        entries = [{
            'date': entry.entry_date.isoformat(),
            'weight': entry.weight
        } for entry in weight_entries]
        
        # Calculate trend
        if len(weight_entries) >= 2:
            first_weight = weight_entries[0].weight
            last_weight = weight_entries[-1].weight
            change = last_weight - first_weight
            
            if abs(change) < 0.5:
                trend = 'stable'
            elif change > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
        else:
            trend = 'insufficient_data'
            change = 0
        
        return {
            'entries': entries,
            'trend': trend,
            'change': round(change, 1),
            'latest_weight': weight_entries[-1].weight
        }
    
    @staticmethod
    def get_fitness_recommendations(user: User) -> list:
        """
        Generate fitness recommendations based on user data
        """
        recommendations = []
        
        # Get recent nutrition data
        recent_nutrition = NutritionCalculator.get_daily_nutrition_summary(user)
        weight_progress = NutritionCalculator.get_weight_progress(user)
        
        # Calorie-based recommendations
        calories_percentage = recent_nutrition['percentages']['calories']
        if calories_percentage < 80:
            recommendations.append({
                'type': 'nutrition',
                'message': 'You may be under-eating. Consider adding healthy snacks to meet your calorie goals.',
                'priority': 'medium'
            })
        elif calories_percentage > 120:
            recommendations.append({
                'type': 'nutrition',
                'message': 'You\'re consuming more calories than your goal. Try reducing portion sizes or choosing lower-calorie options.',
                'priority': 'high'
            })
        
        # Protein recommendations
        protein_percentage = recent_nutrition['percentages']['protein']
        if protein_percentage < 80:
            recommendations.append({
                'type': 'nutrition',
                'message': 'Increase your protein intake with lean meats, eggs, beans, or protein shakes.',
                'priority': 'medium'
            })
        
        # Activity recommendations based on goal
        if user.goal == 'lose_weight':
            recommendations.append({
                'type': 'exercise',
                'message': 'Combine cardio exercises (30 min walking/running) with strength training 3-4 times per week.',
                'priority': 'high'
            })
        elif user.goal == 'gain_weight':
            recommendations.append({
                'type': 'exercise',
                'message': 'Focus on strength training and resistance exercises to build muscle mass.',
                'priority': 'high'
            })
        else:
            recommendations.append({
                'type': 'exercise',
                'message': 'Maintain a balanced routine with 150 minutes of moderate cardio per week plus strength training.',
                'priority': 'medium'
            })
        
        # Weight trend recommendations
        if weight_progress['trend'] == 'increasing' and user.goal == 'lose_weight':
            recommendations.append({
                'type': 'warning',
                'message': 'Your weight is trending upward. Consider reviewing your calorie intake and exercise routine.',
                'priority': 'high'
            })
        elif weight_progress['trend'] == 'decreasing' and user.goal == 'gain_weight':
            recommendations.append({
                'type': 'warning',
                'message': 'Your weight is decreasing. Make sure you\'re eating enough calories to support your goals.',
                'priority': 'high'
            })
        
        # Hydration reminder
        recommendations.append({
            'type': 'general',
            'message': 'Don\'t forget to stay hydrated! Aim for 8-10 glasses of water per day.',
            'priority': 'low'
        })
        
        return recommendations
