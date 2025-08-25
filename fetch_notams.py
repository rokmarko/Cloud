#!/usr/bin/env python3
"""
Scheduled task to fetch NOTAMs every 12 hours.
Can be run as a cron job or standalone script.
"""

import sys
import os
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.services.notam_service import notam_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/notam_fetch.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def fetch_notams():
    """Main function to fetch NOTAMs for all supported areas."""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Starting NOTAM fetch task")
            start_time = datetime.now(timezone.utc)
            
            # Fetch NOTAMs for all areas
            results = notam_service.fetch_all_areas()
            
            # Log results
            total_new = sum(result.get('new_notams', 0) for result in results.values() if 'error' not in result)
            total_updated = sum(result.get('updated_notams', 0) for result in results.values() if 'error' not in result)
            total_errors = sum(1 for result in results.values() if 'error' in result)
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"NOTAM fetch completed in {duration:.2f}s")
            logger.info(f"Total new NOTAMs: {total_new}")
            logger.info(f"Total updated NOTAMs: {total_updated}")
            logger.info(f"Areas with errors: {total_errors}")
            
            # Cleanup old expired NOTAMs
            try:
                cleaned_count = notam_service.cleanup_expired_notams(days_old=30)
                logger.info(f"Cleaned up {cleaned_count} old expired NOTAMs")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
            
            # Log detailed results
            for icao_code, result in results.items():
                if 'error' in result:
                    logger.error(f"{icao_code}: {result['error']}")
                else:
                    logger.info(f"{icao_code}: {result['new_notams']} new, {result['updated_notams']} updated")
            
            return True
            
        except Exception as e:
            logger.error(f"Critical error in NOTAM fetch task: {str(e)}", exc_info=True)
            return False


if __name__ == "__main__":
    success = fetch_notams()
    sys.exit(0 if success else 1)
