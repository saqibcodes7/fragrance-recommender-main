from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix, save_npz, load_npz
import pickle
import gzip
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import os

print("Starting optimization of cosine similarity matrix...")

# Step 1: Load fragrance data
df_path = 'perfume_data_clean.csv'
df = pd.read_csv(df_path)
print(f"Loaded dataset with {len(df)} fragrances")

# Fill missing values
df['Description'] = df['Description'].fillna('')
df['Main Accords'] = df['Main Accords'].fillna('')

# Step 2: Create or load vectorizer
if os.path.exists("vectorizer.pkl"):
    print("Loading existing vectorizer...")
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
else:
    print("Creating new vectorizer...")
    # Use max_features to limit vocabulary size for better performance
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    vectorizer.fit(df['Description'] + " " + df['Main Accords'])
    # Save vectorizer for future use
    with open("vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    print("Vectorizer saved.")

# Step 3: Transform the text data
print("Transforming text data...")
text_data = df['Description'] + " " + df['Main Accords']
with open("text_data.pkl", "wb") as f:
    pickle.dump(text_data, f)

X = vectorizer.transform(text_data)
print(f"Created TF-IDF matrix of shape {X.shape}")

# Step 4: Calculate cosine similarity (sparse format)
print("Calculating cosine similarity (this may take some time)...")
cosine_sim = cosine_similarity(X, dense_output=False)
print(f"Cosine similarity matrix created with shape {cosine_sim.shape}, density: {cosine_sim.nnz / (cosine_sim.shape[0] * cosine_sim.shape[1]):.4f}")

# Step 5: Apply threshold to make matrix more sparse
# Only keep similarity values above threshold
threshold = 0.1  # Adjust this value as needed
cosine_sim_data = cosine_sim.data
cosine_sim_indices = cosine_sim.indices
cosine_sim_indptr = cosine_sim.indptr

mask = cosine_sim_data > threshold
filtered_data = cosine_sim_data[mask]
filtered_indices = cosine_sim_indices[mask]

# Rebuild the CSR matrix
cosine_sim_sparse = csr_matrix((filtered_data, filtered_indices, cosine_sim_indptr), 
                              shape=cosine_sim.shape)

print(f"Applied threshold: new density: {cosine_sim_sparse.nnz / (cosine_sim_sparse.shape[0] * cosine_sim_sparse.shape[1]):.4f}")

# Step 6: Save compressed similarity matrix
print("Saving compressed matrix...")
with gzip.open("cosine_sim.pkl.gz", "wb", compresslevel=9) as f:
    pickle.dump(cosine_sim_sparse, f)

print("Cosine similarity matrix optimized and saved successfully.")
print(f"Original matrix size: ~{cosine_sim.data.nbytes / 1024 / 1024:.2f} MB")
print(f"Optimized matrix size: ~{cosine_sim_sparse.data.nbytes / 1024 / 1024:.2f} MB")
