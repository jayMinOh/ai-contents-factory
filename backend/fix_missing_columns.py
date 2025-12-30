"""Fix missing columns in production database."""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix_columns():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set, skipping column fix")
        return

    engine = create_async_engine(database_url)

    columns_to_add = [
        ("products", "image_url", "VARCHAR(500) NULL"),
        ("products", "image_description", "TEXT NULL"),
    ]

    async with engine.begin() as conn:
        for table, column, column_type in columns_to_add:
            try:
                # Check if column exists
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = '{column}'
                """))
                exists = result.scalar()

                if not exists:
                    print(f"Adding column {table}.{column}...")
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
                    print(f"Added {table}.{column}")
                else:
                    print(f"Column {table}.{column} already exists")
            except Exception as e:
                print(f"Error adding {table}.{column}: {e}")

    await engine.dispose()
    print("Column fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_columns())
