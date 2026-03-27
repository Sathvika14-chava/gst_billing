import streamlit as st

st.title("GST Billing App")

product = st.text_input("Product Name")
price = st.number_input("Price", min_value=0.0)
qty = st.number_input("Quantity", min_value=1)
gst = st.selectbox("GST %", [5, 12, 18, 28])

if st.button("Generate Bill"):
    subtotal = price * qty
    gst_amt = subtotal * gst / 100
    total = subtotal + gst_amt

    st.write("Subtotal:", subtotal)
    st.write("GST:", gst_amt)
    st.write("Total:", total)