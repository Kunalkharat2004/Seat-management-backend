"""rename user_id to employee_id in bookings

Revision ID: 415b74810095
Revises: 235c3d6313a6
Create Date: 2026-02-24 15:09:08.677962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '415b74810095'
down_revision: Union[str, None] = '235c3d6313a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column with data preservation
    op.alter_column('bookings', 'user_id', new_column_name='employee_id')
    
    # Update indices and constraints
    op.drop_index('ix_bookings_user_id', table_name='bookings')
    op.create_index(op.f('ix_bookings_employee_id'), 'bookings', ['employee_id'], unique=False)
    
    op.drop_constraint('uq_user_booking_date', 'bookings', type_='unique')
    op.create_unique_constraint('uq_employee_booking_date', 'bookings', ['employee_id', 'booking_date'])
    
    op.drop_constraint('bookings_user_id_fkey', 'bookings', type_='foreignkey')
    # Assign a name to the new FK constraint for easier management later
    op.create_foreign_key('bookings_employee_id_fkey', 'bookings', 'users', ['employee_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Reverse column rename
    op.alter_column('bookings', 'employee_id', new_column_name='user_id')
    
    # Reverse indices and constraints
    op.drop_index(op.f('ix_bookings_employee_id'), table_name='bookings')
    # Re-create original index
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'], unique=False)
    
    op.drop_constraint('uq_employee_booking_date', 'bookings', type_='unique')
    op.create_unique_constraint('uq_user_booking_date', 'bookings', ['user_id', 'booking_date'])
    
    op.drop_constraint('bookings_employee_id_fkey', 'bookings', type_='foreignkey')
    op.create_foreign_key('bookings_user_id_fkey', 'bookings', 'users', ['user_id'], ['id'], ondelete='CASCADE')
