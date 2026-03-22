import streamlit as st
import math
import io
from datetime import datetime

# Imports conditionnels avec gestion d'erreur
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
