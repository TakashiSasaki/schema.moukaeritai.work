# Everything HTTP Server（Everything 1.5）HTML検索API（`json=0` または省略）

## 目的

Everything（voidtools）の HTTP Server を **ブラウザ向け HTML ページとして**利用する場合（`json=0` または `json` パラメータ省略）に限定して、検索 API の入出力を整理し、OpenAPI 3.1（YAML）として提示する。

* 対象: **検索（HTMLページ出力）**
* 非対象: JSON検索（`json=1`）、ファイル閲覧・ダウンロード

注意: `json=0` は人間向けの HTML であり、**プログラムからの安定利用（スクレイピング）には不向き**。API用途なら `json=1` が推奨。

---

## HTTPサーバの既定値とポート変更

Everything の HTTP Server は既定で **127.0.0.1:80** で待ち受ける。ポート 80 は OS 側で既に使用中のことがあるため、別ポート（例: 8080）への変更が案内されている。

### 本書の作成者環境

本書の作成者は、80 番ポートの競合を避けるため、Everything HTTP Server の設定を **`http://127.160.164.78:8000`** に変更して使用している。

重要:

* `http://127.160.164.78:8000` は一般的な既定値ではなく、**この文書の作成者が選択した設定**に過ぎない。
* あなたの環境では、Everything 側の HTTP Server 設定（バインド先/ポート）に合わせて URL を読み替えること。

---

## エンドポイント概要（HTML）

* HTTP メソッド: **GET**
* パス: `/`
* クエリ: `key=value` 形式（不要なペアは省略可能）

README では `json`（または短縮の `j`）が **非ゼロ**のとき JSON を返す、と説明される。したがって `json=0` または `json` 省略時は HTML ページが返る（HTTP 200 の場合）。

---

## クエリパラメータ（HTMLモード）

HTML モードの既定値として、README に次が示されている。

* `offset=0`
* `count=32`
* `json=0`
* 検索オプション（`case/wholeword/path/regex/diacritics`）はすべて 0
* `sort=name`
* `ascending=1`

APIの安定性のため、本書は正規名（長いキー）を推奨し、短縮名は互換として `deprecated` 扱いにする。

### 基本

* `search`（別名: `s`, `q`）: 検索文字列
* `offset`（別名: `o`）: 先頭から何件目（0-based）から表示するか
* `count`（別名: `c`）: 表示する最大件数（HTMLの既定は 32）
* `json`（別名: `j`）: **HTMLモードは 0 か省略**

### 検索オプション（0/1）

* `case`（別名: `i`）: 大文字小文字を区別
* `wholeword`（別名: `w`）: 単語単位でマッチ
* `path`（別名: `p`）: フルパスも検索対象
* `regex`（別名: `r`）: 正規表現検索
* `diacritics`（別名: `m`）: ダイアクリティカルマーク（アクセント）を区別

### ソート

* `sort`: `name` / `path` / `date_modified` / `size`
* `ascending`: 1 で昇順、0 で降順

---

## レスポンス（HTML）

成功時（HTTP 200）には `text/html` の **人間可読な検索結果ページ**が返る。

最小例（先頭の雰囲気）:

```html
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>...</title>
  </head>
  <body>...</body>
</html>
```

---

## OpenAPI 3.1（YAML）

以下は **検索（HTML出力）**のみに限定した OpenAPI。

```yaml
openapi: 3.1.0
info:
  title: Everything HTTP Server HTML Search API (json=0)
  version: "1.0"
  description: |
    voidtools Everything 1.5 の HTTP Server（http_server プラグイン）の検索（HTML）仕様。

    - 本仕様は HTML 出力（json=0 または json パラメータ省略）に限定する。
    - `json`（または `j`）が非ゼロの場合は JSON が返るが、本仕様の対象外。

    注意: HTML は人間向けであり、画面構造の変更に弱い（スクレイピング用途には不向き）。

servers:
  - url: http://127.160.164.78:8000
    description: |
      本書の作成者環境（ポート競合回避のために Everything 側設定を変更して使用）。
      一般的な既定値ではないため、あなたの環境に合わせて変更すること。

  - url: http://127.0.0.1:80
    description: |
      既定例（127.0.0.1:80 / http://localhost と同等）。
      ポート80は競合しやすいので、環境に応じて別ポートへ変更する。

paths:
  /:
    get:
      operationId: searchHtml
      summary: Search indexed files/folders (HTML page)
      description: |
        Everything のインデックスを検索し、HTMLページ（text/html）を返す。

        - `json=0` または `json` 省略で HTML モード。
        - `json`（または `j`）が非ゼロの場合は JSON を返すが、本仕様では扱わない。

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
            検索文字列。Everything の検索構文に従う。
            URLクエリとして送るため、`&` や `+` などの予約文字を含む場合は URL エンコードする。
          schema:
            type: string
          examples:
            filename:
              summary: Simple filename search
              value: test.md
            and_query:
              summary: AND search (space)
              value: "ABC 123"

        - name: s
          in: query
          required: false
          deprecated: true
          description: "`search` の短縮名（互換用）。新規実装では `search` を推奨。"
          schema:
            type: string

        - name: q
          in: query
          required: false
          deprecated: true
          description: "`search` の別名（互換用）。新規実装では `search` を推奨。"
          schema:
            type: string

        - name: offset
          in: query
          required: false
          description: "返却開始位置（0-based）。HTMLモード既定は 0。別名 `o`。"
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
            表示する最大件数。HTMLモード既定は 32。別名 `c`。
          schema:
            type: integer
            format: int64
            minimum: 0
            default: 32

        - name: c
          in: query
          required: false
          deprecated: true
          description: "`count` の短縮名（互換用）。"
          schema:
            type: integer
            format: int64
            minimum: 0

        - name: json
          in: query
          required: false
          description: |
            HTMLモード指定。省略時の既定も 0。
            非ゼロの場合は JSON を返す（対象外）。
          schema:
            type: integer
            enum: [0]
            default: 0

        - name: j
          in: query
          required: false
          deprecated: true
          description: "`json` の短縮名（互換用）。HTMLモードは 0 のみ。"
          schema:
            type: integer
            enum: [0]

        - name: case
          in: query
          required: false
          description: "大文字小文字を区別（別名 `i`）。1=ON, 0=OFF。HTMLモード既定は 0。"
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
          description: "単語単位でマッチ（別名 `w`）。1=ON, 0=OFF。HTMLモード既定は 0。"
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
          description: "フルパスを検索対象に含める（別名 `p`）。1=ON, 0=OFF。HTMLモード既定は 0。"
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
          description: "正規表現検索（別名 `r`）。1=ON, 0=OFF。HTMLモード既定は 0。"
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
          description: "ダイアクリティカルマークを区別（別名 `m`）。1=ON, 0=OFF。HTMLモード既定は 0。"
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

        - name: sort
          in: query
          required: false
          description: "ソートキー。HTMLモード既定は name。"
          schema:
            type: string
            enum: [name, path, date_modified, size]
            default: name

        - name: ascending
          in: query
          required: false
          description: "昇順(1) / 降順(0)。HTMLモード既定は 1。"
          schema:
            type: integer
            enum: [0, 1]
            default: 1

      responses:
        "200":
          description: HTML page (human-readable)
          content:
            text/html:
              schema:
                type: string
              examples:
                htmlSearchPage:
                  summary: Example HTML (truncated)
                  value: |
                    <html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>...</title></head>
                    <body>...</body></html>

        "401":
          description: Unauthorized (username/password が有効な場合)
          content:
            text/html:
              schema:
                type: string

components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
```
