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

## 8. 検証結果

`search-api-json.py` による実機検証（Everything 1.5 alpha）の結果、以下の挙動を確認済み。

1.  **JSON構造**: `json=1` で正しい JSON (`totalResults`, `results`) が返る。
2.  **パラメータ動作**: `count`, `offset`, `sort` が期待通り機能する。
3.  **カラム追加**: `path`, `size`, `date_modified` パラメータで各フィールドが結果に追加される。
    *   `size`: **10進文字列**として返る（例: "7699"）。
    *   `date_modified`: **10進文字列**として返る。
    *   `date_created`: パラメータを指定しても返ってこない（仕様通り未実装/無効扱い）。

## 9. OpenAPI 定義ファイル

詳細なOpenAPI定義（YAML）は、以下のファイルを参照してください。

* [search-api-json.yaml](search-api-json.yaml)


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
