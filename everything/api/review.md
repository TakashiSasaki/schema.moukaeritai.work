**Rephrased (English)**: *I will thoroughly review the nine attached files (OpenAPI schemas, Python verification scripts, and documentation for three APIs) and check whether they match our current findings about Everything’s HTTP Server API. For ambiguous or previously unresolved points, I will re-check authoritative web sources and produce a detailed report pointing out improvable parts of the provided OpenAPI-related files.*

---

# Everything HTTP Server（voidtools）HTTP API 精読レビュー報告書

作成日時: **2025-12-25（Asia/Tokyo）**

## 目次

1. 結論（整合性サマリ）
2. 入力（ユーザー提供ファイル一覧）
3. 一次情報（Web）で確定できる仕様
4. 3 API 別レビュー
5. 未確定・バージョン差が濃い論点（再検証の優先度付き）
6. 改善提案（OpenAPI / Python / ドキュメント）
7. 改善案（差分レベルの具体案）
8. 参考文献一覧（URL明記）
9. キーワード
10. 図表一覧
11. ユーザー提供ファイル一覧（再掲）

---

## 1. 結論（整合性サマリ）

* **HTML検索（json=0 / 省略）**の OpenAPI とドキュメントは、公式のクエリパラメータ体系（`search/s/q`, `offset/o`, `count/c`, `json/j`, 検索オプション群, `sort`, `ascending`）および HTML 既定値と概ね整合しています。
* **JSON検索（json=1）**は、ドキュメント側では検索オプションや短縮名を扱う前提になっているのに対し、OpenAPI（YAML）側は **検索オプション（case/wholeword/path/regex/diacritics）と `sort/ascending`、`attributes_column` が欠落**しています。ここが最大の不整合です。 
* **バイナリダウンロード**は、公式が明示しているのは「ファイルダウンロード許可」「Basic認証」「Range request対応」などで、**URLパスへの投影ルール自体は一次情報（公式ページ/README）では明確に書かれていません**。一方で、あなたの検証結果として **`/C%3A/Windows/win.ini`（ブラウザスタイル）と `/C%3A%2FWindows%2Fwin.ini`（単一セグメントスタイル）がどちらも 200** を返す点まで確認済みになっており、実装仕様としては「観測事実」として扱えます。

---

## 2. 入力（ユーザー提供ファイル一覧）

3 API ×（ドキュメント .md / 検証スクリプト .py / OpenAPI .yaml）= 9ファイル：

* download-file-api.md / .py / .yaml 
* search-api-html.md / .py / .yaml  
* search-api-json.md / .py / .yaml   

---

## 3. 一次情報（Web）で確定できる仕様

公式（voidtools support / GitHub README）で「確定」と言える範囲は以下です。

* **HTTP Server の機能として**検索・ダウンロードが可能であること、Basic認証の設定が可能であること、Range request をサポートすること。
* **検索APIのクエリパラメータ体系**（`search/s/q`, `offset/o`, `count/c`, `json/j`、検索オプション群、`sort`, `ascending`）と、**HTML/JSONそれぞれの既定値**（特に `count` が HTML=32、JSON=4294967295、`json` が HTML=0/JSON=1 など）。
* JSONモードで `*_column` が存在すること（`path_column`, `size_column`, `date_modified_column`, `date_created_column`, `attributes_column` がREADME上に出る）。

※voidtools forum の該当スレッドは、本環境からは **403 で取得できず**確認不能でした。
（したがって「フォーラムに書いてあるから確定」とは扱っていません。）

---

## 4. 3 API 別レビュー

### 4.1 HTML検索（search-api-html.*）

**整合している点**

* HTMLモードの既定値（`count=32`, `json=0`, 検索オプション既定0、`sort=name`, `ascending=1`）を明示。 公式既定値と整合。
* `search` の別名として `s` / `q` を deprecated 扱いで併記しており、公式の「複数キーを受ける」現実に合っている。
* 検証結果として、`count/offset`、`case`、`sort/ascending` が期待通り動作したことを記録。

**改善余地（軽微）**

* HTMLレスポンスの schema を単なる `string` にしているのは妥当ですが、クライアント側でやるべき最低限（文字コード UTF-8、リンク抽出の要点）を「仕様」ではなく「利用ノート」として、md側にもう少し強調してもよい（OpenAPIに入れ過ぎない方がよい）。

---

### 4.2 JSON検索（search-api-json.*）

**ドキュメント（md）と一次情報の整合**

