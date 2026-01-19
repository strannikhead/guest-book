docker build -t cr.yandex/crpfbols1cpvt8u8s1tt/guestbook:0.1.0 .
docker push cr.yandex/crpfbols1cpvt8u8s1tt/guestbook:0.1.0

yc serverless container create guestbook \
  --image cr.yandex/crpfbols1cpvt8u8s1tt/guestbook:0.1.0 \
  --memory 512M \
  --cores 1 \
  --concurrency 4 \
  --execution-timeout 30s \
  --service-account-id aje4cl4h99bc55kh457k

yc serverless gateway add-backend \
  --gateway-id d5d6rpnsp29i770d0pfk \
  --backend-type container \
  --container-id bba1notpam9il22u19gs \
  --prefix /health \
  --service-account-id aje4cl4h99bc55kh457k