from chromadb import PersistentClient

client = PersistentClient(path="./vectordb")
collection = client.get_or_create_collection(name="my_collection")