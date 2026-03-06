"""feat: enable row level security (RLS)

Revision ID: f2c6e8d1a123
Revises: b3377bbff1f0
Create Date: 2026-03-06 14:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f2c6e8d1a123'
down_revision: Union[str, Sequence[str], None] = 'b3377bbff1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add trainer_id to tables if missing
    op.add_column('workout_sessions', sa.Column('trainer_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_workout_sessions_trainer_id'), 'workout_sessions', ['trainer_id'], unique=False)
    
    op.add_column('events', sa.Column('trainer_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_events_trainer_id'), 'events', ['trainer_id'], unique=False)

    # 2. Enable RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE workout_sessions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE events ENABLE ROW LEVEL SECURITY;")

    # 3. Create Policies
    # Users: Admins see all, Trainers see their clients and themselves, Clients see only themselves
    op.execute("""
        CREATE POLICY trainer_access_users ON users
        FOR ALL
        TO authenticated
        USING (
            trainer_id = NULLIF(current_setting('app.current_trainer_id', TRUE), '')
            OR id = NULLIF(current_setting('app.current_trainer_id', TRUE), '')
            OR current_setting('app.is_admin', TRUE) = 'true'
        );
    """)

    # WorkoutSessions: Admins see all, Trainers see their clients' sessions
    op.execute("""
        CREATE POLICY trainer_access_sessions ON workout_sessions
        FOR ALL
        TO authenticated
        USING (
            trainer_id = NULLIF(current_setting('app.current_trainer_id', TRUE), '')
            OR current_setting('app.is_admin', TRUE) = 'true'
        );
    """)

    # Events: Admins see all, Trainers see their clients' events
    op.execute("""
        CREATE POLICY trainer_access_events ON events
        FOR ALL
        TO authenticated
        USING (
            trainer_id = NULLIF(current_setting('app.current_trainer_id', TRUE), '')
            OR current_setting('app.is_admin', TRUE) = 'true'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS trainer_access_events ON events;")
    op.execute("DROP POLICY IF EXISTS trainer_access_sessions ON workout_sessions;")
    op.execute("DROP POLICY IF EXISTS trainer_access_users ON users;")
    
    op.execute("ALTER TABLE events DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE workout_sessions DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    
    op.drop_index(op.f('ix_events_trainer_id'), table_name='events')
    op.drop_column('events', 'trainer_id')
    op.drop_index(op.f('ix_workout_sessions_trainer_id'), table_name='workout_sessions')
    op.drop_column('workout_sessions', 'trainer_id')
