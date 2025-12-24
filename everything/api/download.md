# Everything HTTP Server のバイナリダウンロードAPI（技術文書 + OpenAPI YAML）

## 1. スコープ

本書は **Everything（Voidtools）HTTP Server** を「ファイル実体（バイナリ）」取得の用途で利用するための技術文書です。

この文書だけで、次が実装できる状態をゴールとします：

* **検索結果等で得た Windows 絶対パスからダウンロードURLを構成し、認証付き GET / Range でバイナリ取得できる**

対象/非対象/前提：

* 対象: **HTTP Server のファイルダウンロード機能**
* 非対象: 検索API（`?search=...&json=1` など）そのものの仕様（ただし「ダウンロードURLを作るために検索結果からパスを得る」前提は最小限触れます）
* 前提: `Allow file download`（ファイルダウンロード許可）が有効になっている

表記上の注意：

* 本書では「バックスラッシュ」を `⧵`（U+29F5）で表記します（例: `C:⧵Users⧵name`）。

## 2. 前提条件と注意（セキュリティ）

公式ドキュメントでは、HTTP Server を有効にすると **Everything がインデックスしたファイル・フォルダが検索でき、さらにダウンロードも可能**になると明記されています。

* 公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/) （Security セクション）

本APIを外部公開する場合は、少なくとも次を検討してください。

* `http_server_bindings` をローカル（例: `127.0.0.1`）に固定する
* 認証（ユーザー名・パスワード）を必ず設定する
* ネットワーク境界（FW/ACL/VPN）でアクセス制限する
* HTTP（平文）である点に注意（必要ならトンネル/リバプロでTLS化）

## 3. HTTP Server とダウンロード許可の有効化

### 3.0 既定のアドレス（公式）と、本書で用いるアドレス（著者環境）

公式ドキュメントでは、Everything の HTTP Server は **既定で `127.0.0.1:80`**（ローカルホストの 80 番）を使用します。
ただし 80 番ポートは既に他サービスで使用されている可能性があるため、本書の著者は **`http://127.160.164.78:8000`** を使用しています。

重要:

* `http://127.160.164.78:8000` は一般的な既定値ではなく、**このドキュメントの作者がそう設定している**だけです。
* 本書に含まれる OpenAPI YAML は、コード生成エージェントがこの著者環境を前提として動作できるように、**`http://127.160.164.78:8000` を `servers` の先頭に明示**しています。
* あなたの環境で別のアドレス/ポートを使う場合は、Everything 側の設定（`http_server_bindings`, `http_server_port`）を変更し、OpenAPI YAML の `servers` も必要に応じて編集してください。

公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/)

### 3.1 GUI から

* Everything → Tools → Options → **HTTP Server**
* **Enable HTTP server** を有効化
* **Allow file download** を有効化（重要）

公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/)

### 3.2 Everything.ini から（自動化・IaC向け）

#### INI の場所

公式 INI ドキュメントより：

* 既定では `Everything.ini` は **`%APPDATA%⧵Everything`** にある
* `Store settings and data in %APPDATA%⧵Everything` を無効にすると、**`Everything.exe` と同じ場所**にある
* Everything 上で `about:config` を検索すると `Everything.ini` を開ける

公式: [https://www.voidtools.com/support/everything/ini/](https://www.voidtools.com/support/everything/ini/) （Editing the Everything.ini / General Settings）

#### 反映タイミング（運用上の注意）

* INI を直接編集する場合は、**Everything を終了**してから編集し、再起動で反映する運用が安全です。
* HTTP Server の設定変更は、GUI 手順として **HTTP Server の再起動（Enable をOFF→Apply→ON）**が案内されています。

公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/) （Restart the HTTP Server）

#### HTTP Server 主要オプション（抜粋）

* `http_server_enabled` : 1 で有効
* `http_server_bindings` : 空文字で全IFにバインド（推奨しない）。ローカル限定なら `127.0.0.1` など
* `http_server_port` : ポート
* `http_server_username` / `http_server_password` : 認証用
* `http_server_allow_file_download` : 1 でダウンロード許可

