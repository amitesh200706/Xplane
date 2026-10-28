from Rag.db_setup import get_embedding_model, get_client
from Rag.embbed import chunk_hashmap

def get_called_chunks(retrieved_chunk):

    called_chunks = []

    for callee in retrieved_chunk.get("callee", []):

        chunk = chunk_hashmap.get(callee)

        if chunk:
            called_chunks.append(chunk)

    return called_chunks


def returnable_chunk(code: str):
    model = get_embedding_model()
    client = get_client()
    try:
        query_embedding = model.encode(code)

        results = client.query_points(
            collection_name="vector_DB",
            query=query_embedding,
            limit=1
        ).points

        retrieved_chunks = []

        for point in results:
            retrieved_chunks.append({
                "score": point.score,
                "code": point.payload.get("code", code),
                "metadata": {
                    "name": point.payload.get("name", "N/A"),
                    "type": point.payload.get("metadata", {}).get("type", "N/A"),
                    "file": point.payload.get("metadata", {}).get("src_file", "N/A"),
                    "start_line": point.payload.get("metadata", {}).get("start_line", 1),
                    "end_line": point.payload.get("metadata", {}).get("end_line", 1),
                }
            })
        
        retrieved_chunk = retrieved_chunks[0]

        related_chunks = get_called_chunks(retrieved_chunk)

        return (
            f"The retrieved code chunk is:\n"
            f"{retrieved_chunk['code']}\n\n"

            f"The metadata for the retrieved chunk is:\n"
            f"{retrieved_chunk['metadata']}\n\n"

            f"The related chunks for better context are:\n"
            f"{[chunk['code'] for chunk in related_chunks]}"
        )    
    
    except Exception as e:
        print("Qdrant lookup exception (falling back to direct snippet):", e)
        return f"Code snippet:\n{code}"


if __name__ == "__main__":
    returnable = returnable_chunk("""def get_callee(node):
    if node.type == "call":
        return get_identifier(node)

    for child in node.children:
        result = get_callee(child)
        if result is not None:
            return result

    return None""")
    
    print(returnable)
