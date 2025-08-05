# NutriTracker

## Overview

NutriTracker is a comprehensive nutrition and fitness tracking web application built with Flask. The platform enables users to monitor their daily food intake, track weight progress, and receive personalized nutrition recommendations. Key features include barcode scanning for food products, AI-powered food recognition through camera capture, comprehensive nutrition analytics, and integration with the Open Food Facts database for accurate nutritional information.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM for database operations
- **Database**: PostgreSQL with SQLAlchemy models for data persistence
- **Authentication**: Replit Auth integration using OAuth2 with Flask-Dance for secure user authentication
- **Session Management**: Flask-Login for user session handling with persistent sessions

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI design
- **Styling**: Custom CSS with Bootstrap theme optimized for dark mode
- **JavaScript**: Vanilla JavaScript with Bootstrap components for interactive features
- **Charts**: Chart.js for nutrition and weight progress visualization

### Data Models
- **User Model**: Stores user profile information including age, gender, height, activity level, and daily calorie goals
- **Food Model**: Manages food database with nutritional information per 100g
- **FoodLog Model**: Tracks daily food consumption with portion sizes and meal types
- **WeightEntry Model**: Records weight measurements over time for progress tracking
- **OAuth Model**: Handles authentication tokens and browser session management

### Core Services
- **NutritionCalculator**: Calculates BMR, TDEE, daily nutrition summaries, and provides fitness recommendations
- **OpenFoodFactsAPI**: Integrates with external food database for product information via barcode scanning
- **FoodRecognitionAPI**: Processes camera-captured images for AI-powered food identification

### Security Features
- Session-based authentication with secure token storage
- CSRF protection and secure cookie handling
- Database connection pooling with automatic reconnection
- Input validation and SQL injection prevention through ORM

## External Dependencies

### Third-Party APIs
- **Open Food Facts API**: Provides comprehensive food product database with nutritional information
- **Food Recognition API**: AI service for identifying food items from camera images

### Frontend Libraries
- **Bootstrap 5**: UI framework with Replit-optimized dark theme
- **Bootstrap Icons**: Icon library for consistent visual elements
- **Chart.js**: Data visualization library for nutrition and weight charts
- **ZXing Library**: JavaScript barcode scanning capability

### Development Tools
- **Flask-Dance**: OAuth integration for Replit authentication
- **Flask-Login**: User session management
- **SQLAlchemy**: Database ORM with migration support
- **Werkzeug**: WSGI utilities and middleware

### Browser APIs
- **getUserMedia**: Camera access for barcode scanning and food recognition
- **Canvas API**: Image processing for food capture functionality
- **LocalStorage**: Client-side data persistence for user preferences