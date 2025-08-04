#!/usr/bin/env python3
"""
Database schema initialization script for Enhanced AI Agent OS v2
"""
import psycopg2
import os
import sys

def init_database_schema():
    """Initialize the database schema using the SQL file."""
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            return False
        
        print(f"🔗 Connecting to database...")
        print(f"Database URL: {database_url[:50]}...")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Read the schema file
        schema_file = '/app/../../../shared/database/01_initial_schema.sql'
        print(f"📄 Reading schema file: {schema_file}")
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        print(f"📝 Schema file contains {len(schema_sql)} characters")
        
        # Execute the schema
        print("🚀 Executing schema...")
        cur.execute(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"✅ Database schema initialized successfully!")
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Test the agents table specifically
        cur.execute("SELECT COUNT(*) FROM agents;")
        agent_count = cur.fetchone()[0]
        print(f"🤖 Agents table ready with {agent_count} records")
        
        conn.close()
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Schema file not found: {e}")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = init_database_schema()
    sys.exit(0 if success else 1)
