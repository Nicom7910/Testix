En la terminal del proyecto:

- Para Windows:

  - python -m venv venv
    Luego este:
  - venv\Scripts\activate

- Para Mac:
  - python3 -m venv venv
    Luego este:
  - source venv/bin/activate

Instalar dependencias:
pip install -r requirements.txt

Ejecutar servidor:
uvicorn app.main:app --reload

En otra terminal correr:
streamlit run frontend/streamlit_app.py
