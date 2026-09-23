import json
import sqlite3


DATABASE_NAME = "erp_history.db"


def initialize_database():

    with sqlite3.connect(DATABASE_NAME) as connection:

        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            erp_system TEXT,
            error TEXT,
            error_meaning TEXT,
            possible_causes TEXT,
            what_to_check TEXT,
            suggested_resolution TEXT,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """)

        connection.commit()


def save_analysis(
    erp_system,
    error,
    data
):

    with sqlite3.connect(DATABASE_NAME) as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO history (
                erp_system,
                error,
                error_meaning,
                possible_causes,
                what_to_check,
                suggested_resolution
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                erp_system,
                error,
                data.get(
                    "error_meaning",
                    ""
                ),
                json.dumps(
                    data.get(
                        "possible_causes",
                        []
                    )
                ),
                json.dumps(
                    data.get(
                        "what_to_check",
                        []
                    )
                ),
                data.get(
                    "suggested_resolution",
                    ""
                )
            )
        )

        connection.commit()


def get_recent_analyses(limit=5):

    with sqlite3.connect(DATABASE_NAME) as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                erp_system,
                error,
                error_meaning,
                possible_causes,
                what_to_check,
                suggested_resolution,
                created_at
            FROM history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        return cursor.fetchall()