* `search` 構文と「URLクエリとしてのエンコード注意」を明確化している点は有用。
* `search/s/q`, `offset/o`, `count/c`, `json/j` と、検索オプション群（`case/i` 等）を **併記する方針**が明記されている。
* `size` と `date_modified` が「10進文字列」で返るという観測結果を、OpenAPIの説明に反映している。 

**最大の不整合（要修正）**

* **OpenAPI（search-api-json.yaml）に、mdが前提としているクエリが落ちています。**

  * 欠落: `case/wholeword/path/regex/diacritics` と短縮名（`i/w/p/r/m`）、`sort/ascending`、`attributes_column`。
  * 公式README/サポートの「URL query string」では、JSON既定値セットに検索オプション群が含まれ、`sort/ascending` も共通に存在します。
  * mdはそれを前提として説明しているのに、OpenAPI側の parameters が追随していないため、**コード生成や検証スクリプトのカバレッジが落ちます**。 

**date_created_column の扱い**

* 公式README上は `date_created_column` が存在しますが、あなたの実測では返ってこない（無視される）と明記されています。 
* 結論としては、OpenAPIでは **「パラメータは存在するが、フィールドは optional かつ未出現を許容」**が安全です（現状の方針は正しい）。

---

### 4.3 バイナリダウンロード（download-file-api.*）

**一次情報で固い部分**

* HTTP Server の設定で「ファイルダウンロード許可」や「ユーザー名/パスワード（Basic認証）」や「Range request対応」が説明されている。
* mdでも Basic 認証と Range を仕様要点として整理。

**あなたの実機検証で固い部分（＝仕様として採用可能な“観測事実”）**

* **ブラウザスタイル** `/C%3A/Windows/win.ini` と、**単一セグメントスタイル** `/C%3A%2FWindows%2Fwin.ini` の双方が 200 を返す。
* Range で 206 が返る。
* インデックス更新遅延により「作成直後は404が出る場合がある」という運用上の注意。

**改善余地（OpenAPI的に重要）**

* download-file-api.yaml は、「OpenAPIツール都合で単一セグメントスタイルを推奨する」構造になっていますが、**OpenAPIのpath parameterではスラッシュを含む実パス表現を正確にモデル化できません**。この点は md にある通りで、OpenAPIには **“限界の明示”**と **“クライアント実装はURLを手で組む”**という注意を、より強く入れるべきです。
* YAML内の「サーバ側で `..` を正規化する」等の説明は、一次情報では確定できません（コード参照が必要）が、現状では web 側からリポジトリのソースファイル閲覧に制約があり裏取り不能でした。

  * 対策: **“観測/推測”ラベル**を明示し、仕様本文（MUST）にしない。

---

## 5. 未確定・バージョン差が濃い論点（再検証優先度つき）

優先度A（OpenAPIを変える価値が高い）

1. `attributes_column` の有効性と返却フィールド名（存在/型）

   * README上は存在するため OpenAPI に追加すべき。
2. `date_created_column` が返らない件のバージョン依存（1.5 alpha 固有か、常に未実装か）

   * 現状は optional でよいが、「返らない前提」をより強く打ち出すなら、検証を増やす価値があります。

優先度B（運用・実装ノートとして重要）
3. ダウンロード時のステータス（download disabled / 権限不足 / ロック中）で 403/404 がどう分岐するか

* mdは揺れを許容しており妥当。

4. `Content-Disposition` の有無、`Content-Type` 推定ルール

   * OpenAPIでは `application/octet-stream` 基本でよいが、実測ヘッダを記録すると実装品質が上がります。

---

## 6. 改善提案（OpenAPI / Python / ドキュメント）

### 6.1 OpenAPI（最優先）

* **search-api-json.yaml に不足パラメータを追加**

  * `case/i`, `wholeword/w`, `path/p`, `regex/r`, `diacritics/m`, `sort`, `ascending`, `attributes_column`。
  * 公式が示すクエリ体系と整合させる。
* download-file-api.yaml は「単一セグメントスタイル」を **“観測上動作”**として残すのは有用だが、**推奨を逆転**させるのが安全

  * 推奨: HTMLリンク互換（ブラウザスタイル）
  * 代替: 単一セグメント（ツール都合）
  * どちらも「Everything 1.5 alpha 実測でOK」を明記。

### 6.2 Python検証スクリプト

