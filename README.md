# Music On Hold SIP Server

軽量PythonベースのMusic On Hold専用SIPサーバーです。Grandstream DP750の「Music On Hold URI」での使用を想定しています。

## 特徴

- 軽量なPython実装のSIPサーバー
- MP3ファイルを自動的にPCMU形式に変換
- ffmpegによるRTPストリーミング
- ループ再生対応
- 認証不要のシンプル構成
- Docker化で簡単デプロイ

## 必要なファイル

- `music.mp3` - 再生したい音源ファイル

## 使用方法

### 1. 音源ファイルの準備

プロジェクトディレクトリに `music.mp3` ファイルを配置してください。

```bash
# 例: プロジェクトディレクトリに音源をコピー
cp /path/to/your/music.mp3 ./music.mp3
```

### 2. サーバーの起動

```bash
docker-compose up -d
```

### 3. Grandstream DP750の設定

DP750の管理画面で以下を設定：

- **Music On Hold URI**: `sip:123@[サーバーのIPアドレス]:5060`

例:
```
sip:123@192.168.1.100:5060
```

**注意**:
- 「123」は任意の番号です（例：`sip:999@192.168.1.100:5060`、`sip:moh@192.168.1.100:5060`）
- サーバーはどの番号でも同じようにMusic On Holdを開始します

### 4. 動作確認

```bash
# ログの確認
docker-compose logs -f

# コンテナの状態確認
docker-compose ps
```

## 動作確認とテスト

### Pythonテストスクリプト

サーバーの動作確認用のテストスクリプトが含まれています：

```bash
# SIPサーバーのテスト実行
python3 test_sip_client.py
```

このテストスクリプトは以下を確認します：
- SIP OPTIONS メッセージの応答
- SIP INVITE → 180 Ringing → 200 OK の流れ
- Music On Hold（RTPストリーム）の開始

### SIPクライアントでの動作確認

**推奨SIPクライアント:**
- **Linphone** (無料): https://www.linphone.org/
- **Zoiper** (無料版あり): https://www.zoiper.com/

**設定例:**
```
Username: test (任意)
Password: (空白)
Domain: [サーバーのIPアドレス]
SIP Server: [サーバーのIPアドレス]:5060
Transport: UDP
認証: 無効/なし
```

**発信テスト:**
1. 任意の番号に発信（例：`123`、`999`、`moh`）
2. 即座に接続され、Music On Holdが再生される
3. 音楽がループ再生されることを確認

### ログ確認

```bash
# サーバーログの確認
docker-compose logs -f

# コンテナの状態確認
docker-compose ps
```

## ポート設定

- **SIP**: 5060/udp
- **RTP**: 10000-10100/udp

## トラブルシューティング

### 音声が再生されない場合

1. MP3ファイルが正しく配置されているか確認
2. ファイルの読み取り権限を確認
3. ログでエラーを確認: `docker-compose logs`

### 接続できない場合

1. ポート5060がファイアウォールで開放されているか確認
2. RTPポート範囲(10000-10100)が開放されているか確認
3. DP750からサーバーのIPアドレスに到達可能か確認

## ファイル構成

```
.
├── Dockerfile
├── docker-compose.yml
├── start.sh                     # 起動スクリプト（MP3→WAV変換）
├── sip_server.py               # メインのSIPサーバー実装
├── test_sip_client.py          # 動作確認用テストクライアント
├── test_udp.py                 # UDP接続テスト用
├── music.mp3                   # 音源ファイル（ユーザーが配置）
├── README.md
└── CLAUDE.md
```

## 技術仕様

- **ベースイメージ**: Python 3.9-slim
- **SIPサーバー**: 軽量Python実装
- **RTPストリーミング**: ffmpeg
- **音声コーデック**: PCMU (G.711 μ-law)
- **音声形式**: 8kHz, モノラル, PCM
- **同時接続数**: 制限なし（必要に応じて制限可能）# music_on_hold_dp750
