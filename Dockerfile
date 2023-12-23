# Utilizar una imagen base oficial de Python
FROM python:3.9

# Establecer el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Copiar los archivos de requisitos y tu script a la carpeta del contenedor
COPY requirements.txt ./
COPY main.py ./

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar tu aplicación
CMD [ "python", "./main.py" ]
