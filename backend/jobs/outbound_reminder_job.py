#!/usr/bin/env python3
"""
Background job for sending outbound reminder conversations
This would typically be run as a cron job or scheduled task
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import SessionLocal
from services.outbound_conversation_service import process_outbound_reminders
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/outbound_reminders.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_outbound_reminder_job(hours_before: int = 24):
    """
    Main job function to send outbound reminders
    """
    
    logger.info(f"Starting outbound reminder job for appointments in next {hours_before} hours")
    
    try:
        db = SessionLocal()
        
        # Process outbound reminders
        result = process_outbound_reminders(db, hours_before)
        
        logger.info(f"Outbound reminder job completed:")
        logger.info(f"  - Total processed: {result['total_processed']}")
        logger.info(f"  - Successful: {result['successful']}")
        logger.info(f"  - Failed: {result['failed']}")
        
        # Log individual results
        for reminder_result in result['results']:
            if reminder_result['status'] == 'reminder_sent':
                logger.info(f"  ✓ Sent to patient {reminder_result['patient_id']} ({reminder_result['patient_name']})")
            else:
                logger.error(f"  ✗ Failed for patient {reminder_result['patient_id']}: {reminder_result.get('error', 'Unknown error')}")
        
        db.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Outbound reminder job failed: {str(e)}")
        raise


def run_urgent_reminders():
    """Send urgent reminders (2 hours before)"""
    return run_outbound_reminder_job(hours_before=2)


def run_daily_reminders():
    """Send daily reminders (24 hours before)"""
    return run_outbound_reminder_job(hours_before=24)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Send outbound appointment reminders')
    parser.add_argument('--hours', type=int, default=24, help='Hours before appointment to send reminders')
    parser.add_argument('--urgent', action='store_true', help='Send urgent reminders (2 hours before)')
    
    args = parser.parse_args()
    
    if args.urgent:
        logger.info("Running urgent reminder job")
        result = run_urgent_reminders()
    else:
        logger.info(f"Running reminder job for {args.hours} hours before")
        result = run_outbound_reminder_job(args.hours)
    
    print(f"Job completed: {result['successful']} successful, {result['failed']} failed")