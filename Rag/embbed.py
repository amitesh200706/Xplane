import __main__
import uuid
from qdrant_client.models import PointStruct

from Parser.Lexer import lexer
from Rag.db_setup import get_embedding_model, get_client

model = get_embedding_model()
chunk_hashmap = {}  

def process_file(file_path, client):
    src_metadata, entities = lexer(file_path)
    entity_embeddings = [model.encode(f"{entity.code}\n{entity.identifier}") for entity in entities]
    points = []

    for entity, embedding in zip(entities, entity_embeddings):

        points.append(
            PointStruct(
                id=str(
                    uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        str(entity.id)
                    )
                ),

                vector=embedding,

                payload={
                    "chunk_id": entity.id,
                    "name": entity.name,
                    "code": entity.code,
                    "metadata": {
                        "type": entity.type,
                        "parent": entity.parent,
                        "identifier": entity.identifier,
                        "callee": entity.callee,
                        "start_line": entity.start_line,
                        "end_line": entity.end_line,
                        "depth": entity.depth,
                        "src_file": src_metadata.file_path,
                        "src_file_name": src_metadata.file_name,}
                }
            )
        )
    
    for point in points:
        chunk_hashmap[point.payload["metadata"]["identifier"]] = point

    if points:
        client.upsert(
            collection_name="vector_DB",
            points=points
        )
    return len(points)

if __name__ == "__main__":
    client = get_client()
    file_path = "D:/untitled/Parser/Visitor.py"  # Replace with the actual file path
    num_chunks = process_file(file_path, client)
    print(f"Processed {num_chunks} chunks from {file_path}.")
    client.close()