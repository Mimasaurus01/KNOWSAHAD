# app.py - Main Flask Application for Hospital Navigation Chatbot

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from fuzzywuzzy import fuzz, process
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
UPLOAD_FOLDER = 'static/images'
LOCATIONS_FILE = 'data/locations.json'
CONVERSATIONS_FILE = 'data/conversations.json'

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class HospitalNavigationBot:
    def __init__(self):
        self.locations = self.load_locations()
        self.conversation_history = {}
        
    def load_locations(self):
        """Load hospital locations from JSON file"""
        if os.path.exists(LOCATIONS_FILE):
            with open(LOCATIONS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create sample data structure - replace with your actual data
            sample_data = {
                "ground_floor": [
                    {
                        "id": 1,
                        "name": "Main Reception",
                        "aliases": ["reception", "front desk", "information", "help desk"],
                        "description": "Main information and registration point",
                        "directions": "Located immediately after the main entrance",
                        "coordinates": {"x": 100, "y": 50},
                        "image": "reception.jpg",
                        "department": "General",
                        "services": ["Registration", "Information", "Visitor passes"]
                    }
                ]
            }
            self.save_locations(sample_data)
            return sample_data
    
    def save_locations(self, data):
        """Save locations to JSON file"""
        with open(LOCATIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def find_location(self, query):
        """Find best matching location using fuzzy string matching"""
        query = query.lower().strip()
        best_matches = []
        
        for floor, locations in self.locations.items():
            for location in locations:
                # Check name match
                name_score = fuzz.ratio(query, location['name'].lower())
                
                # Check aliases
                alias_scores = [fuzz.ratio(query, alias.lower()) for alias in location['aliases']]
                best_alias_score = max(alias_scores) if alias_scores else 0
                
                # Check description keywords
                desc_score = fuzz.partial_ratio(query, location['description'].lower())
                
                # Calculate overall score
                overall_score = max(name_score, best_alias_score, desc_score * 0.8)
                
                if overall_score > 60:  # Threshold for valid matches
                    best_matches.append({
                        'location': location,
                        'score': overall_score,
                        'floor': floor
                    })
        
        # Sort by score and return best matches
        best_matches.sort(key=lambda x: x['score'], reverse=True)
        return best_matches[:3]  # Return top 3 matches
    
    def get_directions(self, from_location, to_location):
        """Generate directions between two locations"""
        # This is a simplified version - you can enhance with actual pathfinding
        return f"From {from_location}, walk to {to_location}. Follow the signs and ask staff if you need help."
    
    def generate_response(self, user_message, session_id):
        """Generate bot response based on user message"""
        user_message = user_message.strip().lower()
        
        # Initialize conversation history for new sessions
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Store user message
        self.conversation_history[session_id].append({
            'type': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate response based on message content
        response = self.process_message(user_message, session_id)
        
        # Store bot response
        self.conversation_history[session_id].append({
            'type': 'bot',
            'message': response['text'],
            'timestamp': datetime.now().isoformat(),
            'data': response.get('data')
        })
        
        return response
    
    def process_message(self, message, session_id):
        """Process user message and return appropriate response"""
        
        # Greeting patterns
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'help' 'yo']
        if any(greeting in message for greeting in greetings):
            return {
                'text': "Hello! Welcome to Sahad Hospital. I'm here to help you navigate our facility. You can ask me about:\n\n• Finding departments (e.g., 'Where is the emergency room?')\n• Getting directions\n• Hospital services\n• General information\n\nHow can I help you today?",
                'type': 'greeting'
            }
        
        # Location search patterns
        location_keywords = ['where', 'find', 'location', 'directions', 'how to get','navigate','lead me']
        if any(keyword in message for keyword in location_keywords):
            matches = self.find_location(message)
            
            if matches:
                best_match = matches[0]
                location = best_match['location']
                
                response_text = f"📍 **{location['name']}**\n\n"
                response_text += f"📝 {location['description']}\n\n"
                response_text += f"🚶 **Directions:** {location['directions']}\n\n"
                response_text += f"🏢 **Department:** {location['department']}\n\n"
                
                if location['services']:
                    response_text += f"🔧 **Services:** {', '.join(location['services'])}\n\n"
                
                if len(matches) > 1:
                    response_text += "\n**Other similar locations:**\n"
                    for match in matches[1:]:
                        response_text += f"• {match['location']['name']}\n"
                
                return {
                    'text': response_text,
                    'type': 'location_info',
                    'data': {
                        'location': location,
                        'alternatives': [m['location'] for m in matches[1:]]
                    }
                }
            else:
                return {
                    'text': "I couldn't find that location. Could you try asking differently? For example:\n• 'Where is the emergency room?'\n• 'Find the reception'\n• 'How do I get to the pharmacy?'",
                    'type': 'location_not_found'
                }
        
        # Emergency keywords
        emergency_keywords = ['emergency', 'urgent', 'help', 'accident', 'pain']
        if any(keyword in message for keyword in emergency_keywords):
            return {
                'text': "🚨 **For medical emergencies, please go directly to our Emergency Room:**\n\n📍 From Ground Floor Section, take the exit near Gynecology that leads to Emergency, ANC, and Labor Ward\n📞 For immediate assistance, call extension 911 or ask any staff member\n\nIs this a medical emergency, or can I help you find the emergency room?",
                'type': 'emergency_response'
            }
        
        # General help
        return {
            'text': "I can help you navigate Sahad Hospital! Try asking me:\n\n• 'Where is the emergency room?'\n• 'Find the pharmacy'\n• 'How do I get to the laboratory?'\n• 'Where is the reception?'\n\nWhat location are you looking for?",
            'type': 'general_help'
        }

# Initialize the bot
bot = HospitalNavigationBot()

# API Routes
@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        response = bot.generate_response(user_message, session_id)
        
        return jsonify({
            'response': response['text'],
            'type': response.get('type', 'general'),
            'data': response.get('data'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all hospital locations"""
    return jsonify(bot.locations)

@app.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    """Get specific location by ID"""
    for floor, locations in bot.locations.items():
        for location in locations:
            if location['id'] == location_id:
                return jsonify({
                    'location': location,
                    'floor': floor
                })
    return jsonify({'error': 'Location not found'}), 404

@app.route('/api/search', methods=['GET'])
def search_locations():
    """Search locations"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    matches = bot.find_location(query)
    return jsonify({
        'matches': matches,
        'count': len(matches)
    })

@app.route('/api/directions', methods=['POST'])
def get_directions():
    """Get directions between two points"""
    data = request.json
    from_loc = data.get('from')
    to_loc = data.get('to')
    
    if not from_loc or not to_loc:
        return jsonify({'error': 'Both from and to locations are required'}), 400
    
    directions = bot.get_directions(from_loc, to_loc)
    return jsonify({'directions': directions})

@app.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation_history(session_id):
    """Get conversation history for a session"""
    history = bot.conversation_history.get(session_id, [])
    return jsonify({'history': history})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'locations_count': sum(len(locations) for locations in bot.locations.values())
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🏥 Starting Hospital Navigation Chatbot Backend...")
    print("📍 Available endpoints:")
    print("   POST /api/chat - Main chatbot interaction")
    print("   GET  /api/locations - Get all locations")
    print("   GET  /api/search?q=query - Search locations")
    print("   GET  /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)