from app import db, create_app
from app.models import User, Post, Comment
from werkzeug.security import generate_password_hash
import time
from sqlalchemy import text

# Initialize app and database
app = create_app()
app.app_context().push()  # Push application context

def clear_database():
    """Clear all tables in the database."""
    db.session.query(Comment).delete()
    db.session.query(Post).delete()
    db.session.query(User).delete()
    db.session.commit()
    db.session.execute(text("ALTER TABLE comment AUTO_INCREMENT = 1;"))
    db.session.execute(text("ALTER TABLE post AUTO_INCREMENT = 1;"))
    db.session.execute(text("ALTER TABLE user AUTO_INCREMENT = 1;"))
    db.session.commit()
    print("Database cleared successfully!")

def seed_database():
    # Seed Users
    igorHub = User(
        email="igorhub2025@gmail.com",
        username="igorhub",
        password=generate_password_hash("12345678", method='pbkdf2:sha256', salt_length=16),
        is_superadmin=True,
    )

    db.session.add_all([igorHub])
    db.session.commit()

    # Seed Posts
    firstPost = Post(
        thumbnail="https://smoothcomp.com/pictures/t/3661472-96fy/igor-piskorskiy-cover.jpg",
        title="First Post",
        description="This is the description for the first post.",
        likes=0
    )
    db.session.add_all([firstPost])
    db.session.commit() 
    # Seed Comments
    comment = Comment(
        user_id=1,
        post_id=1,
        text="Great post!",
        likes=0
    )


    db.session.add_all([comment])
    db.session.commit()
    print("Database seeded successfully!")

if __name__ == "__main__":
    clear_database()
    seed_database()
