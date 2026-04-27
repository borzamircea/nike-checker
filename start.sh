docker build -t nike-bot .

docker rm -f nike-bot

docker run -d \
  --name nike-bot \
  --restart=always \
  nike-bot