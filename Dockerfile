#Usa a imagem oficial do Python como base (versão 3.9, variante slim para ser mais leve)
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências (requirements.txt) para o container
# Isso permite instalar as dependências antes de copiar o restante do código, otimizando o cache do Docker
COPY requirements.txt .

# Instala as dependências do projeto usando o pip, sem cache para reduzir o tamanho da imagem final
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto para o diretório de trabalho no container
COPY . .

# Expõe a porta padrão do Django (8000) para permitir acesso externo
EXPOSE 8000

# Define o comando padrão para iniciar o servidor de desenvolvimento do Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
