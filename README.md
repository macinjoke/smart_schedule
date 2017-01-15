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
- 各環境で動かす
  - ローカルでサンプルコードなどを動かす場合
    - .env.sampleを参考に.env ファイルに環境変数を書き込む 参照 http://qiita.com/hedgehoCrow/items/2fd56ebea463e7fc0f5b#%E7%92%B0%E5%A2%83%E5%A4%89%E6%95%B0%E3%81%AE%E8%A8%98%E5%85%A5%E6%96%B9%E6%B3%95
  - herokuで動かす場合
    - herokuのダッシュボード上でAPIKEYのための環境変数を設定する 参照 http://dackdive.hateblo.jp/entry/2016/01/26/121900
    - herokuにpushする

ライブラリをインストールするコマンド

```
$ cd smart_schedule
$ pip install -r requirements.txt
```  

# DBをmigrateする手順
以下のコマンドで動作することを確認する  

```
$ heroku run bash
Running bash on ⬢ {app_name}... up, run.2491 (Free)
~ $ python manage.py
```
これが確認できたら、```heroku run bash```した状態で以下のコマンドを実行する  

```
~ $ python manage.py db init
~ $ python manage.py db migrate
~ $ python manage.py db upgrade
```