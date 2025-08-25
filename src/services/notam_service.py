"""
NOTAM service for automatically fetching, parsing, and storing NOTAMs.
Includes change detection and email notifications.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from flask_mail import Message

from src.app import db, mail
from src.models import Notam, NotamUpdateLog, NotamNotificationSent, User
from src.notam import fetch_and_parse_notams

logger = logging.getLogger(__name__)


class NotamService:
    """Service for managing NOTAM operations."""
    
    SUPPORTED_AREAS = ['LJLA', 'EDMM', 'LOVV', 'LHCC', 'LKAA']
    
    def __init__(self):
        self.db = db
    
    def fetch_all_areas(self) -> Dict[str, Any]:
        """
        Fetch NOTAMs for all supported areas.
        
        Returns:
            Dictionary with results for each area
        """
        results = {}
        
        for icao_code in self.SUPPORTED_AREAS:
            try:
                logger.info(f"Fetching NOTAMs for {icao_code}")
                result = self.fetch_and_store_notams(icao_code)
                results[icao_code] = result
            except Exception as e:
                logger.error(f"Error fetching NOTAMs for {icao_code}: {str(e)}")
                results[icao_code] = {'error': str(e)}
        
        return results
    
    def fetch_and_store_notams(self, icao_code: str) -> Dict[str, Any]:
        """
        Fetch NOTAMs for a specific ICAO code and store in database.
        
        Args:
            icao_code: 4-letter ICAO code
            
        Returns:
            Dictionary with operation results
        """
        start_time = datetime.now(timezone.utc)
        stats = {
            'total_fetched': 0,
            'new_notams': 0,
            'updated_notams': 0,
            'expired_notams': 0,
            'errors': []
        }
        
        try:
            # Fetch and parse NOTAMs
            notam_data = fetch_and_parse_notams(icao_code)
            stats['total_fetched'] = len(notam_data.get('notams', []))
            
            # Get existing NOTAMs for this area
            existing_notams = {
                notam.notam_id: notam 
                for notam in Notam.query.filter_by(icao_code=icao_code).all()
            }
            
            current_notam_ids = set()
            
            # Process each fetched NOTAM
            for notam_raw in notam_data.get('notams', []):
                try:
                    notam_id = notam_raw.get('id')
                    if not notam_id:
                        continue
                    
                    current_notam_ids.add(notam_id)
                    
                    if notam_id in existing_notams:
                        # Update existing NOTAM
                        updated = self._update_notam(existing_notams[notam_id], notam_raw)
                        if updated:
                            stats['updated_notams'] += 1
                    else:
                        # Create new NOTAM
                        self._create_notam(icao_code, notam_raw)
                        stats['new_notams'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing NOTAM {notam_raw.get('id', 'unknown')}: {str(e)}")
                    stats['errors'].append(str(e))
            
            # Mark NOTAMs as expired if they're not in the current fetch
            for notam_id, notam in existing_notams.items():
                if notam_id not in current_notam_ids:
                    # Check if it's actually expired or just not in current data
                    if notam.valid_until and notam.valid_until < datetime.now(timezone.utc):
                        # Already expired, keep as is
                        continue
                    # Otherwise, we might want to keep it active
                    # This depends on the data source behavior
            
            # Commit all changes
            self.db.session.commit()
            
            # Log the update
            self._log_update(icao_code, stats, 'success')
            
            # Send notifications for new/updated NOTAMs
            if stats['new_notams'] > 0 or stats['updated_notams'] > 0:
                self._send_notifications(icao_code, current_notam_ids)
            
            logger.info(f"NOTAM update completed for {icao_code}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_notams for {icao_code}: {str(e)}")
            self.db.session.rollback()
            self._log_update(icao_code, stats, 'error', str(e))
            stats['errors'].append(str(e))
            raise
    
    def _create_notam(self, icao_code: str, notam_data: Dict[str, Any]) -> Notam:
        """Create a new NOTAM from parsed data."""
        q_line = notam_data.get('q_line', {})
        coords = q_line.get('coords', {})
        
        # Parse validity dates
        valid_from = None
        valid_until = None
        is_permanent = False
        
        if notam_data.get('valid_from'):
            try:
                if isinstance(notam_data['valid_from'], str):
                    valid_from = datetime.fromisoformat(notam_data['valid_from'].replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Could not parse valid_from: {notam_data['valid_from']}")
        
        if notam_data.get('valid_until'):
            if notam_data['valid_until'] == 'PERMANENT':
                is_permanent = True
            else:
                try:
                    if isinstance(notam_data['valid_until'], str):
                        valid_until = datetime.fromisoformat(notam_data['valid_until'].replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Could not parse valid_until: {notam_data['valid_until']}")
        
        # Parse created time
        created_time = None
        if notam_data.get('created', {}).get('iso'):
            try:
                created_time = datetime.fromisoformat(notam_data['created']['iso'].replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Could not parse created time: {notam_data['created']}")
        
        notam = Notam(
            notam_id=notam_data['id'],
            icao_code=icao_code,
            raw_text=notam_data.get('raw', ''),
            
            # Q-line data
            fir=q_line.get('fir'),
            q_code=q_line.get('code'),
            q_code_meaning=q_line.get('code_meaning'),
            traffic_type=q_line.get('traffic'),
            purpose=q_line.get('purpose'),
            scope=q_line.get('scope'),
            
            # Altitude limits
            lower_limit_raw=q_line.get('lower_limit', {}).get('raw'),
            lower_limit_feet=q_line.get('lower_limit', {}).get('feet'),
            upper_limit_raw=q_line.get('upper_limit', {}).get('raw'),
            upper_limit_feet=q_line.get('upper_limit', {}).get('feet'),
            
            # Coordinates
            latitude=coords.get('latitude'),
            longitude=coords.get('longitude'),
            radius_nm=coords.get('radius_nm'),
            
            # Validity
            valid_from=valid_from,
            valid_until=valid_until,
            is_permanent=is_permanent,
            
            # Content
            location=notam_data.get('location'),
            body=notam_data.get('body'),
            f_limit_text=notam_data.get('f_limit', {}).get('raw') if notam_data.get('f_limit') else None,
            g_limit_text=notam_data.get('g_limit', {}).get('raw') if notam_data.get('g_limit') else None,
            
            # Metadata
            created_time=created_time,
            source=notam_data.get('source')
        )
        
        self.db.session.add(notam)
        return notam
    
    def _update_notam(self, existing_notam: Notam, notam_data: Dict[str, Any]) -> bool:
        """
        Update an existing NOTAM if data has changed.
        
        Returns:
            True if NOTAM was updated, False if no changes
        """
        updated = False
        
        # Check if raw text has changed (main indicator of update)
        new_raw_text = notam_data.get('raw', '')
        if existing_notam.raw_text != new_raw_text:
            existing_notam.raw_text = new_raw_text
            
            # Update other fields from new data
            q_line = notam_data.get('q_line', {})
            coords = q_line.get('coords', {})
            
            existing_notam.body = notam_data.get('body')
            existing_notam.latitude = coords.get('latitude')
            existing_notam.longitude = coords.get('longitude')
            existing_notam.radius_nm = coords.get('radius_nm')
            
            # Update validity if changed
            if notam_data.get('valid_until') == 'PERMANENT':
                existing_notam.is_permanent = True
                existing_notam.valid_until = None
            elif notam_data.get('valid_until'):
                try:
                    new_valid_until = datetime.fromisoformat(notam_data['valid_until'].replace('Z', '+00:00'))
                    if existing_notam.valid_until != new_valid_until:
                        existing_notam.valid_until = new_valid_until
                except Exception:
                    pass
            
            existing_notam.updated_at = datetime.now(timezone.utc)
            updated = True
        
        return updated
    
    def _log_update(self, icao_code: str, stats: Dict[str, Any], status: str, error_message: str = None):
        """Log the NOTAM update operation."""
        log_entry = NotamUpdateLog(
            icao_code=icao_code,
            total_notams=stats['total_fetched'],
            new_notams=stats['new_notams'],
            updated_notams=stats['updated_notams'],
            expired_notams=stats['expired_notams'],
            status=status,
            error_message=error_message
        )
        
        self.db.session.add(log_entry)
        
        # Don't commit here, let the caller handle it
    
    def _send_notifications(self, icao_code: str, notam_ids: Set[str]):
        """Send email notifications to users with this home area."""
        try:
            # Get users who have this as their home area
            users = User.query.filter_by(home_area=icao_code).all()
            
            if not users:
                return
            
            # Get NOTAMs that haven't been notified about yet
            recent_notams = (
                Notam.query
                .filter(
                    Notam.icao_code == icao_code,
                    Notam.notam_id.in_(notam_ids),
                    Notam.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)  # Recent NOTAMs
                )
                .all()
            )
            
            if not recent_notams:
                return
            
            for user in users:
                # Check which NOTAMs we haven't notified this user about
                already_notified = {
                    ns.notam_id for ns in 
                    NotamNotificationSent.query
                    .join(Notam)
                    .filter(
                        NotamNotificationSent.user_id == user.id,
                        Notam.notam_id.in_(notam_ids)
                    )
                    .all()
                }
                
                new_notams_for_user = [
                    notam for notam in recent_notams 
                    if notam.id not in already_notified
                ]
                
                if new_notams_for_user:
                    self._send_notification_email(user, new_notams_for_user)
                    
                    # Mark as sent
                    for notam in new_notams_for_user:
                        notification = NotamNotificationSent(
                            user_id=user.id,
                            notam_id=notam.id,
                            notification_type='new'
                        )
                        self.db.session.add(notification)
        
        except Exception as e:
            logger.error(f"Error sending notifications for {icao_code}: {str(e)}")
    
    def _send_notification_email(self, user: User, notams: List[Notam]):
        """Send email notification to user about new NOTAMs."""
        try:
            if not current_app.config.get('MAIL_SERVER'):
                logger.warning("Email not configured, skipping notification")
                return
            
            subject = f"New NOTAMs for {notams[0].icao_code} - KanardiaCloud"
            
            # Build email content
            notam_summaries = []
            for notam in notams:
                summary = f"• {notam.notam_id}: {notam.q_code_meaning or 'NOTAM'}"
                if notam.body:
                    # Truncate body to first 100 characters
                    body_preview = notam.body[:100] + "..." if len(notam.body) > 100 else notam.body
                    summary += f"\n  {body_preview}"
                notam_summaries.append(summary)
            
            email_body = f"""Hello {user.nickname},

