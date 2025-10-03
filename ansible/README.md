# Ansible Playbook for Music On Hold SIP Server

Raspberry Pi 3B (Raspberry Pi OS Lite) に Music On Hold SIP サーバーをセットアップするための Ansible Playbook です。

## 前提条件

### ターゲットホスト (Raspberry Pi)
- **OS**: Raspberry Pi OS Lite
- **SSH**: 公開鍵認証設定済み
- **ユーザー**: `pi`
- **sudo**: パスワードなしsudo実行可能

### コントロールノード (実行元マシン)
- **Ansible**: インストール済み（Python venv推奨）
- **SSH設定**: `~/.ssh/config` にホスト設定済み
  ```
  Host pi-moh
      HostName 192.168.x.x
      User pi
      IdentityFile ~/.ssh/id_rsa
  ```
- **プロジェクトファイル**: プロジェクトルートに以下が必要
  - `sip_server.py`
  - `start.sh`
  - `music.mp3`
  - `test_sip_client.py`
  - `test_udp.py`

## ファイル構成

```
ansible/
├── README.md          # このファイル
├── inventory.ini      # インベントリファイル（pi-mohホスト定義）
└── playbook.yml       # メインPlaybook
```

## Playbook の処理内容

このPlaybookは以下の処理を自動実行します：

### 1. システム準備
- パッケージリストの更新
- 必要パッケージのインストール：
  - `python3` - Pythonランタイム
  - `python3-pip` - Pythonパッケージマネージャー
  - `ffmpeg` - 音声変換・RTPストリーミング
  - `sox` - 音声処理ツール

### 2. 専用ユーザー作成
- ユーザー名: `moh`
- システムユーザーとして作成（`--system`）
- ログインシェル: `/usr/sbin/nologin`
- ホームディレクトリなし

### 3. ディレクトリ作成
- `/opt/moh-server/` - アプリケーションディレクトリ
- `/opt/moh-server/sounds/` - 変換後音声ファイル保存用
- オーナー: `moh:moh`
- パーミッション: `755`

### 4. ファイル転送
プロジェクトルートから以下を転送（シンボリックリンクの実体を転送）：
- `sip_server.py` - メインSIPサーバー
- `start.sh` - 起動スクリプト
- `music.mp3` - 音源ファイル
- `test_sip_client.py` - テストクライアント
- `test_udp.py` - UDP接続テスト

### 5. パス修正
`lineinfile` モジュールでDockerパスをローカルパスに書き換え：
- `start.sh`:
  - `/music.mp3` → `/opt/moh-server/music.mp3`
  - `/app/sounds/music.wav` → `/opt/moh-server/sounds/music.wav`
  - `/app/sip_server.py` → `/opt/moh-server/sip_server.py`
- `sip_server.py`:
  - デフォルト音声ファイルパス → `/opt/moh-server/sounds/music.wav`

### 6. WAV変換（overlayfs対応）
- MP3 → WAV変換を事前実行（8kHz, モノラル, PCM）
- overlayfs（読み取り専用化）後は書き込み不可のため、事前変換が必須

### 7. systemd サービス作成
- サービス名: `moh-server.service`
- 実行ユーザー: `moh`
- 自動起動: 有効
- 自動再起動: 有効（RestartSec=10）
- ログ出力: systemd journal

### 8. swap 無効化
overlayfs（読み取り専用ファイルシステム）準備のため：
- `swapoff -a` でswap即座に無効化
- `/etc/dphys-swapfile` で `CONF_SWAPSIZE=0` 設定
- `dphys-swapfile` サービス停止・無効化

### 9. サービス起動
- `moh-server.service` を有効化
- サービスを起動
- 起動状態を確認・表示

## 実行方法

### 1. Ansible環境準備

```bash
# Python仮想環境のアクティベート
source venv/bin/activate

# ロケール設定（文字化け防止）
export LC_ALL=en_US.UTF-8
```

