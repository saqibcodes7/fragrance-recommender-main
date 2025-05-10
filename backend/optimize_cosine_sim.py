from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import pickle
import gzip

# Step 1: Load trained vectorizer object
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Step 2: Load original text data (list of fragrance descriptions)
with open("text_data.pkl", "rb") as f:
    text_data = pickle.load(f)

# Step 3: Vectorize the text data
X = vectorizer.transform(text_data)

# Step 4: Calculate cosine similarity
cosine_sim = cosine_similarity(X, dense_output=False)

# Step 5: Convert to sparse matrix
cosine_sim_sparse = csr_matrix(cosine_sim)

# Step 6: Save compressed similarity matrix
with gzip.open("cosine_sim.pkl.gz", "wb") as f:
    pickle.dump(cosine_sim_sparse, f)

print("Compressed cosine similarity saved successfully.")
