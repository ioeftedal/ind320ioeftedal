import streamlit as st

st.title("Ivar Eftedal")
st.markdown(
    """ 
    This is a playground for you to try Streamlit and have fun. 

    **:rainbow[There's so much you can build!]**
    
    We prepared a few examples for you to get started. Just 
    click on the buttons above and discover what you can do 
    with Streamlit. 
    """
)

if st.button("Send balloons!"):
    st.balloons()
