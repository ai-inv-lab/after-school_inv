# XBRL Financial Compare

EDINETのWebページからダウンロードしたXBRL zipを、Arelleで読み込み、連結のBS/PL/CFから主要な財務指標を作って比較する小さなプログラムです。

最初の記事では、ソシオネクスト（6526）、メガチップス（6875）、ザインエレクトロニクス（6769）を比較する想定です。会計基準や業種の近さをそろえ、セグメントなしの連結値だけを使います。

## できること

- EDINETから手動で落としたXBRL zipを読み込む
- ArelleでXBRL factsを抽出する
- 売上高、営業利益、純利益、総資産、純資産、営業CF、投資CF、研究開発費などをJSON/CSV化する
- 売上高成長率、営業利益率、ROE、自己資本比率、フリーキャッシュフロー、研究開発費率を計算する
- 複数社のXBRL zipを一度に指定し、抽出から比較までまとめて実行する
- HTMLレポートで、PL表、主要指標グラフ、文章項目の比較、使用データのエビデンスをまとめて表示する
- XBRLファイルが手元になくても、サンプルデータで動作確認できる

## セットアップ

このプログラムは `uv` を使います。`uv` はPythonの仮想環境作成、依存関係インストール、コマンド実行をまとめて扱えるツールです。

### uvをインストールする

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

すでにPython環境がある場合は、pipでも入れられます。

```bash
python -m pip install uv
```

インストールできたか確認します。

```bash
uv --version
```

### 依存関係を入れる

macOS / Linux:

```bash
cd xbrl_financial_compare
uv sync
```

Windows PowerShell:

```powershell
cd xbrl_financial_compare
uv sync
```

`uv sync` を実行すると、このフォルダ内に `.venv/` が作られ、Arelleやpandasなどが入ります。

## まず試す

macOS / Linux:

```bash
cd xbrl_financial_compare
./scripts/run_sample.sh
```

Windows PowerShell:

```powershell
cd xbrl_financial_compare
.\scripts\run_sample.ps1
```

