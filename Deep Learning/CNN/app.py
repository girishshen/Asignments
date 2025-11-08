import streamlit as st
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

st.title("🩺 Chest X-Ray Classifier – Normal vs Pneumonia")

uploaded = st.file_uploader("Upload Chest X-ray Image", type=["jpg","jpeg","png"])

if uploaded is not None:
    img = image.load_img(uploaded, target_size=(150,150))
    st.image(img, caption="Uploaded Image", use_column_width=True)

    img_array = image.img_to_array(img)/255.0
    img_array = np.expand_dims(img_array, axis=0)

    model = tf.keras.models.load_model("chest_xray_cnn_model.h5")
    pred = model.predict(img_array)[0][0]

    if pred > 0.5:
        st.error("Prediction: Pneumonia Detected 😷")
    else:
        st.success("Prediction: Normal Chest X-Ray ✅")