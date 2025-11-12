"""
Safety manager for enforcing rate limits and quotas
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple
from . import config


class SafetyManager:
    """
    Enforce daily and weekly connection request quotas.
    Prevents exceeding LinkedIn's rate limits.
    """

    def __init__(self, db_path: str = None, daily_limit: int = None, weekly_limit: int = None):
        """
        Initialize safety manager.

        Args:
            db_path: Path to tracking database (default: from config)
            daily_limit: Custom daily limit (default: from config)
            weekly_limit: Custom weekly limit (default: from config)
        """
        self.db_path = db_path or config.TRACKING_DB
        self.daily_limit = daily_limit or config.DAILY_LIMIT
        self.weekly_limit = weekly_limit or config.WEEKLY_LIMIT

    def get_requests_today(self) -> int:
        """
        Count connection requests sent today.

        Returns:
            Number of requests sent today
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get today's date at midnight
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        cursor.execute("""
            SELECT COUNT(*) FROM connections
            WHERE sent_at >= ?
            AND status = 'success'
        """, (today_start,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_requests_this_week(self) -> int:
        """
        Count connection requests sent in the last 7 days.

        Returns:
            Number of requests sent this week
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get timestamp 7 days ago
        week_ago = datetime.now() - timedelta(days=7)

        cursor.execute("""
            SELECT COUNT(*) FROM connections
            WHERE sent_at >= ?
            AND status = 'success'
        """, (week_ago,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def can_send_request(self) -> Tuple[bool, str]:
        """
        Check if a connection request can be sent without exceeding quotas.

        Returns:
            Tuple of (can_send: bool, reason: str)
            If can_send is False, reason explains why
        """
        requests_today = self.get_requests_today()
        requests_this_week = self.get_requests_this_week()

        if requests_today >= self.daily_limit:
            return False, f"Daily limit reached ({requests_today}/{self.daily_limit})"

        if requests_this_week >= self.weekly_limit:
            return False, f"Weekly limit reached ({requests_this_week}/{self.weekly_limit})"

        return True, "OK"

    def get_quota_status(self) -> dict:
        """
        Get current quota usage status.

        Returns:
            Dictionary with daily/weekly usage and remaining quota
        """
        requests_today = self.get_requests_today()
        requests_this_week = self.get_requests_this_week()

        return {
            'daily_used': requests_today,
            'daily_limit': self.daily_limit,
            'daily_remaining': max(0, self.daily_limit - requests_today),
            'weekly_used': requests_this_week,
            'weekly_limit': self.weekly_limit,
            'weekly_remaining': max(0, self.weekly_limit - requests_this_week),
            'can_send': requests_today < self.daily_limit and requests_this_week < self.weekly_limit
        }

    def print_quota_status(self):
        """
        Print current quota status to console.
        """
        status = self.get_quota_status()

        print("\n📊 Quota Status:")
        print(f"   Daily:  {status['daily_used']}/{status['daily_limit']} used ({status['daily_remaining']} remaining)")
        print(f"   Weekly: {status['weekly_used']}/{status['weekly_limit']} used ({status['weekly_remaining']} remaining)")

        if not status['can_send']:
            if status['daily_used'] >= self.daily_limit:
                print(f"   ⚠️  Daily limit reached! Cannot send more today.")
            elif status['weekly_used'] >= self.weekly_limit:
                print(f"   ⚠️  Weekly limit reached! Wait until next week.")

    def register_request(self):
        """
        Register that a connection request was sent.
        This increments the daily/weekly counters.

        Note: This is automatically handled by ConnectionTracker.mark_as_sent()
        so you don't need to call this separately.
        """
        # This is a placeholder - actual registration happens in tracker
        pass

    def get_daily_reset_time(self) -> datetime:
        """
        Get the time when daily quota resets (midnight tonight).

        Returns:
            Datetime of next daily reset
        """
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return tomorrow

    def get_hours_until_daily_reset(self) -> float:
        """
        Get hours remaining until daily quota resets.

        Returns:
            Hours until midnight (daily reset)
        """
        reset_time = self.get_daily_reset_time()
        delta = reset_time - datetime.now()
        return delta.total_seconds() / 3600

    def suggest_next_run_time(self) -> str:
        """
        Suggest when to run the automation next based on current quota.

        Returns:
            Human-readable suggestion
        """
        status = self.get_quota_status()

        if status['daily_remaining'] > 0 and status['weekly_remaining'] > 0:
            return "You can run now!"

        if status['daily_used'] >= self.daily_limit:
            hours = self.get_hours_until_daily_reset()
            return f"Daily limit reached. Try again in {hours:.1f} hours (after midnight)."

        if status['weekly_used'] >= self.weekly_limit:
            # Calculate when week resets (7 days from oldest request in past week)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sent_at FROM connections
                WHERE sent_at >= datetime('now', '-7 days')
                AND status = 'success'
                ORDER BY sent_at ASC
                LIMIT 1
            """)

            row = cursor.fetchone()
            conn.close()

            if row:
                oldest_request = datetime.fromisoformat(row[0])
                reset_time = oldest_request + timedelta(days=7)
                hours_until_reset = (reset_time - datetime.now()).total_seconds() / 3600

                return f"Weekly limit reached. Try again in {hours_until_reset:.1f} hours."

            return "Weekly limit reached. Wait 7 days from first request."

        return "Check quota status"
