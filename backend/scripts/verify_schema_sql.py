from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from app.models import DocumentChunk
from app.database import engine

def verify_schema():
    """
    Compiles the DocumentChunk model to SQL DDL and checks for vector column.
    """
    # Create a mock engine/dialect for compilation
    dialect = postgresql.dialect()
    ddl = CreateTable(DocumentChunk.__table__).compile(dialect=dialect)
    sql_str = str(ddl)
    
    print("Generated DDL:")
    print(sql_str)
    
    # Assertions
    if "embedding vector(768)" in sql_str.lower() or "embedding vector(768)" in sql_str:
        print("\nSUCCESS: Vector column correctly defined with 768 dimensions.")
    else:
        print("\nFAILURE: Vector column missing or incorrect.")
        exit(1)

if __name__ == "__main__":
    verify_schema()
