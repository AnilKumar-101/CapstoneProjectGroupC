import streamlit as st
import subprocess


val1 = st.text_input("Enter your Portfolio Size")
subprocess.run(["python", "project.py"])