### 2. Playbookの実行

```bash
# ansibleディレクトリに移動
cd ansible

# 構文チェック（オプション）
ansible-playbook --syntax-check playbook.yml

# 実行（ドライラン）
ansible-playbook -i inventory.ini playbook.yml --check

# 本番実行
ansible-playbook -i inventory.ini playbook.yml
```

### 3. 実行結果の確認

```bash
# サービス状態確認
ssh pi-moh "systemctl status moh-server"

# ログ確認
ssh pi-moh "journalctl -u moh-server -f"

# ポート確認
ssh pi-moh "sudo netstat -ulnp | grep 5060"
```

## 動作確認

### Raspberry Pi 上でのテスト

```bash
# Raspberry Piにログイン
ssh pi-moh

# UDP接続テスト（ローカルホスト）
cd /opt/moh-server
python3 test_udp.py

# SIPクライアントテスト（ローカルホスト）
python3 test_sip_client.py
```

### 他のマシンからのテスト

```bash
# UDP接続テスト
python3 test_udp.py <Raspberry PiのIPアドレス>

# 例
python3 test_udp.py 192.168.52.174

# SIPクライアントテスト
python3 test_sip_client.py <Raspberry PiのIPアドレス>

# 例
python3 test_sip_client.py 192.168.52.174
```

## トラブルシューティング

### music.mp3が見つからないエラー

```bash
# プロジェクトルートにmusic.mp3があるか確認
ls -l music.mp3

# シンボリックリンクの場合、実体を確認
ls -lL music.mp3
```

### サービスが起動しない

```bash
# ログ確認
ssh pi-moh "journalctl -u moh-server -n 50"

# start.shを手動実行
ssh pi-moh "sudo -u moh /opt/moh-server/start.sh"

# ファイル権限確認
ssh pi-moh "ls -la /opt/moh-server/"
```

### ポート5060がリッスンしていない

```bash
# プロセス確認
ssh pi-moh "ps aux | grep sip_server"

# ポート確認
ssh pi-moh "sudo netstat -ulnp | grep 5060"

# ファイアウォール確認（もしあれば）
ssh pi-moh "sudo iptables -L -n"
```

### WAV変換が失敗する

```bash
# ffmpegインストール確認
ssh pi-moh "which ffmpeg"

# 手動変換テスト
ssh pi-moh "ffmpeg -i /opt/moh-server/music.mp3 -ar 8000 -ac 1 -c:a pcm_s16le /tmp/test.wav"
```

## overlayfs 設定後の注意事項

Playbookは swap を無効化しますが、overlayfs の設定は手動で行う必要があります。

overlayfs 設定後：
- `/opt/moh-server/` は読み取り専用になります
- `music.wav` は事前変換済みなので問題ありません
- 設定変更が必要な場合は、overlayfs を一時的に解除してください

## サービス管理コマンド

```bash
# サービス起動
sudo systemctl start moh-server

# サービス停止
sudo systemctl stop moh-server

# サービス再起動
sudo systemctl restart moh-server

# サービス状態確認
sudo systemctl status moh-server

# ログ確認（リアルタイム）
sudo journalctl -u moh-server -f

# ログ確認（最新50行）
sudo journalctl -u moh-server -n 50
```

## 再デプロイ

ファイル更新後、再度Playbookを実行：

```bash
cd ansible
source ../venv/bin/activate
export LC_ALL=en_US.UTF-8
ansible-playbook -i inventory.ini playbook.yml
```

Playbookは冪等性があるため、何度実行しても安全です。

## Grandstream DP750 設定

Raspberry Pi上でサーバーが起動したら、DP750の管理画面で設定：

- **Music On Hold URI**: `sip:123@<Raspberry PiのIPアドレス>:5060`

例:
```
sip:123@192.168.1.100:5060
```

**注意**: 「123」は任意の番号です。サーバーはどの番号でも同じようにMusic On Holdを開始します。
