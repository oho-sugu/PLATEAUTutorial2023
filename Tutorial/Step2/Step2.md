# Topic XX 3D都市モデルを使った位置情報共有ゲームを作る

近年位置情報を基盤としたサービスが多く使われています。Google MapsやUberなどはその典型でしょう。
自分の位置情報をスマートフォン端末のGPSで取得し、サービスのサーバーに送信することで、さまざまな便利なサービスを受けることができます。
本トピックでは、このような位置情報をオンラインでやり取りしたり、サーバーで処理してサービスを提供するなどの参考になるように、例としてPLATEAUの3D都市モデルを活用した位置情報ゲームを作りながら説明します。

## まずは基本のゲームを作る

本トピックではUnityでスマートフォンAR位置情報ゲームを作ります。
ゲームを起動すると、プレイヤーは最初に赤緑青の三色から選び自分が属する陣営を決めます。
AR画面になると、端末カメラが映す実際の街並みが表示されます。
PLATEAUの3D都市モデルを使い、タップするとその場所の建物に「ペンキ」が塗られ、町中の色々なところを塗って最初の点までつないで閉じると、
そこが自陣営の陣地になります。ゲームは獲得した陣地の面積を競います。

サーバーサイドにはPostGIS拡張をインストールしたPostgreSQLデータベースを使います。
面積は、ゲームプレイ時はとった陣地の合計をサーバーで計算しますが、
ゲーム終了後にバッチ処理で重ね合わせを考慮した結果の面積を計算する仕様にします。
これは、時間順に重ね合わせて面積を計算する処理が、リアルタイムに計算にするには重いためです。

### ARの設定をする

最初にプロジェクトを作成し、基本のAR部分を設定します。
本プロジェクトでは、iOS・Androidを対象として、ARFoundationおよびARCoreExtentionでGeospatial APIを使います。

まずはUnityで新規プロジェクトを作成します。
今回は、Unity 2022.3.7f1を使います。

