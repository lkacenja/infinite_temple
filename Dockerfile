FROM ubuntu:latest
RUN apt-get update -y && apt-get install -y curl
RUN curl -fsSL https://ollama.com/install.sh | sh
CMD ["sh", "-c", "sleep 10 && ollama pull deepseek-r1:latest && wait"]
#CMD tail -f /dev/null