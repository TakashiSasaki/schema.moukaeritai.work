# Everything HTTP Server（Everything 1.5）JSON検索API（`json=1`）

## 目的

Everything（voidtools）の HTTP Server（Everything 1.5 プラグイン）を **API用途**で利用するために、**検索API（JSON出力のみ）**を仕様化し、OpenAPI 3.1（YAML）として提示する。

* 対象: **検索**のみ
* 非対象: ファイルの閲覧・ダウンロードAPI（本書では扱わない）

根拠は、voidtools の公式ドキュメント、および voidtools が公開する HTTP Server プラグインの README（公式リポジトリ）とする。

---

## HTTPサーバの既定値とポート変更

Everything の HTTP Server は既定で **127.0.0.1:80**（`http://127.0.0.1/` または `http://localhost/`）で待ち受ける。ポート 80 は OS 側で既に使用中のことがあるため、公式ドキュメントでも **別ポート（例: 8080）** への変更が案内されている。

* 既定例: `http://127.0.0.1/`（ポート 80）
* 変更例: `http://127.0.0.1:8080/`

### 本書の作成者環境

本書の作成者は、80 番ポートの競合を避けるため、Everything HTTP Server の設定を **`http://127.160.164.78:8000`** に変更して使用している。

重要:

* `http://127.160.164.78:8000` は一般的な既定値ではなく、**この文書の作成者が選択した設定**に過ぎない。
* あなたの環境では、Everything 側の HTTP Server 設定（バインド先/ポート）に合わせて URL を読み替えること。

---

## エンドポイント概要

### 検索（JSON）

* HTTP メソッド: **GET**
* パス: `/`
* クエリ: `key=value` 形式（不要なペアは省略可能）

公式 README に記載されている構文（例）:

`http://localhost/?s=&o=0&c=32&j=0&i=0&w=0&p=0&r=0&m=0&path_column=0&size_column=0&date_modified_column=0&sort=name&ascending=1`

本書は **`json=1` 固定**で扱う。

---

## `search`（検索文字列）の言語仕様（Everything 検索構文）

`search` は Everything の通常の検索入力と同じ構文を受け付ける。

最低限知っておくべき点:

* **空白は AND**（`ABC 123` は `ABC` AND `123`）
* `|` は OR
* `!` は NOT
* `"..."` でフレーズ検索
* `*` / `?` のワイルドカード
* `path:` / `regex:` / `case:` などの修飾子・関数（Everything の検索構文に従う）

### URLクエリとして送るときのエンコード（重要）

Everything の検索構文そのものとは別に、HTTP のクエリ文字列として送る都合上、**予約文字を URL エンコード**する必要がある。

* `&` はクエリの区切り文字なので、検索語として含めたい場合は `%26` にする。
* `+` は多くの実装で「スペース」として解釈されるため、検索語として `+` を含めたい場合は `%2B` にする。
* `"`（ダブルクォート）, `:`（コロン）, `\`（バックスラッシュ）, 空白なども状況によりエンコードが必要。

例:

* ファイル名そのまま: `test.md`

  * `?search=test.md&json=1`
* AND（空白）: `ABC 123`

  * `?search=ABC+123&json=1`（空白を `+` として送る例）
* Windows パスをフレーズとして検索: `"C:\Program Files\nodejs"`

  * `?search=%22C%3A%5CProgram%20Files%5Cnodejs%22&json=1`
* `C++` のように `+` を含む語を検索

  * `?search=C%2B%2B&json=1`
* `A&B.txt` のように `&` を含む語を検索

  * `?search=A%26B.txt&json=1`

---

## クエリパラメータ（JSONモード）

HTTP Server は **短縮名/別名**（例: `search` の別名として `s` や `q`）も受け付ける。ただし API の長期運用とコード生成の安定性のため、**本書は正規名（長いキー）を推奨**し、OpenAPI でも正規名を主として記述する。

互換性のために OpenAPI 側にも短縮名/別名を **`deprecated: true`** で併記する。

注意:

* 同じ意味のキー（例: `search` と `s`）を **同一リクエストで併用しない**こと。実装の解釈順に依存し、意図しない結果になる可能性がある。

### 基本

* `search`（別名: `s`, `q`）: 検索文字列
* `offset`（別名: `o`）: 先頭から何件目（0-based）から返すか
* `count`（別名: `c`）: 返す最大件数
* `json`（別名: `j`）: **JSONで返すか**（本書は `1` 固定）

### 検索オプション（0/1）

* `case`（別名: `i`）: 大文字小文字を区別
* `wholeword`（別名: `w`）: 単語単位でマッチ
* `path`（別名: `p`）: フルパスも検索対象
* `regex`（別名: `r`）: 正規表現検索
* `diacritics`（別名: `m`）: ダイアクリティカルマーク（アクセント）を区別

### JSONに含める列（0/1）

JSONレスポンス内に「追加フィールド」を含めるかを指定する。

* `path_column`: `path` を含める
* `size_column`: `size` を含める
* `date_modified_column`: `date_modified` を含める

公式 README では JSONモードの既定値として、`count=4294967295`（実質無制限）かつ各 *_column は 0 が示されている。
API用途では **`count` を必ず指定**し、必要な列だけ *_column を 1 にする運用を推奨する。

### ソート

* `sort`: `name` / `path` / `date_modified` / `size`
* `ascending`: 1 で昇順、0 で降順

---

## レスポンス（JSON）

### 実測（作成者環境）

作成者環境では、Everything を Windows 上で実行し、HTTP Server を `http://127.160.164.78:8000` に設定して利用している。

