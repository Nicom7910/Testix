En la terminal del proyecto:

- Para Windows:
  python -m venv venv
  venv\Scripts\activate

- Para Mac:
  python3 -m venv venv
  source venv/bin/activate

Instalar dependencias:
pip install -r requirements.txt

Ejecutar servidor:
uvicorn app.main:app --reload