ARの設定は、PLATEAU公式サイトのチュートリアルコンテンツの[TOPIC14-3　「Google Geospatial APIで位置情報による3D都市モデルのARを作成する」](https://www.mlit.go.jp/plateau/learning/tpc14-3/)も参考にしてください。
また、UnityでのAR開発の[公式ドキュメント](https://docs.unity3d.com/ja/2022.3/Manual/AROverview.html)や、ARFoundationの[公式ドキュメント](https://docs.unity3d.com/Packages/com.unity.xr.arfoundation@5.0/manual/index.html)なども必要に応じて参照してください。
ここでは、最低限の説明をします。

まず、Unity Hubからプロジェクトを新規作成します。今回は、「3D(URP)」を選択します。必要に応じてダウンロードボタンを押してテンプレートをダウンロードしてください。
プロジェクト名を「PlacePLATEAU」にします。PLATEAUを使った陣取りゲームからの命名です。

![Unity Hub プロジェクト新規作成画面](image-1.png)

プロジェクトが立ち上がったら、ARFoundationとGepspatialAPIを導入します。

［Window］メニューから［Package Manager］を開きます。

Package Managerが開いたら、「Unity Registry」を選択し、「ARFoundation」をインストールします。何らかのダイアログが開いたら適切に対処します。「New Input System」の有効化が必要であればダイアログの指示にしたがい、再起動などをおこないます。

![Unity Package ManagerでARFoundationのインストール](image.png)

同様にして、「Apple ARKit XR Plugin」、「Google ARCore XR Plugin」をインストールします。

この段階で必要に応じてインストール済みのパッケージのアップデートも行っておくとよいでしょう。

次に、「ARCore Extentions for ARFoundation」をインストールします。このパッケージにGeospatialAPIの機能が含まれます。なお、ARCore Extentionsの[ドキュメント](https://developers.google.com/ar/develop/unity-arf/getting-started-extensions?hl=ja)と、GeospatialAPIの[ドキュメント](https://developers.google.com/ar/develop/geospatial?hl=ja)も参考にしてください。
Package Managerの左上の［＋］をクリックし、［Add package from git URL］を選択します。そして次のURLを貼り付け、［Add］をクリックします。

```
https://github.com/google-ar/arcore-unity-extensions.git
```

![ARCore Extentionsのインストール](image-2.png)

ARCore Extensionsの画面が表示されたら、［Samples］の項目にある［Geospatial Sample］の［Import］をクリックして、このサンプルもインポートしておいてください。

![Geospatial SampleもImportしておく](image-3.png)

さらに、Unity Editorの［Edit］メニューから［Project Settings］を開き、いくつかの設定を加えます。

![Android ARCore有効](image-4.png)

![iOS　ARKit有効](image-5.png)

「XR Plug-in Management」の「Project Validation」では、プロジェクトの設定を自動的にARに最適な形に修正してくれます。もし、ここでエラーなどが出ていたら、「Fix All」ボタンを押して修正します。

![Project Validation](image-6.png)

GeospatialAPIのAPIキーはGoogle Cloudのコンソールで作成し、「XR Plug-in Management」の「ARCore Extentions」で設定してください。詳細な手順は[公式ドキュメント](https://developers.google.com/ar/develop/geospatial?hl=ja)や、PLATEAU公式サイトのチュートリアルコンテンツの[TOPIC14-3　「Google Geospatial APIで位置情報による3D都市モデルのARを作成する」](https://www.mlit.go.jp/plateau/learning/tpc14-3/)の「■ APIキーの作成」の項目を参照してください。
また、「iOS Support Enabled」「Geospatial」のチェックもつけておきます。

![GeospatialAPIの設定](image-7.png)

```
※※※　注意　※※※

ここではAPIキーを設定していますが、秘密情報をアプリに組み込むことになるためセキュリティ的には推奨されません。
後半のアプリをビルドする際により適切な方法の説明をします。
APIキーのままでアプリを公開しないように気を付けてください。
```

次に、Unity Editorの「Project」ビューにうつり、「Assets/Samples/ARCore Extentions/1.38.0/Geospatial Samples/Configurations/GeospatialConfig」をクリックします。「Inspector」ビューの「Geospatial」を「Enabled」にします。
![Geospatial Config](image-8.png)

Playerタブで、Android,iOSの各プラットフォームを以下のように設定します。

【Androidの場合】

- Minimum API Levelは、28以上が妥当です。
- IL2CPPでビルドします。
- Graphics APIは、OpenGL ES3以上が必要です。（Vulkanは外しておいた方が無難です）
- Target ArchitectureのARMv7のチェックを外す

【iOSの場合】

- サポートするOSは、iOS11以上です。
- ARM64でビルドします。
- 「Require ARKit Support」にチェックを入れます。
- 「Location Usage Description」に、位置情報を使う際にユーザーに通知するメッセージの文字列を入れます。

URPの設定で、Renderer FeaturesにAR Background Renderer Featureが設定されていない場合、追加します。使用するURP設定が分からなければ、すべての設定に追加します。

![AR Background Renderer Feature](image-9.png)

ここまでの設定で、Geospatial APIを使ったARアプリの基本の設定が終わりました。一度各プラットフォーム向けに「Geospatial Samples」の「Gepspatial」シーンをビルド対象にして動作確認のためにビルドしておくとよいでしょう。

### PLATEAUを読み込む

「PLATEAU SDK for Unity」をインストールし、ゲーム対象地域の3D都市モデルを読み込みます。
詳細は、公式の[ドキュメント](https://project-plateau.github.io/PLATEAU-SDK-for-Unity/index.html)や、PLATEAU公式サイトのチュートリアルコンテンツの[TOPIC 17｜PLATEAU SDKでの活用[1/2]｜PLATEAU SDK for Unityを活用する](https://www.mlit.go.jp/plateau/learning/tpc17-1/)なども参考にしてください。

ここでは、GitHubからtarボールでインストールします。
「PLATEAU SDK for Unity」のリリースページからtgzファイルをダウンロードします。

Unity Package Managerを開き、左上の＋ボタンから「Add Package from tarball...」を選択し、ダウンロードしたtgzファイルを指定してインストールします。

![PLATEAU SDK for Unityのインストール](image-10.png)

インストールが正常に行われると、Unity Editorのメニューに「PLATEAU」の項目が増えています。
早速3D都市モデルを読み込んでみます。

まず、作業用のシーンを用意します。`Assets/Samples/ARCore Extensions/1.38.0/Geospatial Samples/Scenes/Geospatial`シーンを開きます。「ヒエラルキー」のシーン名の右からメニューを開くと、シーンを別名で保存する選択肢があるので、`Assets/Scenes`などに保存します。（Geospatial Samplesのサンプルシーンをコピーして作業用のシーンとしています。）

![Geospatialシーンを開き、別名で保存する](image-14.png)

作業用シーンが準備できたら、「PLATEAU」メニューから「PLATEAU SDK」を選択し、SDKのダイアログを表示します。
インポートの画面で、ローカルの方であらかじめダウンロードしておいた使いたい地域のPLATEAUの3D都市モデルを展開したフォルダーを選択するか、サーバーの方で使いたい地域を選択します。

![ローカルで使用する3D都市モデルデータを指定したところ](image-11.png)

続いて範囲選択を行います。範囲選択ボタンを押すとEditor画面の方で選択UIが起動するので、必要な範囲を指定します。ここでは、あまり広い範囲を指定してしまうと処理負荷がかかるので、気を付けてください。

![範囲選択しているところ](image-12.png)

次に地物別設定をします。今回は、建築物のLOD1のみを「地域単位」で結合してインポートします。
建築物以外の「インポートする」のチェックを外します。
また、テクスチャは必要ないので「テクスチャを含める」のチェックは外します。
これで「モデルをインポート」を押し、処理を開始します。範囲やPCの性能にもよりますが、数分の時間がかかる場合もあります。

![地物別設定をしているところ](image-13.png)

最後に、3D都市モデルがシーンに読み込まれたことを確認します。

![3D都市モデルがシーンに読み込まれたところ。](image-15.png)

### Paint in 3Dを導入し、PLATEAUに印を塗れるようにする

ここまでがゲーム開発の基本となる準備となります。ここからPLATEAUを使ったゲームロジックを実装します。
最初に、ARでPLATEAUの3D都市モデルに弾を発射すると、ビルに印が塗られる仕組みを作ってみます。Unity Asset Storeで[「Paint in 3D」](https://assetstore.unity.com/packages/tools/painting/paint-in-3d-26286?locale=ja-JP)というアセットを購入($66)し使用します。
このアセットは、3Dのオブジェクトにお絵描きができるものです。購入したら通常のアセットの導入と同様にUnity Package Managerから導入してください。

![Paint in 3DのAsset Storeページ](image-16.png)

```
※※※　ヒント　※※※
ここでは、有料アセットを使用しましたが、例えばコライダーとレイキャストの機能を使って、タップ位置からの当たり判定を計算し、そこにオブジェクトを表示するなどでも近いことはできると思います。
興味のある人はチャレンジしてみてください。
```

さて、読み込んだままのPLATEAUの3D都市モデルだと、Paint in 3Dで使うためには不便です。
Paint in 3Dは、設定したテクスチャ画像に描画することで3Dモデルに描画しているように見せる仕組みです。
そのため、広範囲の3Dモデルを結合した巨大なモデルを対象とした場合、テクスチャの解像度が足りずジャギーが発生したりモザイクのようになってしまいます。一方で、3Dモデルを細かく分割しそれぞれに高解像度のテクスチャを貼ると、描画が非常に高負荷になってしまいます。

![テクスチャ解像度が足らずモザイク様になったところ](image-17.png)

ここでは、読み込んだPLATEAUの3Dモデルを9分割して[「Mesh Combiner」](https://assetstore.unity.com/packages/tools/modeling/mesh-combiner-157192)というアセットで結合することで、テクスチャの品質と描画負荷のバランスのよい設定にします。

Mesh CombinerはAsset Storeで入手し、プロジェクトにインストールしておきます。

最初に、Editor上で読み込んだ3D都市モデルをマウスで選択しながらまとめるための空のGameObjectの子にしていき、縦横それぞれ3分割した9つのGameObjectに分けた階層構造にします。

![読み込んだ3D都市モデルを9つにまとめたところ](image-19.png)

`Assets/MeshCombiner/Scripts/MeshCombiner.cs`を、9分割したそれぞれのGameObjectにD&Dでアタッチします。
「Deactivate Combined Children」と「Generate UV Map」にチェックを入れて、「Combine Meshes」を押すと。メッシュが結合されます。正しく結合されていることが分かったら、子オブジェクトは消してしまっても問題ありません。

![Mesh Combinerでメッシュを結合する](image-21.png)

Paint in 3Dは、モデルのUV座標に基づいて、テクスチャのどこにペイントするかを判定します。そのため、モデルに正しくUV座標が設定されていないとおかしな描画になってしまいます。Mesh CombinerでUVは自動的に生成されていますが、現状のMesh Combinerで結合したメッシュだと、UV座標がUV1に入っています。これをPaint in 3Dの機能を使って、UV0にコピーします。

一度FBXに変換するために、「FBX Exporter」をUnity Package Managerからインストールしておきます。Hierarchyのモデルを選択して右クリックし「Export to FBX...」を選択します。

![FBXでExport](image-27.png)

図のように設定して「Export」を押します。

![FBX Exportの設定](image-28.png)

指定したフォルダにFBXとして書き出され、プロジェクトの方に表示されます。
ここで、FBXの階層を開いてMeshのInspectorを表示し、右側のメニューを開くと、「Coord Copier(Paint in 3D)」があるのでこれを選択します。

![Coord Copierを開く](image-29.png)

図のような設定で「Generate」ボタンを押します。

![Coord Copier設定](image-30.png)

すると、UV1の内容をUV0にコピーしたメッシュが新しく作成されます。

![Coord Copierによって作成された新しいメッシュ](image-31.png)

これを、元のメッシュの代わりに3D都市モデルのMesh FilterのMeshに設定します。

![新しいメッシュの設定](image-32.png)

これで、Paint in 3D用に変換されたメッシュの準備ができました。

さらに、ペイントの衝突判定用にMesh Colliderを追加します。

![Mesh Colliderの追加](image-26.png)

次に、Paint in 3Dで建物をペイントできるように設定します。
結合したメッシュを選択し、InspectorのMesh Rendererの右肩のメニューボタンからメニューを開き、「Make Paintable(Paint in 3D)」を選択します。これで、Paint in 3Dのペイント対象になります。

![メニューからMake Paintableを選択](image-23.png)

P3D Paintableコンポーネントのボタンで、「Add Material Cloner」と「Add Paintable Texture」を押下し、それぞれのコンポーネントも追加しておきます。

![P3D Paintable、P3D Material Cloner、P3D Paintable Textureを追加](image-24.png)

P3D Paintable Textureの設定を図のように変更します。Sizeを2048x2048に、ColorをR:0,G:0,B:0,A:0にしています。これでAR表示したときに、塗られていないところは完全な透過となります。

![P3D Paintable Textureの設定変更](image-33.png)

Paint in 3Dは、モデルのテクスチャにペイントした結果を描画しますが、表示のための専用のペイント用のマテリアルを作ります。（Paint in 3Dが自動的に実行時にコピーしてくれるので、このマテリアルは一つ作成してすべての3D都市モデルで共有することができます。）
適当なフォルダーにマテリアルを新規に作り、シェーダーを「Paint in 3D/Overlay」にします。

![マテリアルの設定](image-25.png)

このマテリアルを建物モデルに適用します。

なお、P3D Paintableの「Analyze Mesh」ボタンを押すと、現在のメッシュのUV座標を確認できます。
図のように、CoordにUV0を指定した状態で、矩形が多く並んだような状態になっていれば、ここまでの手順で正しく変換されていると考えられます。

![Analyze Mesh](image-34.png)

以上のモデルの設定を分割した全てのモデルに対して行います。

```
このように、ゲームエンジンでPLATEAUの3D都市モデルを表示する以上の活用をしようとすると、ゲームエンジンの様々な機能の活用やその仕組みの理解が必要になります。
また適切に3D都市モデルのデータを変換や調整していくことも必要になります。
幸いにも、UnityやUnreal Engineでは、公式非公式問わず様々な入門コンテンツやサンプルが充実しています。一歩進んだ応用を目指して活用してみましょう。
```

最後に、Paint in 3Dの描画を制御するコンポーネントを追加します。
Hierarchyで、空のゲームオブジェクトを一つ追加し、「P3D Hit Screen」コンポーネントと「P3D Paint Sphere」コンポーネントを追加します。それぞれのコンポーネントは図のように設定してください。

![ペイントの管理オブジェクトの設定](image-36.png)

さらに、「P3D Pointer Mouse」と「P3D Pointer Touch」を追加します。これらはデフォルトの設定で構いません。

![MouseとTouchの有効化](image-37.png)

ここまでで、建物をペイントする仕組みができました。

```
PLATEAUの3D都市モデルは巨大なので、どうしてもテクスチャの解像度を上げるのが難しい場合があります。
そこで、ドット絵風など表現を工夫することも考えられます。
その際には、「P3D Paintable Texture」の「Advanced/Filter」の設定を「Point」に変えるとドット絵がくっきり見えるようになります。
```

Editor上で実行すると、マウスでクリックすると3D都市モデルにペイントできるようになっています。

![実行例](image-38.png)

### 塗った場所の位置座標を計算する

GeospatialでWorld座標から緯度経度にする

## サーバーに位置情報を送る

位置情報を送る先のサーバーを作ります。
機能としては、HTTPでJSONにした位置情報をクライアントとやり取りするシンプルなAPIサーバーです。
サーバーでは位置情報を受信すると、それをPostGISの空間情報データとしてデータベースに格納し、
空間クエリで面積を計算してクライアントに結果を返します。

サーバーにはさまざまな技術がありますが、
ここではフレームワークにはPythonのFlaskを使い、PostgreSQL+PostGISをバックエンドデータベースとして使います。
また、動作させるインフラとして、AWSを使うこととします。

これらの構成はあくまでもこのサンプルでの説明用で、同じようなことをやる場合のさまざまな選択肢があります。
今回はなるべく汎用的かつ基本的で、読者が自分の環境に読み替えて考えやすい作り方を目指しました。
言語もフレームワークもクラウドもデータベースも多くの選択肢があるので、自分の慣れているものに読み替えてください。

また、HTTPでやり取りするAPIは、リアルタイムでの同期には向いていません。
FirebaseなどのMBaaSや、Photonなどのリアルタイム通信基盤など、まったく別の考え方の選択肢もあります。
ここでは詳細を説明しませんが、作りたいサービスに合わせて選択してください。

### サーバーの準備

AWSでEC2インスタンスを立ち上げます。AWSを使うにはアカウントの登録が必要です。今回は無料枠の範囲内でできるように構成していますが、設定のミスなどで予想外の金額が請求されることもあります。アカウントの2段階認証を設定するなど、セキュリティにも十分気を付けてください。
また、本項はある程度AWSを使い慣れている前提で進めます。分からないことがある場合はAWSのドキュメントなどを参照してください。

また、内容の中にセキュリティの側面などで本番環境で動作させるには適さない部分があります。本項のアプリはあくまでも解説用のサンプルということで、実際のサービスなどを構築していく際には十分考慮してください。

EC2インスタンスはいわゆるクラウドの仮想マシンです。クラウドの使い方としては旧式なものですが、なるべく基本的なところから説明して分かりやすくという方向で説明します。サーバーレスなど最近のモダンな構成を試したい方は是非チャレンジしてみてください。

OSは、著者が使い慣れていることもあり、Ubuntu 22.04を使います。インスタンスタイプは現時点ではt3a.nanoが単価が安いのでこちらを使っていきます。（※注：無料枠の範囲でやりたい人は`t2.micro`を選択してください）
キーペアなどは適切に設定してください。セキュリティグループは、SSHとHTTPSが通るように設定してください。テスト用にHTTPが通ってもよいと思いますが、スマホアプリからのアクセスではHTTPSが必須である場合が大半なので基本はHTTPSを使います。（※注：本番環境ではHTTPは外にさらさない方がいいと思います。）

![EC2インスタンスの起動](image-22.png)

SSHで接続し環境構築します。最初に、PostgreSQLとその地理空間拡張のPostGISをインストールします。ついでにシステムのアップデートも一緒にしておきましょう。

```
$ sudo apt update
$ sudo apt upgrade
$ sudo apt install postgresql postgis
```

まずログインできるようにパスワードを設定します。

```
$ sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'password';"
```

このままだと、PostgreSQLのPeer認証になっているので、postgresユーザーしかアクセスできません。この後の作業に不便なので、Peer認証を変更します。以下のコマンドでPostgreSQLの設定ファイルを開きます。
（エディターはvimでもEmacsでもお好みのものを使ってください。例ではnanoを使います。）

```
$ sudo nano /etc/postgresql/14/main/pg_hba.conf
```

この行を

```
# Database administrative login by Unix domain socket
local   all             postgres                                peer
```

このように変えて保存します。

```
# Database administrative login by Unix domain socket
local   all             postgres                                scram-sha-256
```

PostgreSQLのサービスを再起動します。

```
$ sudo service postgresql restart
```

次のように`psql`コマンドを`ubuntu`ユーザーで実行し、さきほど設定したパスワードでPostgreSQLのプロンプトに入れたら準備完了です。
（※注：本来はデータベース操作用の権限を絞ったユーザーを作成しますが、簡単のためこのような設定で進めます。）

```
$ psql -U postgres
Password for user postgres:
psql (14.9 (Ubuntu 14.9-0ubuntu0.22.04.1))
Type "help" for help.

postgres=#
```

### データベースの準備

次にデータベースを作成します。データベースの名前は、`placeplateau`にします。
PostgreSQLの詳しい使い方は公式ドキュメントなどを参考にしてください。

```
postgres=# create database placeplateau;
postgres=# \c placeplateau
```

PostGISを有効にします。

```
placeplateau=# CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;
```

アプリ用のテーブルを作ります。

```
placeplateau=# create table placedata (
  id SERIAL PRIMARY KEY,
  userid VARCHAR(255) NOT NULL,
  side INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  geom GEOMETRY(POLYGON,4326) NOT NULL);
```

### Webアプリケーションプログラムの作成

Python3とその周辺環境をインストールします。uwsgi経由でnginxをWebサーバーに使います。

```
$ sudo apt install python3 python3-pip python3-venv nginx
```

Pythonのvenvを設定しFlaskと必要なライブラリをインストールします。
作業用のディレクトリは、自分のホーム直下の`placeplateau_web`とします。

```
$ sudo apt install libpq-dev
$ mkdir placeplateau_web
$ cd placeplateau_web/
$ pwd
/home/ubuntu/placeplateau_web
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install Flask uwsgi geoalchemy2 flask_sqlalchemy psycopg2 geoalchemy2[shapely] pyjwt cryptography
```

次のPythonプログラムをエディタなどで作成します。

``` app.py
from flask import Flask,request
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from datetime import datetime,date,timedelta
from sqlalchemy.sql import func, and_
import json
import jwt
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/placeplateau'
db = SQLAlchemy(app)

# テーブルのスキーマ定義
class PlaceData(db.Model):
    __tablename__ = 'placedata'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.String)
    side = db.Column(db.Integer)
    created_at = db.Column(db.Time)
    geom = db.Column(Geometry('POLYGON'))

    def getdict(self):
        return {"id":self.id,
                "userid":self.userid,
                "side":self.side,
                "created_at":str(self.created_at),
                "geom":to_shape(self.geom).wkt}

# 動作確認　テスト用
@app.route('/')
def hello():
    return 'PlacePLATEAU API SERVER'

# 当日のデータ取得
@app.route('/getarea')
def getArea():
    today = date.today()
    placedatas = db.session.query(PlaceData).where(PlaceData.created_at >= func.date(func.now())).order_by(PlaceData.id)
    datas = []
    for placedata in placedatas:
        print(placedata.id)
        datas.append(placedata.getdict())
    return json.dumps(datas)

# 新しい領域の作成と未読データの取得
@app.route('/makearea', methods=['POST'])
def makeArea():
    data = request.json

    lastid=data['lastid']
    userid=data['userid']
    side=data['side']
    newareaWKT=data['newarea']

    newarea = PlaceData(userid=userid, created_at=func.now(),side=side, geom=newareaWKT)
    db.session.add(newarea)
    db.session.commit()

    placedatas = db.session.query(PlaceData).filter(and_(PlaceData.created_at >= func.date(func.now()),PlaceData.id >= lastid)).order_by(PlaceData.id)
    datas = []
    for placedata in placedatas:
        print(placedata.id)
        datas.append(placedata.getdict())
    return json.dumps(datas)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
```

PostgreSQLにデータを記録しているところを説明します。
WebフレームワークはFlaskを使用しています。FlaskはPythonの軽量なWebフレームワークで、例のように各URLに対する処理をメソッドとして記述することでWebサーバーとして動作します。

ORMとして、[SQLAlchemy](https://www.sqlalchemy.org)に[GeoAlchemy](https://geoalchemy-2.readthedocs.io/en/latest/)という地理情報拡張を組み合わせて使っています。

スキーマ定義で、Geometry型を使うことで、PostGISの地理情報型を利用できます。

```
# テーブルのスキーマ定義
class PlaceData(db.Model):
    __tablename__ = 'placedata'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.String)
    side = db.Column(db.Integer)
    created_at = db.Column(db.Time)
    geom = db.Column(Geometry('POLYGON'))
```

新規の領域を作る(SQLのInsertを発行する)際は、WKT(Well Known Text)形式でジオメトリーのデータを渡します。

```
    newarea = PlaceData(userid=userid, created_at=func.now(),side=side, geom=newareaWKT)
    db.session.add(newarea)
    db.session.commit()
```

ここでは使っていませんが、空間検索なども実行できます。
GeoAlchemyの[公式ドキュメント](https://geoalchemy-2.readthedocs.io/en/latest/index.html)などを参照してください。

最後に動作確認をします。app.pyを保存したディレクトリで、以下のコマンドを実行します。

```
$ python app.py
```

開発サーバーですよという警告が出ますが、IPアドレスとポートが表示され動作します。
curlで動作確認をします。以下コマンドで、動作確認用のメッセージが出力されます。

```
$ curl http://127.0.0.1:5000/
```

また、以下のコマンドで、データベースに新しいエリアが作成され、既存のエリアのリストがJSONで返ってきます。

```
$ curl -X POST -H "Content-Type: application/json" -d '{"lastid":"0","userid":"12345","side":"0","newarea":"POLYGON((1 0,3 0,3 2,1 2,1 0))"}' http://127.0.0.1:5000/makearea
```

### Webサーバーの公開

ここまでは、AWS上の仮想マシンで外からのアクセスがされない状態でのテストでした。次に、nginxを設定して外部に公開する設定をします。

uwsgi用の設定ファイルを作成します。app.pyと同じ場所にapp.iniというファイル名で以下のファイルを作成します。

```app.ini
[uwsgi]
module = app
callable = app
master = true
processes = 1
socket = /tmp/uwsgi.sock
chmod-socket = 666
vacuum = true
die-on-term = true
wsgi-file = /home/ubuntu/placeplateau_web/app.py
logto = /home/ubuntu/placeplateau_web/app.log
```

nginxの設定ファイルを修正します。以下のコマンドでroot権限で設定ファイルを開き編集します。

```
$ sudo nano /etc/nginx/nginx.conf
```

httpのセクションに以下の二行があるので、sites-enabledの方をコメントアウトします。

```
        include /etc/nginx/conf.d/*.conf;
        #include /etc/nginx/sites-enabled/*;
```

nginxのconf.d以下にuwsgi.confを作成します。

```
$ sudo nano /etc/nginx/conf.d/uwsgi.conf
```

uwsgi.confに以下の内容を記載します。

```uwsgi.conf
server {
    listen    80;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:///tmp/uwsgi.sock;
    }
}
```

ここまでできたら、nginxを再起動します。

```
$ sudo service nginx restart
```

以下のコマンドでuwsgiを起動して、外部からアクセスして確認します。

```
$ uwsgi --ini app.ini
```

EC2のインスタンスの情報から、パブリックIPv4アドレスを確認し、ブラウザでアクセスするなどでサーバーの動作を確認できます。

![ブラウザでアクセスしたところ](image-39.png)

```
※ドメイン取得やSSLについて
ここまでの手順ではHTTPでの直接IPアドレスを指定したアクセスで検証しています。
実際のサービスを運用するためには、SSLを使ったアクセスや、正式にドメインを取得しての様々な設定などが必要ですが、
有料の契約を含むことなど本項の内容を超えるので、ここでは説明しません。
```


メモ
ドメインの確保どうしようか…例として進める分には自分が持ってるドメインを使えばいいけど…
無料ではできんよなぁ。無料のDDNSとかでやれるかなぁ？

 sudo -u postgres psql

postgres=# create database nurinuriplateau;
CREATE DATABASE
postgres=# \c nurinuriplateau
You are now connected to database "nurinuriplateau" as user "postgres".
nurinuriplateau=# CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;
CREATE EXTENSION
CREATE EXTENSION
nurinuriplateau=#
nurinuriplateau=# \q


postgres=#
postgres=# \c nurinuriplateau
You are now connected to database "nurinuriplateau" as user "postgres".
nurinuriplateau=# create table main (
nurinuriplateau(#   id SERIAL PRIMARY KEY,
nurinuriplateau(#   geom GEOMETRY(POLYGON,4326),
nurinuriplateau(#   area REAL);
CREATE TABLE
nurinuriplateau=# INSERT INTO main (geom, area) VALUES (
nurinuriplateau(# ST_GeomFromText('POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))', 4326),
nurinuriplateau(# ST_Area(ST_GeomFromText('POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))', 4326)));
INSERT 0 1
nurinuriplateau=# SELECT * FROM main;
nurinuriplateau=# \q
ubuntu@ip-172-31-17-190:~$ sudo -u postgres psql
could not change directory to "/home/ubuntu": Permission denied
psql (14.8 (Ubuntu 14.8-0ubuntu0.22.04.1))
Type "help" for help.

postgres=# \c nurinuriplateau
You are now connected to database "nurinuriplateau" as user "postgres".
nurinuriplateau=# SELECT * FROM main;
nurinuriplateau=# INSERT INTO main (geom, area) VALUES (
ST_GeomFromText('POLYGON((0 0, 0 1.1, 1.1 1.1, 1.1 0, 0 0))', 4326),
ST_Area(ST_GeomFromText('POLYGON((0 0, 0 1.1, 1.1 1.1, 1.1 0, 0 0))', 4326)));
INSERT 0 1
nurinuriplateau=# SELECT * FROM main;


create table placedata (
  id SERIAL PRIMARY KEY,
  userid VARCHAR(255) NOT NULL,
  side INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  geom GEOMETRY(POLYGON,4326) NOT NULL,
  area REAL NOT NULL);


nurinuriplateau=> SELECT ST_Area(ST_GeomFromText('POLYGON((0 0, 0 1.1, 1.1 1.1, 1.1 0, 0 0))',4326)::geography);
      st_area

--------------------

 14893547154.626783
(1 row)


Python・Flaskで作るかな
送信可能なAPIをまず作る
デプロイ先はAWSにしよう
スキーマの決定


### サーバーへの位置情報の送信
UnityWebRequest
APIに合わせてリクエスト
ループを閉じたときにまとめてリクエスト
ユーザーが受け取っている最後のIDも送る
DBに、ID（AutoInc）、時刻、ユーザーのUUID、Geomを格納
ユーザーが受け取っていないIDの時刻内のGeomと面積の集計を返却する
トランザクション忘れるな

### サーバーでの面積の計算
PostGISのクエリでSQLで計算してみる
SELECT　でArea計算

### サーバーで塗った場所の表示
これはQGISで直接DBにアクセスしてやろうかな
それが一番楽そう

### 正確な面積計算のプログラム
データ分析の文脈でこの辺をQGIS？あたりを使いながら説明

### コラム　チート対策

地理情報を扱ううえでのチート対策など

### コラム　プライバシーについて

地理情報は個人情報であることの説明

## アプリとしてリリースする

### Google Playに出す


### AppStoreに出す

JWTでのトークン認証


//////　以下メモ

## 位置情報を複数人で共有する

サーバーと連携する仕組みの作成
 位置情報を扱うときに気にすること
  座標系
  精度
 データベース
  格納方法 単なるDoubleか、空間データ構造か
  インデックス

## 池袋塗りつぶしゲームを作る

  チート対策
 データ分析
  どんな分析ができる？
  分析のヒント
 オクルージョン

## アプリとしてリリースする

AppStore・Google Playに出す方法