公式: [https://www.voidtools.com/support/everything/ini/](https://www.voidtools.com/support/everything/ini/) （HTTP セクション）

例（概念例）：

```ini
; Everything.ini
http_server_enabled=1
http_server_bindings=127.0.0.1
http_server_port=8000
http_server_username=api
http_server_password=REDACTED
http_server_allow_file_download=1
```

## 4. ダウンロードURLの形式（最短レシピ → 詳細）

Everything HTTP Server は、検索結果一覧（HTML/JSON）で得られる Windows のファイルパスを URL パスとして表現し、**そのURLに GET** することでファイル実体を返します。

### 4.0 最短レシピ（実装の最小手順）

1. **Windows 絶対パス**を得る（例: `C:⧵Program Files⧵…⧵file.ext`）

* HTML のリンク（`href="/C%3A/..."`）をそのまま使うのが最も確実
* JSON 検索を使う場合は、`json=1` と併せて `path_column=1` を有効化し、結果からパス情報を得る（検索APIの詳細は本書の範囲外）

2. パスを **セグメントに分割**し、各セグメントを **`encodeURIComponent` 相当でパーセントエンコード**する

* 例: `C:` → `C%3A`、`Program Files` → `Program%20Files`、`x#y.txt` → `x%23y.txt`

3. `/{drive}/{seg1}/{seg2}/.../{file}` の形にして **GET**（必要なら Basic 認証、必要なら `Range`）

### 4.1 URLパスへの変換ルール（観測に基づく）

ユーザー環境で観測された HTML の `href`（抜粋）：

* Windows: `C:⧵Program Files⧵nodejs⧵…⧵npm-install-ci-test.md`
* URL: `/C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md`

この観測から確実に言える規則：

1. Windows の区切り（バックスラッシュ）は URL では `/` に置換
2. ドライブレターの `:` はパーセントエンコード（例: `C:` → `C%3A`）
3. スペースは `%20` にエンコード（例: `Program Files` → `Program%20Files`）
4. URL の先頭には `/` が付く（例: `/C%3A/...`）

### 4.2 エンコード実装（推奨）

推奨は「Windows パスを分割して、**各セグメントをエンコードしてから** `/` で連結」する方式です。

* ドライブ部: `encodeURIComponent("C:")` → `C%3A`
* 以降のフォルダ名/ファイル名: それぞれ `encodeURIComponent` して `/` 連結

疑似コード：

```text
input:  C:⧵Program Files⧵A B⧵x#y.txt
split:  ["C:", "Program Files", "A B", "x#y.txt"]
encode: ["C%3A", "Program%20Files", "A%20B", "x%23y.txt"]
join:   "/" + join("/", encode)
output: /C%3A/Program%20Files/A%20B/x%23y.txt
```

実装上の注意：

* `encodeURI` は `:` をエンコードしないため **不適**（`C:` が壊れる）
* **二重エンコード禁止**（`%` をさらに `%25` にしない）
* `#` や `?` は URL の意味を持つので、**セグメント内に現れる場合は必ず `%23`, `%3F` にエンコード**する

OpenAPI との関係（重要）：

* 実リクエストは `/{drive}/{seg1}/{seg2}/.../{file}` のように **複数セグメント**です。
* OpenAPI の path parameter では `/` 跨ぎの表現が弱いため、**クライアント実装は「テンプレート置換」よりも “URL を自前で組み立てる” 方が確実**です（7章参照）。

### 4.3 仕様として未確定/要検証の点

運用上、次は Everything のバージョンや実装、対象ファイルの状態（ロック/権限など）で変動し得ます。

* UNC パス（例: `⧵⧵server⧵share⧵...`）の URL 表現
* 特定ファイルでの `404`（存在していても OS から読み取り不可/ロック等で失敗するケース）
* `Content-Type` 推定の詳細（拡張子で変わるか、既定が何か）
* `Content-Disposition` が付与されるか（付与されない場合、ブラウザは拡張子により表示/保存を選ぶ）

これらは対象環境でレスポンスヘッダを観測して確定させてください。

## 5. リクエストとレスポンス（実装上の要点）

### 5.1 メソッド

* **GET** のみでファイル実体取得が成立（UI のリンクも GET）

### 5.2 認証

* HTTP Server は username/password を設定可能
* プラグイン実装では `401` 時に `WWW-Authenticate: Basic realm="Everything"` を返すため、クライアントは **HTTP Basic 認証**を実装すればよい

公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/) （Set a username and password）

### 5.3 Range（部分取得）

公式に **Range request をサポート**すると記載があります。

* 公式: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/) （Range request）

従ってクライアントは以下を実装できます。

* `Range: bytes=0-1023`（先頭1KBだけ取得）
* 大きなファイルのレジューム/ストリーミング

### 5.4 代表的ステータスコード（注意付き）