次のリクエストを実行したところ:

`http://127.160.164.78:8000/?search=test.md&json=1&date_modified_column=1&date_created_column=1&size_column=1&path_column=1`

以下の JSON を得た（`results` は 10 件だったが、ここでは 2 件だけ掲載）:

```json
{
  "totalResults": 10,
  "results": [
    {
      "type": "file",
      "name": "npm-install-ci-test.md",
      "path": "C:\Program Files\nodejs\node_modules\npm\docs\content\commands",
      "size": "7699",
      "date_modified": "133754350660000000"
    },
    {
      "type": "file",
      "name": "npm-install-ci-test.md",
      "path": "C:\Users\takas\AppData\Roaming\npm\node_modules\npm\docs\content\commands",
      "size": "7428",
      "date_modified": "134093252010785768"
    }
  ]
}
```

観測された型:

* `totalResults`: number（整数として扱える）
* `path`: 文字列（Windows のディレクトリパス）
* `size`: **10 進数の文字列**（数値ではない）
* `date_modified`: **10 進数の文字列**

また、`date_created_column=1` を指定しても、少なくともこの環境では `date_created` は返らなかった。
過去のフォーラム投稿では、HTTP Server の JSON 出力で date created は未サポートとされており、現状は **未実装または無効**と見なすのが安全。

### `date_modified` の解釈（FILETIME）

Everything SDK では更新日時は `FILETIME`（Windows の 64-bit 時刻: 1601-01-01 UTC から 100ns 単位）として提供される。したがって HTTP Server の `date_modified` も、`FILETIME`（`uint64`）を **10 進数文字列としてシリアライズ**した値と解釈するのが整合的。

代表的な変換（FILETIME → UNIX 秒）:

`unix_seconds = (filetime - 116444736000000000) / 10000000`

（`116444736000000000` は 1601-01-01 と 1970-01-01 のオフセットを 100ns 単位にした定数）

### 実装上の注意

* `*_column=0` の列は JSON に現れない（クライアントは「存在しない」を許容する）。
* `size` と `date_modified` は **数値としての意味を持つが文字列**なので、必要に応じて `uint64` にパースする。
* 未知フィールドは無視する（前方互換）。

---

## OpenAPI 3.1（YAML）

以下は **検索API（`json=1` 固定）**のみを記述する。

