ydb \
  --endpoint grpcs://ydb.serverless.yandexcloud.net:2135 \
  --database /ru-central1/b1gg2nsser01m7uhn0ad/etngmqco9mbhtqtb0j31 \
  table query execute \
  -q '
CREATE TABLE messages (
  id Uint64,
  author Utf8,
  text Utf8,
  created_at Timestamp,
  PRIMARY KEY (id)
);
'
