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

## 8. 検証結果

`search-api-html.py` による実機検証（Everything 1.5 alpha）の結果、以下の挙動を確認済み。

1.  **基本検索**: `search` パラメータで指定した文字列（ファイル名）を含む行が HTML 内に見つかる。
2.  **ページング**: `count` で件数が制限され、`offset` で続きのページが取得できる。
3.  **大文字小文字 (case)**:
    *   `case=0` (既定): 大文字小文字を区別せずヒットする。
    *   `case=1`: 区別し、ヒットしない（0件）挙動となる。
4.  **ソート**: `sort=name`, `ascending=0` で名前の降順に並ぶことを確認。

## 9. OpenAPI 定義ファイル

詳細なOpenAPI定義（YAML）は、以下のファイルを参照してください。

* [search-api-html.yaml](search-api-html.yaml)
