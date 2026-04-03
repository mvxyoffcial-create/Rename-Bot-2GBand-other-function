FROM python:3.10
WORKDIR /app
COPY . /app/

# Install ffmpeg static binary — works even without apt access
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar xf ffmpeg-release-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ffprobe \
    && rm -rf ffmpeg-*-amd64-static* \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

RUN pip3 install -r requirements.txt
CMD ["python3", "bot.py"]
