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

    # All columns that might be missing from products table
    columns_to_add = [
        # From 002_add_cosmetics_fields migration
        ("products", "product_category", "VARCHAR(50) NULL"),
        ("products", "key_ingredients", "JSON NOT NULL DEFAULT ('[]')"),
        ("products", "suitable_skin_types", "JSON NOT NULL DEFAULT ('[]')"),
        ("products", "skin_concerns", "JSON NOT NULL DEFAULT ('[]')"),
        ("products", "texture_type", "VARCHAR(50) NULL"),
        ("products", "finish_type", "VARCHAR(50) NULL"),
        ("products", "certifications", "JSON NOT NULL DEFAULT ('[]')"),
        ("products", "clinical_results", "JSON NOT NULL DEFAULT ('[]')"),
        ("products", "volume_ml", "INT NULL"),
        # From 5cdd9c934f54 migration
        ("products", "image_url", "VARCHAR(500) NULL"),
        ("products", "image_description", "TEXT NULL"),
    ]

    async with engine.begin() as conn:
        for table, column, column_type in columns_to_add:
            try:
                # Check if column exists
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                    AND table_name = '{table}'
                    AND column_name = '{column}'
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

        # Create index if not exists
        try:
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                AND table_name = 'products'
                AND index_name = 'ix_products_product_category'
            """))
            index_exists = result.scalar()

            if not index_exists:
                print("Creating index ix_products_product_category...")
                await conn.execute(text("CREATE INDEX ix_products_product_category ON products(product_category)"))
                print("Index created")
            else:
                print("Index ix_products_product_category already exists")
        except Exception as e:
            print(f"Error creating index: {e}")

    await engine.dispose()
    print("Column fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_columns())
