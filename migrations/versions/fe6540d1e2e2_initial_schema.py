"""initial_schema

Revision ID: fe6540d1e2e2
Revises: 
Create Date: 2026-11-02 17:04:26.425957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe6540d1e2e2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'departments' not in tables:
        op.create_table(
            'departments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('full_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=150), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
            sa.PrimaryKeyConstraint('id')
        )
    if 'complaints' not in tables:
        op.create_table(
            'complaints',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('complaint_id', sa.String(length=30), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=30), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('assigned_to', sa.Integer(), nullable=True),
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('resolution_note', sa.Text(), nullable=True),
            sa.Column('attachment', sa.String(length=255), nullable=True),
            sa.Column('video_attachment', sa.String(length=255), nullable=True),
            sa.Column('subcategory', sa.String(length=100), nullable=True),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('area', sa.String(length=150), nullable=True),
            sa.Column('street_name', sa.String(length=200), nullable=True),
            sa.Column('landmark', sa.String(length=200), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('contact_phone', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
    if 'feedback' not in tables:
        op.create_table(
            'feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('complaint_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('complaint_id')
        )
    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('complaint_id', sa.Integer(), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
    if 'status_timeline' not in tables:
        op.create_table(
            'status_timeline',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('complaint_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('changed_by', sa.Integer(), nullable=True),
            sa.Column('changed_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['changed_by'], ['users.id']),
            sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id']),
            sa.PrimaryKeyConstraint('id')
        )

    inspector = sa.inspect(bind)
    user_indexes = {index['name'] for index in inspector.get_indexes('users')}
    if 'ix_users_email' not in user_indexes:
        op.create_index('ix_users_email', 'users', ['email'], unique=True)

    complaint_indexes = {
        index['name'] for index in inspector.get_indexes('complaints')
    }
    complaint_index_columns = {
        'ix_complaints_area': ['area'],
        'ix_complaints_city': ['city'],
        'ix_complaints_complaint_id': ['complaint_id'],
    }
    for index_name, columns in complaint_index_columns.items():
        if index_name not in complaint_indexes:
            op.create_index(
                index_name,
                'complaints',
                columns,
                unique=(index_name == 'ix_complaints_complaint_id')
            )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('status_timeline')
    op.drop_table('notifications')
    op.drop_table('feedback')
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_complaints_complaint_id'))
        batch_op.drop_index(batch_op.f('ix_complaints_city'))
        batch_op.drop_index(batch_op.f('ix_complaints_area'))

    op.drop_table('complaints')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    op.drop_table('departments')
    # ### end Alembic commands ###
