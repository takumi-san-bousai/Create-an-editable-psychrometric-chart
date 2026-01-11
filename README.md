# Create-an-editable-psychrometric-chart
プレゼンボードに利用可能な空気線図のSVGデータを作成するためのコードです

仕様書
1. 目的・スコープ
1.1 目的
EPW気象データから、外気状態点（乾球温度・湿度）をサイコロメトリックチャート上に表現し、プロットを生成する。
出力は **プレゼンボードに貼り込めるベクタ形式（SVG）**とする。

1.2 依存ライブラリ（前提）

shimeri：湿り空気物性計算＋Plotlyベースのチャート描画ライブラリ。

PsychrometricChart は Plotly の go.Figure を拡張したクラスで、背景の等RH/等DB/等EN線や軸設定を持つ。

密度プロット用に add_histogram_2d_contour(en, hr, **kwargs) を提供。

点群追加用に add_points(en, hr, **kwargs) を提供。

物性計算は PsychrometricCalculator（CoolPropベース）で、get_all() は5変数のうち任意2つから残りを算出する。

Plotlyの静的画像出力（SVG）には write_image()（Kaleido等）を使用。SVG含む形式に対応。

2. 入出力仕様
2.1 入力（EPW）

入力ファイル：EnergyPlus Weather File（*.epw）

利用フィールド（最低限）：

Dry Bulb Temperature（℃、欠損=99.9）

Relative Humidity（%、欠損=999）

Atmospheric Station Pressure（Pa、欠損=999999）

レコード数：

通常年：8760（1時間）を想定しつつ、EPWの仕様上 8784（うるう年/設計上の拡張）等も許容する。

2.2 出力（SVG）

出力形式：SVG（1図=1ファイル）

出力種類：

月別：12枚（Jan〜Dec）

季節別：デフォルト 4枚（DJF/MAM/JJA/SON）＋ユーザー定義を許容

出力先ディレクトリ：--out_dir で指定

ファイル命名（デフォルト案）：

月別：{site}_{year}_M{MM}_psychro_density.svg

季節別：{site}_{year}_S{season_name}_psychro_density.svg

{site} はEPWヘッダの地名（取得不可なら unknown_site）

{year} はEPWの年（複数年混在なら multi）

3. 機能要件
3.1 月別密度プロット

EPW時系列を月でフィルタし、各月の点群（乾球温度・相対湿度）を物性変換して **（エンタルピー en, 絶対湿度 hr）**に変換する。

shimeri.PsychrometricChart 上に **2Dヒストグラム等高線（密度）**を追加する。add_histogram_2d_contour(en, hr, **kwargs) を使用する。

オプションで、点群（scatter）を薄く重ねられる（プレボ用途では「密度のみ」が基本）。

3.2 季節別密度プロット

季節定義（デフォルト）：

Winter = Dec, Jan, Feb

Spring = Mar, Apr, May

Summer = Jun, Jul, Aug

Autumn = Sep, Oct, Nov

CLIまたは設定ファイルで任意の月セットを定義できるようにする（例：夏季運転=7–9、冬季運転=12–3 など）。

季節ごとに同様に密度プロットSVGを出力。

3.3 EPW→物性変換

PsychrometricCalculator を使用し、入力2変数（例：dbとrh）から hr（g/kg）と en（kJ/kg）を得る。get_all() は「5変数のうち2変数が必要」という制約があるため、db/rh を必須とする（あるいは db/wb 等の代替入力も将来拡張）。

大気圧はEPWの Pa を kPa に変換し、PsychrometricChart(pressure=kPa) に渡す（PsychrometricChart の引数は kPa）。

4. 非機能要件（プレゼンボード品質）
4.1 図の体裁（SVG前提）

文字・線が細すぎて印刷で潰れないように、最低線幅やフォントサイズの下限を設ける。

背景：白（Plotlyテンプレート plotly_white ベース）

余白（margin）を明示制御し、トリミング不要な見切れないSVGを出力。

出力サイズ：--width --height（px）で指定（プレボ貼り込み想定の縦横比に合わせる）。

4.2 再現性

同一入力・同一パラメータで同一SVGが得られること（乱数不使用）。

バージョン差による出力差を抑えるため、依存関係は requirements.txt か pyproject.toml でピン留め（特に Plotly/Kaleido）。

5. CLI（コマンドライン）仕様
5.1 コマンド名（案）

epw2psychro-svg

5.2 引数

必須：

--epw PATH：入力EPW

--out_dir PATH：出力先

任意（代表）：

--pressure_source {epw,constant}（default: epw）

--pressure_kpa FLOAT：pressure_source=constant時に使用

--seasons_config PATH：季節定義JSON/YAML（後述）

--make_monthly / --no-monthly（default: make）

--make_seasonal / --no-seasonal（default: make）

--density_bins_x INT --density_bins_y INT：2Dヒストグラム解像度

--density_ncontours INT：等高線本数

--colorscale NAME：例 Turbo 等

--opacity FLOAT：密度レイヤ透明度

--show_colorbar / --hide_colorbar（default: hide：プレボでは凡例を別途置く想定）

--add_scatter / --no-scatter：点群の重ね合わせ

--width INT --height INT：出力サイズ

--locale {en,ja}：軸タイトル等の言語（default: en）

--log_level {DEBUG,INFO,WARNING,ERROR}

5.3 実行例（仕様例）

