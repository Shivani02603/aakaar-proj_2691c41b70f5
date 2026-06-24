import uuid
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    SessionLocal,
    User,
    Session,
    Document,
    DocumentChunk,
    Query
)

def seed_database():
    session = SessionLocal()
    try:
        # Seed Users
        user1 = User(
            id=str(uuid.uuid4()),
            username="john_doe",
            email="john.doe@example.com",
            hashed_password="hashed_password_1"
        )
        user2 = User(
            id=str(uuid.uuid4()),
            username="jane_smith",
            email="jane.smith@example.com",
            hashed_password="hashed_password_2"
        )
        user3 = User(
            id=str(uuid.uuid4()),
            username="alice_jones",
            email="alice.jones@example.com",
            hashed_password="hashed_password_3"
        )
        session.add_all([user1, user2, user3])
        session.commit()

        # Seed Sessions
        session1 = Session(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            last_active="2023-10-01 12:00:00"
        )
        session2 = Session(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            last_active="2023-10-02 14:30:00"
        )
        session3 = Session(
            id=str(uuid.uuid4()),
            user_id=user3.id,
            last_active="2023-10-03 16:45:00"
        )
        session.add_all([session1, session2, session3])
        session.commit()

        # Seed Documents
        document1 = Document(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            session_id=session1.id,
            filename="document1.txt",
            file_type="text/plain",
            file_path="/uploads/document1.txt",
            status="processed",
            processed_at="2023-10-01 13:00:00"
        )
        document2 = Document(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            session_id=session2.id,
            filename="document2.pdf",
            file_type="application/pdf",
            file_path="/uploads/document2.pdf",
            status="error",
            error_message="File format not supported"
        )
        document3 = Document(
            id=str(uuid.uuid4()),
            user_id=user3.id,
            session_id=session3.id,
            filename="document3.docx",
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_path="/uploads/document3.docx",
            status="uploaded"
        )
        session.add_all([document1, document2, document3])
        session.commit()

        # Seed DocumentChunks
        chunk1 = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document1.id,
            user_id=user1.id,
            session_id=session1.id,
            chunk_index=0,
            chunk_text="This is the first chunk of document1.",
            embedding=[0.1] * 1536,
            metadata={"page": 1}
        )
        chunk2 = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document1.id,
            user_id=user1.id,
            session_id=session1.id,
            chunk_index=1,
            chunk_text="This is the second chunk of document1.",
            embedding=[0.2] * 1536,
            metadata={"page": 2}
        )
        chunk3 = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document3.id,
            user_id=user3.id,
            session_id=session3.id,
            chunk_index=0,
            chunk_text="This is the first chunk of document3.",
            embedding=[0.3] * 1536,
            metadata={"page": 1}
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.commit()

        # Seed Queries
        query1 = Query(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            session_id=session1.id,
            question="What is the content of document1?",
            answer="Document1 contains text about AI.",
            sources=[{"document_id": document1.id, "chunk_index": 0}]
        )
        query2 = Query(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            session_id=session2.id,
            question="Why did document2 fail?",
            answer="Document2 failed due to unsupported format.",
            sources=[{"document_id": document2.id}]
        )
        query3 = Query(
            id=str(uuid.uuid4()),
            user_id=user3.id,
            session_id=session3.id,
            question="What is the first chunk of document3?",
            answer="The first chunk of document3 contains introductory text.",
            sources=[{"document_id": document3.id, "chunk_index": 0}]
        )
        session.add_all([query1, query2, query3])
        session.commit()

        print("Database seeded successfully!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()