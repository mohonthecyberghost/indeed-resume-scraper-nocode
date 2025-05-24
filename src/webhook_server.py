from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
from scraper import IndeedResumeScraper
import logging
from dotenv import load_dotenv
import traceback

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape_resumes():
    try:
        # Get request data
        data = request.get_json()
        logger.debug(f"Received request data: {data}")
        
        # Validate required fields
        required_fields = ['keywords', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Initialize scraper
        logger.debug("Initializing scraper...")
        scraper = IndeedResumeScraper()
        
        # Login to Indeed
        logger.debug("Attempting to login...")
        if not scraper.login():
            return jsonify({
                'error': 'Failed to login to Indeed'
            }), 500
        
        # Perform search
        logger.debug("Starting resume search...")
        results = scraper.search_resumes(data)
        
        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_path = os.path.join(output_dir, f'results_{timestamp}.csv')
        scraper.export_to_csv(results, csv_path)
        
        # Cleanup
        scraper.cleanup()
        
        # Return results
        return jsonify({
            'status': 'success',
            'message': f'Found {len(results)} results',
            'results': results,
            'csv_path': csv_path
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 