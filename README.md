# smart_schedule
Line bot + Google Calendar で予定を管理

# 概要
TODO
製作途中です

# 環境
- python3.5.2

# 動かし方手順
- python3.5.2 をなんらかの方法でいれる
- リポジトリをクローンする
- 必要なライブラリをインストールする
- smart_schedule/local_setting/api_keys.pyを編集する
  -  `CHANNEL_ACCESS_TOKEN = ""` にLineのチャンネルアクセストークンを入れる 
  -  `CHANNEL_SECRET = ""` にLineのチャンネルシークレットを入れる
- herokuにデプロイする用のブランチを立て、commit, push(デプロイ)する
```
$ cd smart_schedule
$ pip install -r requirements.txt
$ git checkout -b deploy/heroku
$ git commit -am 'add api key'
$ git push heroku deploy/heroku:master
```

## 注意
- APIキーをgithubに公開するわけにはいかないのでデプロイ用のブランチを作る必要がある
- herokuではmasterブランチを本番環境と見なしているのでpushの際には工夫が必要
