import os

# Получаем порт как строку (иначе будет ошибка в f-строке)
port = os.environ.get("PORT", "10000")

# Запускаем Streamlit на нужном адресе и порту
os.system(f"streamlit run main.py --server.port={port} --server.address=0.0.0.0")