* JSON検索のスクリプトに、OpenAPIに追加する予定のパラメータ（`case/wholeword/path/regex/diacritics`, `sort/ascending`, `attributes_column`）のテストを追加し、**OpenAPIと検証の同期**を取る。
* ダウンロードのスクリプトは既に「両スタイル」「Range」「インデックス遅延」を扱っており強い。

  * 追加するなら、レスポンスヘッダ（`Accept-Ranges`, `Content-Range`, `Last-Modified`）のログ保存。

### 6.3 ドキュメント（md）

* 「公式で言っている」vs「あなたの環境で観測した」を、章/ラベルで機械的に分離する（将来の差分吸収が楽）。
* JSON側で `date_created_column` が返らない件は既に明確。

  * 追加で「返ってくる環境があったらログ添付して差分管理する」運用指針を入れると、将来の再調査が短縮できます。

---

## 7. 改善案（差分レベルの具体案）

### 7.1 search-api-json.yaml に追加すべき parameters（抜粋）

以下を `paths: /: get: parameters:` に追加（もしくは components/parameters 化）するのが最短です。
（※ここでは“追加すべき最小ブロック”のみ提示します）

```yaml
# 追加: 検索オプション（0/1） + 短縮名
- name: case
  in: query
  required: false
  description: "大文字小文字を区別（別名 `i`）。1=ON, 0=OFF。"
  schema: { type: integer, enum: [0, 1], default: 0 }
- name: i
  in: query
  required: false
  deprecated: true
  description: "`case` の短縮名（互換用）。"
  schema: { type: integer, enum: [0, 1] }

- name: wholeword
  in: query
  required: false
  description: "単語単位マッチ（別名 `w`）。"
  schema: { type: integer, enum: [0, 1], default: 0 }
- name: w
  in: query
  required: false
  deprecated: true
  description: "`wholeword` の短縮名（互換用）。"
  schema: { type: integer, enum: [0, 1] }

- name: path
  in: query
  required: false
  description: "フルパスも検索対象（別名 `p`）。"
  schema: { type: integer, enum: [0, 1], default: 0 }
- name: p
  in: query
  required: false
  deprecated: true
  description: "`path` の短縮名（互換用）。"
  schema: { type: integer, enum: [0, 1] }

- name: regex
  in: query
  required: false
  description: "正規表現検索（別名 `r`）。"
  schema: { type: integer, enum: [0, 1], default: 0 }
- name: r
  in: query
  required: false
  deprecated: true
  description: "`regex` の短縮名（互換用）。"
  schema: { type: integer, enum: [0, 1] }

- name: diacritics
  in: query
  required: false
  description: "ダイアクリティカルマークを区別（別名 `m`）。"
  schema: { type: integer, enum: [0, 1], default: 0 }
- name: m
  in: query
  required: false
  deprecated: true
  description: "`diacritics` の短縮名（互換用）。"
  schema: { type: integer, enum: [0, 1] }

# 追加: sort / ascending
- name: sort
  in: query
  required: false
  description: "ソートキー。"
  schema: { type: string, enum: [name, path, date_modified, size], default: name }
- name: ascending
  in: query
  required: false
  description: "昇順(1) / 降順(0)。"
  schema: { type: integer, enum: [0, 1], default: 1 }

# 追加: attributes_column
- name: attributes_column
  in: query
  required: false
  description: "結果要素に attributes を含める（1=ON, 0=OFF）。"
  schema: { type: integer, enum: [0, 1], default: 0 }
```

この追加は、公式のパラメータ体系（検索オプション群・sort/ascending・attributes_column）に寄せる目的です。

---

## 8. 参考文献一覧（URL明記）

```text
- voidtools support: Everything HTTP Server
  https://www.voidtools.com/support/everything/http/

- voidtools/http_server (GitHub) - README (URL query string / defaults)
  https://github.com/voidtools/http_server
```

（注）voidtools forum は本環境では 403 となり取得できませんでした。

---

## 9. キーワード

Everything, voidtools, HTTP Server, OpenAPI 3.1, Basic Auth, Range request, json=1, HTML mode, query parameters, FILETIME, percent-encoding

---

## 10. 図表一覧

* 図表なし（テキストのみ）

---

## 11. ユーザー提供ファイル一覧（再掲）

* download-file-api.md / download-file-api.py / download-file-api.yaml 
* search-api-html.md / search-api-html.py / search-api-html.yaml  
* search-api-json.md / search-api-json.py / search-api-json.yaml   

---

必要なら、上の「追加parameters」を実際にあなたの `search-api-json.yaml` 全体へ適用した“置換後YAML全文”も、この場で生成できます（既存の構造を崩さずに差し込みます）。