* `200 OK` : 全体取得
* `206 Partial Content` : Range による部分取得
* `401 Unauthorized` : 認証要求（ユーザー名/パスワード設定時）
* `403 Forbidden` / `404 Not Found` : ダウンロード禁止・アクセス不可・解決不能パスなど（環境/実装差・対象ファイル状態により揺れる可能性がある）
* `416 Range Not Satisfiable` : Range 指定が不正

実装では「ステータスだけで断定」せず、必要ならレスポンス本文（HTMLエラー）やログも併用して診断してください。

## 6. 利用例（curl / Node / Python）

以下の例ではホストを `127.160.164.78:8000` とします（著者環境）。

補足:

* 公式の既定値は `127.0.0.1:80` です。
* 本書の例・OpenAPI YAML は「著者が 80 番の競合回避のために 8000 を選んだ」ことを前提にしています。

### 6.1 ファイル全体のダウンロード（curl）

```bash
curl -L \
  -u "api:REDACTED" \
  -o npm-install-ci-test.md \
  "http://127.160.164.78:8000/C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md"
```

### 6.2 Range で先頭だけ取得（curl）

```bash
curl -L \
  -u "api:REDACTED" \
  -H "Range: bytes=0-1023" \
  -o head.bin \
  "http://127.160.164.78:8000/C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md"
```

### 6.3 Node.js（fetch）

```js
const url = "http://127.160.164.78:8000/C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md";

const res = await fetch(url, {
  headers: {
    "Authorization": "Basic " + Buffer.from("api:REDACTED").toString("base64"),
    // "Range": "bytes=0-1023",
  }
});

if (!res.ok && res.status !== 206) throw new Error(`HTTP ${res.status}`);
const buf = Buffer.from(await res.arrayBuffer());
// buf を保存
```

### 6.4 Python（requests）

```python
import requests

url = "http://127.160.164.78:8000/C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md"

r = requests.get(url, auth=("api", "REDACTED"), stream=True)
r.raise_for_status()

with open("npm-install-ci-test.md", "wb") as f:
    for chunk in r.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)
```

## 7. OpenAPI 仕様（ダウンロード専用・YAML）

OpenAPI は「パスパラメータが `/` を跨いで貪欲にマッチする」ことを標準では表現しにくいため、**実務上は2つの表現を併記**します。

* **(A) 実URL表現（推奨・実態に忠実）**: `/{drive}/{path}`（ただし `path` は複数セグメントの連結として解釈）
* **(B) ツール互換表現（補助）**: `/{encodedPath}`（OpenAPIツールの都合で単一パラメータに見せるための“記法”）

  * 注意: サーバが `"%2F"` を `/` として復号・解釈するかは実装次第です。
  * 互換性が問題になる場合は、**クライアント側で URL を組み立てて送る**運用を基本にしてください。

