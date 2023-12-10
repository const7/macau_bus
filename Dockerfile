FROM python:3.10-slim

# set timezone
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# set workdir
WORKDIR /app

# run scripts
CMD exec /bin/sh -c "python /app/bus_data.py & streamlit run /app/app.py & wait"
