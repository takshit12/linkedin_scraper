"""
Connection tracker using SQLite database
"""
import sqlite3
import csv
from datetime import datetime
from typing import Optional, List, Dict
from . import config


class ConnectionTracker:
    """
    Track sent connection requests to prevent duplicates and enable resume capability.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize tracker with database connection.

        Args:
            db_path: Path to SQLite database file (default: from config)
        """
        self.db_path = db_path or config.TRACKING_DB
        self._init_database()

    def _init_database(self):
        """
        Create database tables if they don't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT UNIQUE NOT NULL,
                profile_url TEXT NOT NULL,
                poster_name TEXT,
                job_title TEXT,
                company TEXT,
                sent_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT
            )
        """)

        conn.commit()
        conn.close()

    def already_contacted(self, profile_id: str) -> bool:
        """
        Check if a profile has already been contacted.

        Args:
            profile_id: LinkedIn profile ID

        Returns:
            True if already contacted, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM connections
            WHERE profile_id = ?
        """, (profile_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def mark_as_sent(
        self,
        profile_id: str,
        profile_url: str,
        status: str,
        poster_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Record a sent connection request.

        Args:
            profile_id: LinkedIn profile ID
            profile_url: Full profile URL
            status: Status code ('success', 'already_connected', 'failed', etc.)
            poster_name: Name of the person
            job_title: Job title from the posting
            company: Company name
            error_message: Error message if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO connections (
                    profile_id, profile_url, poster_name, job_title,
                    company, sent_at, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_id,
                profile_url,
                poster_name,
                job_title,
                company,
                datetime.now(),
                status,
                error_message
            ))

            conn.commit()
        except sqlite3.IntegrityError:
            # Already exists (duplicate profile_id)
            pass
        finally:
            conn.close()

    def get_all_sent_connections(self) -> List[Dict]:
        """
        Get all sent connections from database.

        Returns:
            List of connection dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM connections
            ORDER BY sent_at DESC
        """)

        rows = cursor.fetchall()
        connections = [dict(row) for row in rows]

        conn.close()
        return connections

    def get_connections_by_status(self, status: str) -> List[Dict]:
        """
        Get connections filtered by status.

        Args:
            status: Status to filter by ('success', 'failed', etc.)

        Returns:
            List of connection dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM connections
            WHERE status = ?
            ORDER BY sent_at DESC
        """, (status,))

        rows = cursor.fetchall()
        connections = [dict(row) for row in rows]

        conn.close()
        return connections

    def get_statistics(self) -> Dict:
        """
        Get statistics about sent connections.

        Returns:
            Dictionary with counts and percentages
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total connections
        cursor.execute("SELECT COUNT(*) FROM connections")
        total = cursor.fetchone()[0]

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM connections
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())

        conn.close()

        return {
            'total': total,
            'success': status_counts.get('success', 0),
            'already_connected': status_counts.get('already_connected', 0),
            'failed': status_counts.get('failed', 0),
            'by_status': status_counts
        }

    def export_to_csv(self, output_file: str):
        """
        Export all connections to CSV file.

        Args:
            output_file: Path to output CSV file
        """
        connections = self.get_all_sent_connections()

        if not connections:
            print("⚠️  No connections to export")
            return

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'profile_id',
                'profile_url',
                'poster_name',
                'job_title',
                'company',
                'sent_at',
                'status',
                'error_message'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for conn in connections:
                writer.writerow({
                    'profile_id': conn['profile_id'],
                    'profile_url': conn['profile_url'],
                    'poster_name': conn['poster_name'] or '',
                    'job_title': conn['job_title'] or '',
                    'company': conn['company'] or '',
                    'sent_at': conn['sent_at'],
                    'status': conn['status'],
                    'error_message': conn['error_message'] or ''
                })

        print(f"✓ Exported {len(connections)} connections to {output_file}")

    def clear_all(self):
        """
        Clear all connections from database.
        USE WITH CAUTION - This deletes all history.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM connections")
        conn.commit()
        conn.close()

        print("⚠️  Cleared all connection history")
