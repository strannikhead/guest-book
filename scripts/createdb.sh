ydb \
  --endpoint grpcs://ydb.serverless.yandexcloud.net:2135 \
  --database /ru-central1/b1gg2nsser01m7uhn0ad/etn44f5cojgs2dkncukn \
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
