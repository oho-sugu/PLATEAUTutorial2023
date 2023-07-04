# Topic XX 3D都市モデルと位置情報をUnityで扱う

PLATEAUは他のさまざまな位置情報と組み合わせて使うことで、さらに多くの活用が考えられます。本トピックでは22年度チュートリアルのTopic14の発展として、スマートフォンのGPSによる位置情報など、座標系の違う位置情報をPLATEAUと重ね合わせて表示するARアプリの開発を通して、PLATEAUを他の位置情報と合わせて使う方法について説明します。

## 3D都市モデルを読み込む

最初に、PLATEAU SDK for Unityを使ってPLATEAUの3D都市モデルをUnityに読み込みます。この時、どのような座標系で読み込まれるかなど、重ね合わせるためのポイントを確認します。

### PLATEAU SDK for Unityを使ってデータを読み込む

[PLATEAU SDK for Unity](https://github.com/Project-PLATEAU/PLATEAU-SDK-for-Unity)を使って、PLATEAUの3D都市モデルをUnityに読み込みます。SDKについての詳細は、PLATEAU公式サイトのチュートリアルでも解説されています。詳細はそちらも参照してください。[TOPIC 17｜PLATEAU SDKでの活用[1/2]｜PLATEAU SDK for Unityを活用する](https://www.mlit.go.jp/plateau/learning/tpc17-1/)
また、GitHubのリポジトリのReadmeやマニュアルも参考にしてください。

今回は、Unity 2021.3.16f1を使用して進めていきます。.16f1などのマイナーバージョンはあまり気にしなくてよいと思いますが、PLATEAU SDK for Unityが現在Unityバージョン2021.3を想定しているので、2021.3系列を使用するとよいでしょう。

SDKのマニュアルなどにしたがって、新規プロジェクトを作成しSDKを導入します。

この際、読み込む座標系を確認します。PLATEAU SDK for Unityでは、インポート時に平面直角座標系に変換するようになっています。平面直角座標系は日本固有の投影座標系で、日本全国を19のゾーンに分け、ガウスの等角投影法を適用した座標系です。
そのため、これから作るアプリでは最終的に平面直角座標系に変換することで、PLATEAUの3D都市モデルと合わせていきます。

<!-- 
SDKで読み込む方法の紹介と、その際の座標変換の確認
平面直角座標系
中心点のオフセットの確認と、オフセット値のJGD2011への変換
-->

## さまざまな地理情報を重ねる

次に、座標変換の方法を説明します。実際に座標変換の式をプログラムにして、変換を確認します。また、GPSのデータやオープンデータの変換を行います。

### 座標計算の一般的な注意

緯度経度の座標から、平面直角座標系の座標に変換するプログラムを作成します。変換式は国土地理院が公開しているので、それをプログラムに落とし込みます。
一般的な注意点ですが、地理座標を扱うプログラムでは数値計算の誤差に注意します。とくに、地球規模の座標計算をする場合、たとえば地球の周囲長は約4万㎞なので、メートルで記述すると約40,000,000mとなります。また、コンピューターが扱う浮動小数点規格の標準であるIEEE754を参照すると、一般的にfloatとして知られる32ビットの単精度浮動小数点の形式では実際の数字を現す仮数部が23ビットとなり、10進数でおよそ7桁の数字を表現できます。つまり、地球の周囲長と比べてみると上から数えて10mの位までしか表現できません。地球規模の座標の演算を行う際にfloatを使うと、10m以下の数字は計算されないことになり、大きく精確性が落ちます。
一方で、Unityなどの3Dコンピュータグラフィックスを描画するプログラムは、一般的に高速化のためfloatで座標を表します。
こうした違いのため、座標変換のプログラム内では倍精度浮動小数であるdoubleで計算し、扱いやすい局所的な座標に計算してからfloatにキャストしてUnityなどに渡す、という方法をとるのがよいでしょう。

### 平面直角座標系への変換

平面直角座標系への変換は、ガウス＝クリューゲル変換として知られる計算を行います。国土地理院のWebに、[測量計算サイト](https://vldb.gsi.go.jp/sokuchi/surveycalc/main.html)というページがあり、ここでよく使う計算についてWebページ上で計算できる仕組みが用意されています。また、それぞれの計算式やアルゴリズムが解説されています。

![測量計算サイト](image.png)

ここの計算式を使って、緯度経度から平面直角座標系に変換するプログラムを作成してみましょう。
[平面直角座標への換算](https://vldb.gsi.go.jp/sokuchi/surveycalc/surveycalc/bl2xyf.html)のページの上段に、計算式というリンクがあり、

![平面直角座標への換算](image-1.png)

そこから計算式を確認できます。
![計算式のページ](image-2.png)

今回は、Unityなので、C#でこの計算式をプログラムに落とし込みます。

ここでは、座標変換のクラスは、UnityのMonoBehaviorを継承する必要がないので、素のクラスとして記述します。また、状態を持つ必要がないので、変換メソッドはstaticとして実装します。サンプルでは座標の2つの値を返すのにタプルを使っていますが、ここも必要に応じて設計を変えるとよいでしょう。（ここはどのように使うかを想定して各自で設計を考えてみてください。）

以下が緯度経度と平面直角座標系の変換プログラムのサンプルです。

```csharp:CoordinateUtil.cs
using System;

public class CoordinateUtil
{
    // GRS80 Ellipsoid
    private const double a = 6378137d;
    private const double F = 298.257222101d;

    // 平面直角座標系のX軸上における縮尺係数
    private const double m0 = 0.9999d;

    private const double n = 1d / (2d * F - 1d);

    // Geographic -> Plane Rectangular
    private const double a1 = 1d * n / 2d - 2d * n * n / 3d + 5d * n * n * n / 16d + 41d * n * n * n * n / 180d - 127d * n * n * n * n * n / 288d;
    private const double a2 = 13d * n * n / 48d - 3d * n * n * n / 5d + 557d * n * n * n * n / 1440d + 281d * n * n * n * n * n / 630d;
    private const double a3 = 61d * n * n * n / 240d - 103d * n * n * n * n / 140d + 15061d * n * n * n * n * n / 26880d;
    private const double a4 = 49561d * n * n * n * n / 161280d - 179d * n * n * n * n * n / 168d;
    private const double a5 = 34729d * n * n * n * n * n / 80640d;

    private const double A0 = 1d + n * n / 4d + n * n * n * n / 64d;
    private const double A1 = -3d / 2d * (n - n * n * n / 8d - n * n * n * n * n / 64d);
    private const double A2 = 15d / 16d * (n * n - n * n * n * n / 4d);
    private const double A3 = -35d / 48d * (n * n * n - 5d * n * n * n * n * n / 16d);
    private const double A4 = 315d * n * n * n * n / 512d;
    private const double A5 = -693d * n * n * n * n * n / 1280d;

    // Plane Rectangular -> Geographic
    private const double b1 = n / 2d - 2d * n * n / 3d + 37d * n * n * n / 96d - n * n * n * n / 360d - 81d * n * n * n * n * n / 512d;
    private const double b2 = n * n / 48d + n * n * n / 15d - 437d * n * n * n * n / 1440d + 46d * n * n * n * n * n / 105d;
    private const double b3 = 17d * n * n * n / 480d - 37d * n * n * n * n / 840d - 209d * n * n * n * n * n / 4480d;
    private const double b4 = 4397d * n * n * n * n / 161280 - 11d * n * n * n * n * n / 504d;
    private const double b5 = 4583d * n * n * n * n * n / 161280d;

    private const double d1 = 2d * n - 2d * n * n / 3d - 2d * n * n * n + 116d * n * n * n * n / 45d + 26d * n * n * n * n * n / 45d - 2854d * n * n * n * n * n * n / 675;
    private const double d2 = 7d * n * n / 3d - 8d * n * n * n / 5d - 227d * n * n * n * n / 45d + 2704d * n * n * n * n * n / 315d + 2323d * n * n * n * n * n * n / 945d;
    private const double d3 = 56d * n * n * n / 15d - 136d * n * n * n * n / 35d - 1262d * n * n * n * n * n / 105d + 73814d * n * n * n * n * n * n / 2835d;
    private const double d4 = 4279d * n * n * n * n / 640d - 332d * n * n * n * n * n / 35d - 399572d * n * n * n * n * n * n / 14175d;
    private const double d5 = 4174d * n * n * n * n * n / 315d - 144838d * n * n * n * n * n * n / 6237d;
    private const double d6 = 601676d * n * n * n * n * n * n / 22275d;

    public static (double x, double y) JGD2011ToPlaneRectCoord(double lat, double lon, double o_lat, double o_lon)
    {
        double latr = lat * Math.PI / 180d; // TO Radian
        double lonr = lon * Math.PI / 180d;
        double o_latr = o_lat * Math.PI / 180d;
        double o_lonr = o_lon * Math.PI / 180d;

        double t = Math.Sinh(Math.Atanh(Math.Sin(latr))
            - 2d * Math.Sqrt(n) / (1d + n) * Math.Atanh(2d * Math.Sqrt(n) / (1d + n) * Math.Sin(latr)));
        double _t = Math.Sqrt(1d + t * t);

        double Lc = Math.Cos(lonr - o_lonr);
        double Ls = Math.Sin(lonr - o_lonr);

        double Xi_ = Math.Atan(t / Lc);
        double Eta_ = Math.Atanh(Ls / _t);

        double _S = m0 * a / (1d + n) * (A0 * o_latr +
            A1 * Math.Sin(2d * o_latr) +
            A2 * Math.Sin(2d * 2d * o_latr) +
            A3 * Math.Sin(2d * 3d * o_latr) +
            A4 * Math.Sin(2d * 4d * o_latr) +
            A5 * Math.Sin(2d * 5d * o_latr));

        double _A = m0 * a / (1d + n) * A0;

        double x = _A * (Xi_ +
            a1 * Math.Sin(2d * 1d * Xi_) * Math.Cosh(2d * 1d * Eta_) +
            a2 * Math.Sin(2d * 2d * Xi_) * Math.Cosh(2d * 2d * Eta_) +
            a3 * Math.Sin(2d * 3d * Xi_) * Math.Cosh(2d * 3d * Eta_) +
            a4 * Math.Sin(2d * 4d * Xi_) * Math.Cosh(2d * 4d * Eta_) +
            a5 * Math.Sin(2d * 5d * Xi_) * Math.Cosh(2d * 5d * Eta_)) - _S;
        double y = _A * (Eta_ +
            a1 * Math.Cos(2d * 1d * Xi_) * Math.Sinh(2d * 1d * Eta_) +
            a2 * Math.Cos(2d * 2d * Xi_) * Math.Sinh(2d * 2d * Eta_) +
            a3 * Math.Cos(2d * 3d * Xi_) * Math.Sinh(2d * 3d * Eta_) +
            a4 * Math.Cos(2d * 4d * Xi_) * Math.Sinh(2d * 4d * Eta_) +
            a5 * Math.Cos(2d * 5d * Xi_) * Math.Sinh(2d * 5d * Eta_));

        return (x, y);
    }

    public static (double lat, double lon) PlaneRectCoordToJGD2011(double x, double y, double o_lat, double o_lon)
    {
        double o_latr = o_lat * Math.PI / 180d;
        double o_lonr = o_lon * Math.PI / 180d;

        double _S = m0 * a / (1d + n) * (A0 * o_latr +
            A1 * Math.Sin(2d * o_latr) +
            A2 * Math.Sin(2d * 2d * o_latr) +
            A3 * Math.Sin(2d * 3d * o_latr) +
            A4 * Math.Sin(2d * 4d * o_latr) +
            A5 * Math.Sin(2d * 5d * o_latr));

        double _A = m0 * a / (1d + n) * A0;

        double Xi = (x + _S) / _A;
        double Eta = y / _A;

        double Xi_ = Xi - (
            b1 * Math.Sin(2d * Xi) * Math.Cosh(2d * Eta) +
            b2 * Math.Sin(2d * 2d * Xi) * Math.Cosh(2d * 2d * Eta) +
            b3 * Math.Sin(2d * 3d * Xi) * Math.Cosh(2d * 3d * Eta) +
            b4 * Math.Sin(2d * 4d * Xi) * Math.Cosh(2d * 4d * Eta) +
            b5 * Math.Sin(2d * 5d * Xi) * Math.Cosh(2d * 5d * Eta));
        double Eta_ = Eta - (
            b1 * Math.Cos(2d * Xi) * Math.Sinh(2d * Eta) +
            b2 * Math.Cos(2d * 2d * Xi) * Math.Sinh(2d * 2d * Eta) +
            b3 * Math.Cos(2d * 3d * Xi) * Math.Sinh(2d * 3d * Eta) +
            b4 * Math.Cos(2d * 4d * Xi) * Math.Sinh(2d * 4d * Eta) +
            b5 * Math.Cos(2d * 5d * Xi) * Math.Sinh(2d * 5d * Eta));

        double Kai = Math.Asin(Math.Sin(Xi_) / Math.Cosh(Eta_));

        double lat = 180d / Math.PI * (Kai + (
            d1 * Math.Sin(2d * Kai) +
            d2 * Math.Sin(2d * 2d * Kai) +
            d3 * Math.Sin(2d * 3d * Kai) +
            d4 * Math.Sin(2d * 4d * Kai) +
            d5 * Math.Sin(2d * 5d * Kai) +
            d6 * Math.Sin(2d * 6d * Kai)
            ));
        double lon = o_lon + 180d / Math.PI * Math.Atan2(
            Math.Sinh(Eta_), Math.Cos(Xi_));

        return (lat, lon);
    }
}
```

次に、この変換プログラムを使って緯度経度を持った点をPLATEAUの3D都市モデルと重ねて表示してみましょう。

<!--
国土地理院の変換式を使って計算するルーチン
相互変換のルーチンを作っておく
-->

### 位置情報の読み込み

まず初めに、座標を羅列したCSVファイルを読み込み、その場所にオブジェクトを置いてみます。
CSVファイルはカンマでデータを区切ったテキストファイルです。テキストエディタで作成でき、扱いが容易なのでデータの保存形式としてよく使われます。
ここでは、緯度,経度,高さのように3つの数値を羅列したファイルを以下のように作ります。

```csv:place.csv
35.729550,139.730014,20.8
35.730756,139.725266,31.8
35.730020,139.727659,24.2
35.730020,139.723019,30.8
```

手作業で場所のデータを作成するときは、国土地理院の公開している[地理院地図](https://maps.gsi.go.jp/)が便利です。地図中心の地理座標や標高などを調べることができます。

![地理院地図の画面](image-3.png)

次に、用意したCSVファイルを読み込み、Prefabを配置するC#スクリプトを書きます。

```csharp:ReadCSV.cs
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ReadCSV : MonoBehaviour
{
    public TextAsset csv;
    public GameObject go;

    // Start is called before the first frame update
    void Start()
    {
        var lines = csv.text.Split("\n");
        foreach (var line in lines)
        {
            if (line.Contains(","))
            {
                var tokens = line.Split(",");
                double lat = double.Parse(tokens[0]);
                double lon = double.Parse(tokens[1]);
                double height = double.Parse(tokens[2]);

                (var x,var y) = CoordinateUtil.JGD2011ToPlaneRectCoord(lat, lon, 36d, 139.83333333333d);

                x = x + 29787.4390;
                y = y + 9810.3435;

                Instantiate(go, new Vector3((float)y, (float)height, (float)x), Quaternion.identity);

            }
        }
    }

}
```

CSVファイルは`TextAsset`として読み込むようにしましたが、FileStreamなどで読み込んでもよいでしょう。CSVファイルのパースは便利なライブラリなどもありますが、今回は簡単な読み込みロジックを書きました。
座標変換には、作成した変換クラスを使っています。平面直角座標系の原点は9系の値を設定しています。
また、Unity SDK for PLATEAUで読み込む際に計算したオフセットの値を引き算しています。
平面直角座標では、Xが南北方向、Yが東西方向を表すので、そこも注意しましょう。

実行すると図のように、PLATEAUの3D都市モデルと合わせて指定した位置にオブジェクトを配置します。

![実行画面](image-4.png)

<!-- CSVから読み込みのサンプルコード作る -->

### スマホのGPS情報を重ねる

スマートフォンのGPS情報を取得して、その位置にオブジェクトを置いてみましょう。

端末のGPSの座標をUnityで取得するには、`Input.Location`を使うことができますが、これまでの歴史的経緯のために、緯度経度の座標値がfloatの単精度浮動小数で返ってきます。これでは精度として足りないので、AssetsStoreに公開されている[`NaitiveToolkit`](https://assetstore.unity.com/packages/tools/integration/native-toolkit-132452?locale=ja-JP)を使います。`NativeToolkit`は、iOSとAndroidのモバイル端末向けの複数の機能をまとめたネイティブライブラリです。

AssetStoreから導入

ボタンを押したらその位置にオブジェクトを置くコード

<!-- その場のGPS座標もとって、データを追加できるようにする
（NaitiveToolkit使ってDoubleで座標とるのの説明
GPS座標などの緯度経度の情報をPLATEAUで扱う
-->

### GPS受信機のデータを重ねる

NMEAのファイルをパースするコード
LineRendererでルートを表示

Neo-Z9pあたりのデータを取得する
NMEA
WGS84と平面直角座標の変換
RTK-GNSSの説明もしたらいいか

### オープンデータを重ねる



オープンデータを扱う
地理情報データの探し方・作り方
オープンデータの取得
前章での座標変換に合わせる形で、座標を変換する方法を解説

### その他の座標変換

WGS84とJGD2011の変換　PROJの説明する？
WGS84とECEF/ENUの変換
ジオイド高・標高・楕円体高、計算の方法

コラム：旧日本測地系について

## ARアプリの開発

最後に、実際のARアプリにまとめます。ここでは、あらかじめアプリに内蔵した位置情報をAR表示する機能、新しい位置情報を端末のGPSから記録してAR表示する機能、3D都市モデルを表示する機能を持ったARアプリを作成します。

### 座標の保存

PlayerPrefsに保存する仕組みを作る
座標保存の方法　Doubleにすることなど

### PLATEAUモデルの調整

半透明オクルージョン

### 表示の工夫

PLATEAUに隠れたらステンシルで色変える
https://nn-hokuson.hatenablog.com/entry/2017/05/02/185320

### GeospatialAPI・ARFoundationの設定

ドキュメントを提示しながら設定手順解説

### ピンの配置

POIのピンがARで現実の風景に重畳されるようなアプリを想定
Geospatial Anchorで配置する
平面直角座標でのオフセットで子要素として配置する

### アプリ完成

スマホGPSのポイントがPlayerPrefsに保存される
あらかじめアプリ内に入れた複数のCSVがそれぞれのピンで表示される

