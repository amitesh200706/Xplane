import os
import shutil

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "vector_DB"
QDRANT_PATH = "./qdrant"

model = SentenceTransformer("all-MiniLM-L6-v2")

def refresh_db():
    # Delete old database
    if os.path.exists(QDRANT_PATH):
        shutil.rmtree(QDRANT_PATH)

    client = QdrantClient(path=QDRANT_PATH)
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=model.get_embedding_dimension(),
            distance=Distance.COSINE
        )
    )

    return client


def get_client():
    return QdrantClient(path=QDRANT_PATH)


def get_embedding_model():
    return model

if __name__ == "__main__":
    client = refresh_db()
    print("Database refreshed and collection created.")
    client.close()