```yaml
openapi: 3.1.0
info:
  title: Everything HTTP Server JSON Search API (json=1)
  version: "1.2"
  description: |
    voidtools Everything 1.5 の HTTP Server（http_server プラグイン）の検索API。

    - 本仕様は json=1（JSON出力）に限定する。
    - Everything の検索文字列は、Everything の通常の検索構文（演算子、ワイルドカード、関数など）に従う。

    実測（作成者環境）:
    - size は "7699" のように 10 進文字列で返る。
    - date_modified は "133754350660000000" のように 10 進文字列で返る。
      これは Windows FILETIME（1601-01-01 UTC から 100ns 単位の 64-bit 値）を文字列化したものと解釈するのが整合的。

servers:
  - url: http://127.160.164.78:8000
    description: |
      本書の作成者環境（ポート競合回避のために Everything 側設定を変更して使用）。
      一般的な既定値ではないため、あなたの環境に合わせて変更すること。

  - url: http://127.0.0.1:80
    description: |
      既定例（127.0.0.1:80 / http://localhost と同等）。
      ポート80は競合しやすいので、環境に応じて別ポートへ変更する。

  - url: http://{host}:{port}
    description: 任意のホスト/ポート（HTTP Server設定に合わせる）
    variables:
      host:
        default: 127.0.0.1
      port:
        default: "80"

paths:
  /:
    get:
      operationId: search
      summary: Search indexed files/folders (JSON only)
      description: |
        Everything のインデックスを検索し、JSONを返す。

        - `search` は Everything の検索構文を受け付ける。
        - `json` は 1 固定（この仕様では enum で固定）。
        - *_column パラメータを 1 にすると、結果要素に対応するフィールドが追加される。

        認証:
        - HTTP Server の設定で username/password が有効な場合、Basic 認証が要求される。

      security:
        - {}
        - basicAuth: []

      parameters:
        - name: search
          in: query
          required: false
          description: |
            検索文字列。Everything の検索構文（演算子、ワイルドカード、関数）に従う。
            URLクエリとして送るため、`&` や `+` などの予約文字を含む場合は URL エンコードする。

            互換のため `s` / `q` も受け付けるが、新規実装では `search` を推奨する。
          schema:
            type: string
          examples:
            filename:
              summary: Simple filename search
              value: test.md
            and_query:
              summary: AND search (space)
              value: "ABC 123"
            plus_literal:
              summary: Literal plus signs (URL encode as %2B)
              value: "C++"
            ampersand_literal:
              summary: Literal & (URL encode as %26)
              value: "A&B.txt"
            phrase_path:
              summary: Phrase search with a Windows path
              value: '"C:\Program Files\nodejs"'

        - name: s
          in: query
          required: false
          deprecated: true
          description: "`search` の短縮名（互換用）。新規実装では `search` を使用する。"
          schema:
            type: string

        - name: q
          in: query
          required: false
          deprecated: true
          description: "`search` の別名（互換用）。新規実装では `search` を使用する。"
          schema:
            type: string

        - name: offset
          in: query
          required: false
          description: "返却開始位置（0-based）。別名 `o`。"
          schema:
            type: integer
            format: int64
            minimum: 0
            default: 0

        - name: o
          in: query
          required: false
          deprecated: true
          description: "`offset` の短縮名（互換用）。"
          schema:
            type: integer
            format: int64
            minimum: 0

        - name: count
          in: query
          required: false
          description: |
            返却する最大件数。別名 `c`。

            公式 README の既定例では 4294967295（2^32-1）が示される。
            API用途では必ず妥当な上限を指定することを推奨。
          schema:
            type: integer
            format: int64
            minimum: 0
            maximum: 4294967295
            default: 4294967295
          examples:
            recommended:
              summary: Recommended bounded page size
              value: 100

        - name: c
          in: query
          required: false
          deprecated: true
          description: "`count` の短縮名（互換用）。"
          schema:
            type: integer
            format: int64
            minimum: 0
            maximum: 4294967295

        - name: json
          in: query
          required: true
          description: |
            JSONモード指定。HTTP Server は `j` を別名として受け付ける。
            本仕様では 1 固定。
          schema:
            type: integer
            enum: [1]
            default: 1

        - name: j
          in: query
          required: false
          deprecated: true
          description: "`json` の短縮名（互換用）。本仕様では `1` のみ許容。"
          schema:
            type: integer
            enum: [1]

        - name: case
          in: query
          required: false
          description: "大文字小文字を区別（別名 `i`）。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: i
          in: query
          required: false
          deprecated: true
          description: "`case` の短縮名（互換用）。"
          schema:
            type: integer
            enum: [0, 1]

        - name: wholeword
          in: query
          required: false
          description: "単語単位でマッチ（別名 `w`）。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: w
          in: query
          required: false
          deprecated: true
          description: "`wholeword` の短縮名（互換用）。"
          schema:
            type: integer
            enum: [0, 1]

        - name: path
          in: query
          required: false
          description: "フルパスを検索対象に含める（別名 `p`）。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: p
          in: query
          required: false
          deprecated: true
          description: "`path` の短縮名（互換用）。"
          schema:
            type: integer
            enum: [0, 1]

        - name: regex
          in: query
          required: false
          description: "正規表現検索（別名 `r`）。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: r
          in: query
          required: false
          deprecated: true
          description: "`regex` の短縮名（互換用）。"
          schema:
            type: integer
            enum: [0, 1]

        - name: diacritics
          in: query
          required: false
          description: "ダイアクリティカルマークを区別（別名 `m`）。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: m
          in: query
          required: false
          deprecated: true
          description: "`diacritics` の短縮名（互換用）。"
          schema:
            type: integer
            enum: [0, 1]

        - name: path_column
          in: query
          required: false
          description: "結果要素に `path` を含める。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: size_column
          in: query
          required: false
          description: "結果要素に `size` を含める。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: date_modified_column
          in: query
          required: false
          description: "結果要素に `date_modified` を含める。1=ON, 0=OFF。"
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: date_created_column
          in: query
          required: false
          description: |
            結果要素に `date_created` を含める（公式 README にキーが現れる）。

            ただし作成者環境では `date_created_column=1` を指定しても `date_created` は返らなかった。
            現状は未実装または無効と見なすのが安全。
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: attributes_column
          in: query
          required: false
          description: |
            結果要素に `attributes` を含める（公式 README にキーが現れる）。
            （本書では未検証のため、利用する場合は実測して確認すること）
          schema:
            type: integer
            enum: [0, 1]
            default: 0

        - name: sort
          in: query
          required: false
          description: "ソートキー。"
          schema:
            type: string
            enum: [name, path, date_modified, size]
            default: name

        - name: ascending
          in: query
          required: false
          description: "昇順(1) / 降順(0)。"
          schema:
            type: integer
            enum: [0, 1]
            default: 1

      responses:
        "200":
          description: Search results
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/SearchResponse"
              examples:
                observed:
                  summary: Observed response (columns enabled)
                  value:
                    totalResults: 10
                    results:
                      - type: file
                        name: npm-install-ci-test.md
                        path: "C:\Program Files\nodejs\node_modules\npm\docs\content\commands"
                        size: "7699"
                        date_modified: "133754350660000000"
                      - type: file
                        name: npm-install-ci-test.md
                        path: "C:\Users\takas\AppData\Roaming\npm\node_modules\npm\docs\content\commands"
                        size: "7428"
                        date_modified: "134093252010785768"

        "401":
          description: Unauthorized (HTTP Server の設定で username/password が有効な場合)

components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

  schemas:
    SearchResponse:
      type: object
      additionalProperties: true
      required: [totalResults, results]
      properties:
        totalResults:
          type: integer
          format: int64
          minimum: 0
          description: ヒット総数（offset/count の影響を受けない総数）。
        results:
          type: array
          items:
            $ref: "#/components/schemas/SearchResultItem"

    SearchResultItem:
      type: object
      additionalProperties: true
      required: [type, name]
      properties:
        type:
          type: string
          enum: [file, folder]
          description: 結果の種別。
        name:
          type: string
          description: ファイル名またはフォルダ名。

        path:
          type: string
          description: ディレクトリパス（`path_column=1` のときに含まれうる）。

        size:
          type: string
          pattern: "^[0-9]+$"
          description: |
            サイズ（バイト）を表す 10 進数文字列（`size_column=1` のときに含まれうる）。
            必要なら `uint64` としてパースする。

        date_modified:
          type: string
          pattern: "^[0-9]+$"
          description: |
            更新日時を表す 10 進数文字列（`date_modified_column=1` のときに含まれうる）。

            推奨解釈: Windows FILETIME（1601-01-01 UTC から 100ns 単位の 64-bit 値）を 10 進文字列化したもの。
            代表的な変換（FILETIME → UNIX 秒）:

            unix_seconds = (filetime - 116444736000000000) / 10000000

        date_created:
          type: string
          pattern: "^[0-9]+$"
          deprecated: true
          description: |
            作成日時（date_created_column=1 のときに含まれうる、という説明が公式 README に現れる）。

            ただし作成者環境では返らなかったため、現状は未実装または無効と見なすのが安全。

        attributes:
          description: |
            ファイル属性（attributes_column=1 のときに含まれうる）。
            型やビット割り当ては実装依存の可能性があるため、本仕様では固定しない。
          oneOf:
            - type: integer
              format: int64
            - type: string
```

---

## 参考資料（根拠）

以下は本書の根拠として参照した一次情報。

```text
- voidtools/http_server (公式リポジトリ README: URL query string とパラメータ/既定値)
  https://github.com/voidtools/http_server

- voidtools サポート: Everything → Searching（検索構文: 演算子/ワイルドカード/関数等）
  https://www.voidtools.com/support/everything/searching/

- voidtools サポート: Everything → HTTP（HTTP機能の概要）
  https://www.voidtools.com/support/everything/http/

- voidtools forum（JSONレスポンス例: totalResults / results, type/name の存在）
  https://www.voidtools.com/forum/viewtopic.php?t=1782
```
