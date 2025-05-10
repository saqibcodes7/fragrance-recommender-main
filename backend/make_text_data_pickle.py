import pickle

# Step 1: Tumhari original text data (sample list)
text_data = [
    "Fresh and citrus fragrance for summer.",
    "Warm and woody scent perfect for winter.",
    "Floral perfume with notes of jasmine and rose.",
    "Strong oud-based fragrance with spicy undertones.",
    "Light and clean smell, great for daily wear."
]

# Step 2: Save as pickle
with open("text_data.pkl", "wb") as f:
    pickle.dump(text_data, f)

print("text_data.pkl file saved successfully.")
