FROM alpine:latest

COPY script.sh /script.sh
RUN chmod +x /script.sh

RUN apk add --no-cache dos2unix \
 && dos2unix /script.sh

ENTRYPOINT ["/script.sh"]