月別＋季節別をすべて出力

epw2psychro-svg --epw tokyo.epw --out_dir out/

季節定義をカスタム（例：夏=7-9、冬=12-3）

epw2psychro-svg --epw tokyo.epw --out_dir out/ --seasons_config seasons.json

6. 設定ファイル仕様（季節定義）
6.1 フォーマット（JSON例）

キー：季節名

値：含める月番号配列

例：

{
  "SummerOperation": [7, 8, 9],
  "WinterOperation": [12, 1, 2, 3],
  "Shoulder": [4, 5, 6, 10, 11]
}

6.2 バリデーション

月は 1–12 の整数

重複許容：原則「許容」だが、デフォルトは警告（同じ月が複数季節に入ると解釈が曖昧）

空配列はエラー

7. 内部設計（モジュール分割）
7.1 ディレクトリ（案）

src/epw2psychro_svg/

cli.py：引数処理、全体制御

epw_reader.py：EPWパース、欠損処理、datetime生成

psychro_transform.py：db/rh/p→en/hr変換

grouping.py：月別・季節別フィルタ、統計（件数等）

plot_factory.py：PsychrometricChart生成、レイアウト統一、密度レイヤ追加

exporter.py：SVG出力（Plotly write_image）

models.py：設定・データ構造（dataclass）

logging_utils.py

7.2 主要データ構造（案）

WeatherRecordFrame（pandas.DataFrame）

dt（datetime）

month（int）

db_c（float）

rh_pct（float）

p_pa（float）

PsychroPointFrame

en_kj_per_kg（float）

hr_g_per_kg（float）

month / season

8. 処理フロー（逐次）

EPW読み込み

ヘッダ8行を読み飛ばし、データ部CSVをパース

欠損値を NaN 化：

db=99.9、rh=999、p=999999 を欠損扱い

日時生成

year/month/day/hour/minute から dt を生成

圧力決定

pressure_source=epw の場合：

レコードごとに p を使うか、代表値（中央値）に集約するかを仕様で選ぶ

「図としての一貫性」を優先し、代表値（中央値）を採用をデフォルト推奨（仕様固定）

物性変換

shimeri の PsychrometricCalculator.get_all() を用い、db と rh を入力として en, hr を得る（圧力は kPa）。

グルーピング

月別：month==1..12

季節別：設定ファイル定義に従う

図生成

chart = PsychrometricChart(pressure=kPa) を生成（背景等が自動描画される）。

chart.add_histogram_2d_contour(en, hr, **density_kwargs) で密度等高線を追加。

オプションで chart.add_points(en, hr, **scatter_kwargs) を追加。

タイトル・注記（例：Tokyo / Aug / N=744）を配置

SVG出力

fig.write_image("xxx.svg") を使用（Kaleido等）。SVG対応。

9. 密度プロット仕様（Histogram2dContour）
9.1 デフォルト推奨パラメータ（仕様値）

nbinsx=40, nbinsy=30（図面用途で過度に細かくしない）

ncontours=8

contours_coloring="fill"（等高線の塗り）

showscale=False（プレボでは色バー無しを既定。必要ならON）

opacity=0.85

hoverinfo="skip"（shimeri側も未指定時にskipへ寄せる実装）

9.2 注意点

add_histogram_2d_contour は内部で座標をスキュー変換して追加する（ユーザー側は en/hr を渡せばよい）。

プレボ用途では「色の意味」を注釈で補う（例：濃いほど出現頻度が高い）。

10. エラーハンドリング

EPWが読めない：FileNotFoundError／フォーマットエラー → 明示メッセージ

必須列欠落：year/month/day/db/rh/p が不足 → エラー

欠損が多すぎる：

月/季節で有効点が min_points 未満（例：50未満）→ その図はスキップし警告ログ＋空ファイルは作らない

物性計算失敗：
get_all() は「5変数中2変数必須」で違反すると ValueError となるため、入力前に必ずチェック。

SVG出力失敗：

Kaleido未導入等 → 依存導入の案内（エラー停止）

11. ロギング仕様

INFO：読み込み件数、有効件数、出力ファイル数、処理時間

WARNING：欠損率が閾値超え、月/季節スキップ、季節定義の月重複

DEBUG：bin/contour等のパラメータ、代表圧力、月別の点数内訳

12. テスト仕様
12.1 単体テスト

EPW欠損値が NaN に置換されること（99.9/999/999999）

季節定義バリデーション（範囲外月、空配列）

グルーピングの点数一致

12.2 結合テスト

サンプルEPWで「月12枚＋季節4枚」が生成されること

各SVGが非ゼロサイズであること

例外時に適切な終了コードを返すこと

13. 今後の拡張（仕様の余白）

期間・時間帯フィルタ（例：業務時間のみ）

複数年EPWの年別比較（同一月を複数レイヤで重ねる）

色バーの出力ON＋凡例の配置テンプレート

SVGに加えてPDF/PNG一括生成（PlotlyはSVG/PDF対応）

仕様確定のためにこちらで“仮置き”した点（実装前の前提）

季節定義のデフォルトは DJF/MAM/JJA/SON としました（運転期ベースの独自定義は seasons_config で対応）。

EPW圧力は「図の一貫性」のため、レコードごとではなく **代表値（中央値）**を PsychrometricChart(pressure=...) に渡す想定にしました（必要なら仕様で「時刻別圧力」モードも追加できます）。
