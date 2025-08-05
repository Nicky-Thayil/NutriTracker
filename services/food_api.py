import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OpenFoodFactsAPI:
    BASE_URL = "https://world.openfoodfacts.org/api/v0"
    
    @staticmethod
    def get_product_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
        """
        Fetch product information from Open Food Facts by barcode
        """
        try:
            url = f"{OpenFoodFactsAPI.BASE_URL}/product/{barcode}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 1 and 'product' in data:
                product = data['product']
                
                # Extract nutrition information
                nutriments = product.get('nutriments', {})
                
                # Convert to our standard format
                food_data = {
                    'barcode': barcode,
                    'name': product.get('product_name', 'Unknown Product'),
                    'brand': product.get('brands', '').split(',')[0].strip() if product.get('brands') else None,
                    'calories_per_100g': nutriments.get('energy-kcal_100g'),
                    'protein_per_100g': nutriments.get('proteins_100g'),
                    'carbs_per_100g': nutriments.get('carbohydrates_100g'),
                    'fat_per_100g': nutriments.get('fat_100g'),
                    'fiber_per_100g': nutriments.get('fiber_100g'),
                    'sugar_per_100g': nutriments.get('sugars_100g'),
                    'sodium_per_100g': nutriments.get('sodium_100g')
                }
                
                logger.info(f"Successfully fetched product data for barcode: {barcode}")
                return food_data
            else:
                logger.warning(f"Product not found for barcode: {barcode}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching product data for barcode {barcode}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing barcode {barcode}: {str(e)}")
            return None

    @staticmethod
    def search_products(query: str, page: int = 1, page_size: int = 20) -> list:
        """
        Search for products by name
        """
        try:
            url = f"{OpenFoodFactsAPI.BASE_URL}/cgi/search.pl"
            params = {
                'search_terms': query,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page': page,
                'page_size': page_size
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for product in data.get('products', []):
                if 'product_name' in product:
                    nutriments = product.get('nutriments', {})
                    
                    food_data = {
                        'barcode': product.get('code'),
                        'name': product.get('product_name', 'Unknown Product'),
                        'brand': product.get('brands', '').split(',')[0].strip() if product.get('brands') else None,
                        'calories_per_100g': nutriments.get('energy-kcal_100g'),
                        'protein_per_100g': nutriments.get('proteins_100g'),
                        'carbs_per_100g': nutriments.get('carbohydrates_100g'),
                        'fat_per_100g': nutriments.get('fat_100g'),
                        'fiber_per_100g': nutriments.get('fiber_100g'),
                        'sugar_per_100g': nutriments.get('sugars_100g'),
                        'sodium_per_100g': nutriments.get('sodium_100g')
                    }
                    products.append(food_data)
            
            logger.info(f"Found {len(products)} products for query: {query}")
            return products
            
        except requests.RequestException as e:
            logger.error(f"Error searching products for query {query}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching products for query {query}: {str(e)}")
            return []

class FoodRecognitionAPI:
    """
    Simple food recognition - in a real implementation, this would integrate
    with a computer vision API like Google Vision, AWS Rekognition, or a specialized food API
    """
    
    @staticmethod
    def recognize_food_from_image(image_data: bytes) -> Optional[str]:
        """
        Recognize food from image data
        For this MVP, we'll return common food suggestions
        In production, this would use actual AI/ML services
        """
        # This is a simplified implementation for MVP
        # In production, you would integrate with services like:
        # - Google Vision API
        # - AWS Rekognition
        # - Clarifai Food Model
        # - LogMeal API
        
        common_foods = [
            "apple", "banana", "orange", "bread", "chicken breast", 
            "rice", "pasta", "salad", "sandwich", "pizza",
            "yogurt", "milk", "eggs", "cheese", "vegetables"
        ]
        
        # For MVP, return a random suggestion
        # In production, this would analyze the actual image
        import random
        return random.choice(common_foods)
    
    @staticmethod
    def get_food_suggestions(partial_name: str) -> list:
        """
        Get food suggestions based on partial name
        This could be enhanced with a food database or API
        """
        common_foods = [
            "apple", "apricot", "avocado", "banana", "bread", "broccoli",
            "chicken breast", "chicken thigh", "rice", "brown rice", "pasta",
            "whole wheat pasta", "salad", "caesar salad", "sandwich", "pizza",
            "yogurt", "greek yogurt", "milk", "almond milk", "eggs", "cheese",
            "cheddar cheese", "vegetables", "mixed vegetables", "salmon",
            "tuna", "beef", "pork", "turkey", "quinoa", "oats", "almonds",
            "walnuts", "strawberries", "blueberries", "spinach", "carrots"
        ]
        
        if not partial_name:
            return common_foods[:10]
        
        # Filter foods that contain the partial name
        suggestions = [food for food in common_foods if partial_name.lower() in food.lower()]
        return suggestions[:10]
