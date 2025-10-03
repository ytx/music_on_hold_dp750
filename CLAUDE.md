# Music On Hold SIP Server - 開発ログ

## プロジェクト概要

Grandstream DP750の「Music On Hold URI」で使用するための専用SIPサーバーを構築。

## 開発経緯

### フェーズ1: Asterisk実装（失敗）
初期はAsteriskベースで実装を試みたが、Stasis initializationエラーにより断念。
- Ubuntu 22.04/20.04/18.04 すべてで同じエラー
- Stasisモジュールが必須だが、無効化が困難

### フェーズ2: Python軽量実装（成功）
Asteriskの複雑さを回避し、軽量なPython実装に変更。

### フェーズ3: Ansible自動デプロイ（完成）
Raspberry Pi OS Lite向けのAnsible Playbookを作成し、自動セットアップを実現。

## 要件定義

### 基本要件
- **プラットフォーム**: Docker または Raspberry Pi OS Lite（ベアメタル）
- **音源形式**: MP3ファイル（起動時にバインド/配置）
- **音声処理**: 起動時に適切な形式に変換
- **再生方式**: ループ再生
- **対象機器**: Grandstream DP750

### 技術仕様（最終）
- **SIPサーバー**: 軽量Python実装
- **Docker環境**: Python 3.9-slim
- **Raspberry Pi環境**: Python 3（OS標準）
- **音声コーデック**: PCMU（G.711 μ-law）
- **RTPストリーミング**: ffmpeg
- **ネットワーク**: SIP 5060、RTP 10000-10100（動的割り当て）
- **認証**: なし（オープン）
- **同時接続数**: 制限なし
- **デプロイ方法**:
  - Docker: docker-compose.yml
  - Raspberry Pi: Ansible Playbook

## 実装内容

### 1. Dockerfile
- Python 3.9-slimベース
- ffmpeg、soxによる音声変換機能
- 軽量コンテナ（Asteriskなし）

### 2. SIPサーバー実装（sip_server.py）
- カスタムSIPプロトコル実装
- UDP ソケット通信
- SIP メッセージ処理：
  - OPTIONS → 200 OK
  - INVITE → 180 Ringing → 200 OK（SDP付き）
  - BYE → 200 OK
- RTPストリーム開始（ffmpeg subprocess）

### 3. 起動スクリプト（start.sh）
- MP3 → WAV変換（8kHz、モノラル、PCM）
- Python SIPサーバー起動

### 4. テストスクリプト
- **test_sip_client.py**: 完全なSIPクライアント実装（IPアドレス指定可能）
- **test_udp.py**: UDP接続確認用（IPアドレス指定可能）

### 5. docker-compose.yml
- ポートマッピング（5060/udp、10000-10100/udp）
- 音源ファイルバインド
- ネットワーク設定

### 6. Ansible Playbook（ansible/）
- **inventory.ini**: ホスト定義
- **playbook.yml**: 自動セットアップPlaybook
  - システムパッケージインストール
  - 専用ユーザー（moh）作成
  - ファイル転送とパス修正
  - WAV事前変換（overlayfs対応）
  - systemdサービス作成
  - swap無効化
- **README.md**: 実行手順とトラブルシューティング

## ファイル構成

```
moh/
├── Dockerfile
├── docker-compose.yml
├── start.sh
├── sip_server.py           # メインSIPサーバー
├── test_sip_client.py      # テストクライアント
├── test_udp.py            # UDP接続テスト
├── music.mp3              # 音源ファイル
├── README.md
├── CLAUDE.md
└── ansible/
    ├── inventory.ini      # Ansibleホスト定義
    ├── playbook.yml       # 自動セットアップPlaybook
    └── README.md          # Ansible実行手順
```

## 使用方法

### Docker環境
1. 音源ファイル配置: `music.mp3`
2. サーバー起動: `docker-compose up -d`
3. DP750設定: Music On Hold URI = `sip:123@[サーバーIP]:5060`

### Raspberry Pi環境
1. 音源ファイル配置: `music.mp3`
2. Ansible実行: `cd ansible && ansible-playbook -i inventory.ini playbook.yml`
3. DP750設定: Music On Hold URI = `sip:123@[サーバーIP]:5060`

詳細は `ansible/README.md` を参照。

## 特徴

- **軽量**: Asteriskなし、Pythonスクリプトのみ
- **シンプル**: 認証不要、設定最小限
- **自動変換**: MP3を起動時にPCM形式に変換
- **ループ再生**: ffmpegによる音源の途切れない再生
- **テスト対応**: 包括的なテストスクリプト付属（IPアドレス指定可能）
- **柔軟なデプロイ**: Docker と Raspberry Pi の両方に対応
- **自動化**: Ansible Playbookによる完全自動セットアップ
- **overlayfs対応**: Raspberry Piの読み取り専用ファイルシステムに対応

## 技術的なポイント

- **SIP実装**: 軽量なカスタム実装（Python socket）
- **音声変換**: ffmpegで8kHz/モノラル/PCMに変換
- **RTPストリーミング**: ffmpeg subprocessでリアルタイム配信
- **動的ポート**: RTPポート10000-10100の範囲で動的割り当て
- **マルチスレッド**: 各SIP接続を独立スレッドで処理

## 開発の成果

✅ **成功**: Music On Hold SIPサーバーが正常動作
- SIP OPTIONS/INVITE/ACK/BYEの基本機能
- RTPストリーミングによる音楽配信
- Grandstream DP750対応
- Docker化で簡単デプロイ
- Ansible Playbookによる自動セットアップ
- Raspberry Pi OS Lite対応

## トラブルシューティング履歴

1. **Asterisk Stasisエラー**: Python実装への変更で解決
2. **macOS Docker networking**: 実際は問題なし、テスト方法の改善で解決
3. **SIP URIフォーマット**: `sip:123@server:5060`形式の確認
4. **ACK処理**: ACKメッセージの適切な処理（応答不要）を追加
5. **Ansible パス修正**: start.shの全パスを正しく置換するよう修正
6. **テストスクリプト**: IPアドレス指定をコマンドライン引数で可能に