New NOTAMs have been issued for your home area {notams[0].icao_code}:

{chr(10).join(notam_summaries)}

You can view complete NOTAM details in your KanardiaCloud dashboard.

This is an automated notification. To change your NOTAM notification preferences, visit your user settings.

Best regards,
KanardiaCloud Team
"""
            
            msg = Message(
                subject=subject,
                recipients=[user.email],
                body=email_body
            )
            
            mail.send(msg)
            logger.info(f"NOTAM notification sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {str(e)}")
    
    def get_active_notams(self, icao_code: str = None, check_date: datetime = None) -> List[Notam]:
        """Get active NOTAMs for a specific area or all areas."""
        if check_date is None:
            check_date = datetime.now(timezone.utc)
        
        # Convert to naive datetime for database comparison if it's timezone-aware
        if check_date.tzinfo is not None:
            check_date_naive = check_date.replace(tzinfo=None)
        else:
            check_date_naive = check_date
        
        query = Notam.query
        
        if icao_code:
            query = query.filter_by(icao_code=icao_code)
        
        # Filter for active NOTAMs
        query = query.filter(
            db.or_(
                # Permanent NOTAMs that have started
                db.and_(
                    Notam.is_permanent == True,
                    db.or_(
                        Notam.valid_from.is_(None),
                        Notam.valid_from <= check_date_naive
                    )
                ),
                # Temporary NOTAMs within validity period
                db.and_(
                    Notam.is_permanent == False,
                    Notam.valid_from <= check_date_naive,
                    Notam.valid_until >= check_date_naive
                )
            )
        )
        
        return query.order_by(Notam.valid_from.desc()).all()
    
    def cleanup_expired_notams(self, days_old: int = 30):
        """Remove NOTAMs that have been expired for more than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        expired_notams = (
            Notam.query
            .filter(
                Notam.is_permanent == False,
                Notam.valid_until < cutoff_date
            )
            .all()
        )
        
        count = len(expired_notams)
        
        for notam in expired_notams:
            self.db.session.delete(notam)
        
        self.db.session.commit()
        logger.info(f"Cleaned up {count} expired NOTAMs older than {days_old} days")
        
        return count


# Singleton instance
notam_service = NotamService()