```yaml
openapi: 3.1.0
info:
  title: Everything HTTP Server Binary Download API
  version: 0.2.0
  description: |
    Everything (Voidtools) HTTP Server の「ファイル実体（バイナリ）」取得エンドポイント。

    スコープ:
      - ファイルダウンロードのみ（検索 API は含めない）

    前提:
      - Everything 側で HTTP Server が有効
      - Allow file download / http_server_allow_file_download=1 が有効

    重要:
      - URL パスは Windows のフルパスを URL パスに投影した形式。
      - drive は例: "C%3A" のように ":" を %3A にする。
      - 以降の各セグメントも RFC3986 に従ってパーセントエンコード（例: 空白は %20）。

servers:
  - url: http://127.160.164.78:8000
    description: 著者の検証環境（一般的ではない）。OpenAPI 参照・コード生成時にこのアドレスが使われることを意図して先頭に記載。
  - url: http://{host}:{port}
    description: Everything HTTP Server（一般形）
    variables:
      host:
        default: 127.0.0.1
        description: 既定はローカルホスト（公式ドキュメント参照）
      port:
        default: "80"
        description: 既定ポート（公式ドキュメント参照）

tags:
  - name: download
    description: ファイル実体（バイナリ）の取得

paths:
  # (A) 実URLに忠実な表現。
  # OpenAPI では / を跨ぐ path parameter を表現しにくいため、path は「以降の全セグメントを / で連結したもの」として扱う。
  "/{drive}/{path}":
    get:
      tags: [download]
      summary: Download file content by encoded Windows absolute path
      description: |
        Everything HTTP Server のファイル実体取得（実URL表現）。

        例:
          - Windows: C:⧵Program Files⧵nodejs⧵…⧵npm-install-ci-test.md
          - URL:     /C%3A/Program%20Files/nodejs/.../npm-install-ci-test.md

        エンコード指針:
          - drive: "C:" を encodeURIComponent 相当でエンコードし "C%3A" とする。
          - 以降のフォルダ名/ファイル名もセグメント単位で encodeURIComponent。
          - 区切りは URL パス区切りとして `/` を使う。

      parameters:
        - name: drive
          in: path
          required: true
          description: ドライブセグメント（例: C: → C%3A）
          schema:
            type: string
          examples:
            C_drive:
              value: C%3A

        - name: path
          in: path
          required: true
          allowReserved: true
          description: |
            drive 以降のパス。

            OpenAPI 表現上は 1 つのパラメータだが、実際の URL は
            `/{drive}/{seg1}/{seg2}/.../{file}` のように複数セグメント。

            各セグメントをパーセントエンコードした上で `/` 連結する。
          schema:
            type: string
          examples:
            npm_doc:
              value: Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md

        - name: Range
          in: header
          required: false
          description: 取得範囲（バイト）。例: bytes=0-1023
          schema:
            type: string
          examples:
            first_1kb:
              value: bytes=0-1023

      security:
        - basicAuth: []

      responses:
        "200":
          description: Full content
          headers:
            Content-Length:
              description: ファイルサイズ（バイト）
              schema:
                type: integer
                format: int64
            Accept-Ranges:
              description: bytes が返ることがある（Range 対応）
              schema:
                type: string
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary

        "206":
          description: Partial content (Range)
          headers:
            Content-Range:
              description: 返却範囲
              schema:
                type: string
            Content-Length:
              description: 返却サイズ（バイト）
              schema:
                type: integer
                format: int64
            Accept-Ranges:
              schema:
                type: string
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary

        "401":
          description: Unauthorized (authentication required)
          content:
            text/html:
              schema:
                type: string

        "403":
          description: Forbidden (file download disabled or access denied)
          content:
            text/html:
              schema:
                type: string

        "404":
          description: Not Found (path not resolvable / file unavailable)
          content:
            text/html:
              schema:
                type: string

        "416":
          description: Range Not Satisfiable
          content:
            text/html:
              schema:
                type: string

  # (B) ツール互換の補助表現。
  # OpenAPIクライアント生成が `/{drive}/{path}` を扱いにくい場合の“記法”。
  # 実際のHTTPリクエストは最終的に (A) の形式（パス区切りは /）へ展開して送ること。
  "/{encodedPath}":
    get:
      tags: [download]
      summary: (Tooling helper) Download by fully encoded path template
      description: |
        OpenAPI の都合で「全パスを 1 パラメータに見せる」ための補助表現。

        encodedPath には、以下のいずれかを入れる:
          - 既に `/{drive}/{seg1}/.../{file}` 形式で組み立てたもの（先頭の / を除く）
          - またはツールが許すなら、`/` を `%2F` にした文字列（ただしサーバ側の復号挙動は要検証）

        推奨運用:
          - encodedPath を受け取ったらクライアントで “実URL（A）” を組み立てて送信する。
      parameters:
        - name: encodedPath
          in: path
          required: true
          description: |
            先頭 `/` を除いた、エンコード済みのパス表現。
            例: C%3A/Program%20Files/.../file.ext
          schema:
            type: string
          examples:
            full_path:
              value: C%3A/Program%20Files/nodejs/node_modules/npm/docs/content/commands/npm-install-ci-test.md
        - name: Range
          in: header
          required: false
          schema:
            type: string
      security:
        - basicAuth: []
      responses:
        "200":
          description: Full content
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        "206":
          description: Partial content (Range)
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        "401":
          description: Unauthorized
          content:
            text/html:
              schema:
                type: string
        "403":
          description: Forbidden
          content:
            text/html:
              schema:
                type: string
        "404":
          description: Not Found
          content:
            text/html:
              schema:
                type: string
        "416":
          description: Range Not Satisfiable
          content:
            text/html:
              schema:
                type: string

components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
      description: |
        Everything の HTTP Server は username/password を設定可能。
        401 応答の WWW-Authenticate は Basic realm を示す。
```

## 8. 参照（一次情報）

* Everything HTTP Server 公式ドキュメント: [https://www.voidtools.com/support/everything/http/](https://www.voidtools.com/support/everything/http/)
* Everything.ini 公式ドキュメント（HTTP設定/INI位置）: [https://www.voidtools.com/support/everything/ini/](https://www.voidtools.com/support/everything/ini/)
* HTTP Server plugin (GitHub): [https://github.com/voidtools/http_server](https://github.com/voidtools/http_server)