PowerShellでスクリプト実行が止められる場合は、このターミナルだけ実行を許可します。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\run_sample.ps1
```

スクリプトを使わずに直接実行する場合:

```bash
uv run xbrl-financial-compare sample --out sample/20260627/processed
uv run xbrl-financial-compare compare "sample/20260627/processed/*.json" --out sample/20260627
```

出力:

- `sample/20260627/processed/*.json`
- `sample/20260627/comparison_metrics.csv`
- `sample/20260627/report.html`

Windowsではワイルドカードの展開方法がmacOS/Linuxと異なるため、`"sample/20260627/processed/*.json"` のように引用符付きで渡しても動くようにしています。

## 記事からリンクする実データ出力

このリポジトリには、実際にEDINETから取得したXBRL zipをこのプログラムで処理した成果物を `sample/20260627/` に置いています。

- HTMLレポート: `sample/20260627/report.html`
- 指標CSV: `sample/20260627/comparison_metrics.csv`
- JSON: `sample/20260627/processed/6526.json`, `sample/20260627/processed/6875.json`, `sample/20260627/processed/6769.json`

対象書類は、ソシオネクスト（6526）、メガチップス（6875）、ザインエレクトロニクス（6769）の有価証券報告書XBRLです。元zipそのものはリポジトリには含めず、JSON/CSV/HTMLの出力結果だけを置いています。

GitHub上でHTMLをそのまま開く場合は、通常のファイル表示ではなく、GitHub PagesやRaw表示を使います。記事からは、公開後のPages URLに差し替えるのが読みやすいです。

## Apple containerで試す

Appleの `container` CLI が入っている環境では、同梱の `Dockerfile` を使ってコンテナ内でテストを実行できます。

```bash
cd xbrl_financial_compare
container system start
container build -t xbrl-financial-compare .
container run --rm xbrl-financial-compare
```

このコンテナの既定コマンドは、`uv run pytest tests -q` です。EDINETからダウンロードしたzipを使う場合は、ローカルの `data/raw/` をコンテナにマウントして `compare-zips` を実行します。

## EDINETからXBRLをダウンロードする流れ

1. EDINETのWebページを開く
2. 企業名や証券コードで検索する
3. 有価証券報告書を選ぶ
4. XBRL一式のzipをダウンロードする
5. `data/raw/` に置く

このプログラムでは、EDINET APIではなく、読者がWebページで検索してダウンロードしたzipを処理します。

## 複数のXBRL zipを一気に比較する

macOS / Linux:

```bash
cd xbrl_financial_compare
uv run xbrl-financial-compare compare-zips \
  data/raw/socionext.zip \
  data/raw/megachips.zip \
  data/raw/thine.zip \
  --out outputs
```

Windows PowerShell:

```powershell
cd xbrl_financial_compare
uv run xbrl-financial-compare compare-zips `
  data\raw\socionext.zip `
  data\raw\megachips.zip `
  data\raw\thine.zip `
  --out outputs
```

会社名、証券コード、期末日はXBRL zip内の提出者情報から取得します。

出力:

- `outputs/processed/*.json`
- `outputs/comparison_metrics.csv`
- `outputs/report.html`

`report.html` には次を入れています。

- 今年度・前年度のPL表
- 売上高成長率、営業利益率、ROE、自己資本比率、研究開発費率などのグラフ
- 主力ビジネス、経営環境・対処すべき課題、業績・財政状態の説明など、文章項目の比較
- 使用したXBRL factのQName、コンテキストID、期間

EDINETのXBRLでは、`CurrentYearDuration` や `CurrentYearInstant` など、コンテキストIDの命名規約が比較的そろっています。そのため、このサンプルではコンテキストIDを手がかりにしています。

ただし、XBRL一般ではコンテキストIDの名前だけに頼るべきではありません。特にEDGARでは会社ごとにID名が異なることがあるため、本来はコンテキストIDが指す `context` の中身を確認します。contextには、対象企業、期間または時点、連結・単体やセグメントなどの追加軸が入ります。

XBRLでは、まとまった文章が入る項目に `TextBlock` という名前が付いていることがあります。これは普段の日本語として一般的な言い方ではないため、このREADMEでは「文章項目」と呼びます。たとえば、有価証券報告書の「事業の内容」や「経営方針、経営環境及び対処すべき課題等」のような長めの説明文が、ひとかたまりで入っている項目です。

文章項目の比較では、次のXBRLタグを使います。

- `DescriptionOfBusinessTextBlock`: 主力ビジネスを把握する入口
- `BusinessPolicyBusinessEnvironmentIssuesToAddressEtcTextBlock`: 経営環境、経営方針、対処すべき課題を見るための入口
- `ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock`: 業績や財政状態について、会社自身の説明を読むための入口

これらは長文になりやすいため、HTMLレポートのカード上では抜粋を表示します。カードの「全文を開く」をクリックすると、別ウインドウで全文を確認できます。抽出元のQName、コンテキストIDも併記するので、どのXBRL factから読んだかを確認できます。

## 1社ずつ処理したい場合

通常は `compare-zips` を使えば十分です。途中のJSONを個別に確認したい場合だけ、`extract` と `compare` を分けて使います。

```bash
uv run xbrl-financial-compare extract \
  --zip data/raw/socionext.zip \
  --ticker 6526 \
  --company "ソシオネクスト"
```

複数社を処理したあと、比較します。

```bash
uv run xbrl-financial-compare compare data/processed/*.json --out outputs
```

## venv + pipで動かしたい場合

uvが使えない環境では、標準のvenvでも動かせます。

```bash
cd xbrl_financial_compare
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m xbrl_financial_compare sample --out sample/20260627/processed
.venv/bin/python -m xbrl_financial_compare compare "sample/20260627/processed/*.json" --out sample/20260627
```

Windows PowerShell:

```powershell
cd xbrl_financial_compare
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m xbrl_financial_compare sample --out sample/20260627/processed
.\.venv\Scripts\python.exe -m xbrl_financial_compare compare "sample/20260627/processed/*.json" --out sample/20260627
```

## 注意

- XBRLはそのまま読むものではなく、Arelleのようなソフトウェアで解析します。
- EDINETの提出書類ごとにタグや文脈が異なることがあります。このプログラムは、連結の `CurrentYearDuration` / `Prior1YearDuration` / `CurrentYearInstant` などのコンテキストを優先して使います。
- 投資判断ではなく、一次情報を扱う練習用です。
