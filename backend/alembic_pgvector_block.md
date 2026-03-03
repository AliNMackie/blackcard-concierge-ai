### Alembic `upgrade()` Block for `pgvector` Contextual Memory

When you run `alembic revision --autogenerate -m "add contextual memory"`, Alembic might miss the exact syntax for `CREATE EXTENSION` and the HNSW ops. Replace the generated `upgrade()` and `downgrade()` blocks with exactly this:

```python
import pgvector.sqlalchemy

def upgrade() -> None:
    # 1. Ensure pgvector extension exists BEFORE creating tables
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    # 2. Create InferenceState table
    op.create_table('inference_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('state_vector', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('context_summary', sa.String(), nullable=False),
        sa.Column('resulting_outcome', sa.String(), nullable=True),
        sa.Column('raw_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inference_states_user_id'), 'inference_states', ['user_id'], unique=False)
    
    # 3. Create HNSW index for InferenceState using RAW SQL execution
    op.execute(
        "CREATE INDEX ix_inference_states_vector_hnsw "
        "ON inference_states "
        "USING hnsw (state_vector vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )

    # 4. Create BiomechanicalSignature table
    op.create_table('biomechanical_signatures',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('movement_type', sa.String(), nullable=False),
        sa.Column('is_golden', sa.Boolean(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('kinematic_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biomechanical_signatures_movement_type'), 'biomechanical_signatures', ['movement_type'], unique=False)
    op.create_index(op.f('ix_biomechanical_signatures_user_id'), 'biomechanical_signatures', ['user_id'], unique=False)

    # 5. Create HNSW index for BiomechanicalSignature using RAW SQL execution
    op.execute(
        "CREATE INDEX ix_biomechanical_signatures_vector_hnsw "
        "ON biomechanical_signatures "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index(op.f('ix_biomechanical_signatures_user_id'), table_name='biomechanical_signatures')
    op.drop_index(op.f('ix_biomechanical_signatures_movement_type'), table_name='biomechanical_signatures')
    op.drop_table('biomechanical_signatures')
    
    op.drop_index(op.f('ix_inference_states_user_id'), table_name='inference_states')
    op.drop_table('inference_states')
```
