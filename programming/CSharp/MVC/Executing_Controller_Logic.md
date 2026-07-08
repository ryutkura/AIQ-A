# User[[Controller]].Profile(5) をプログラム上で意図的に実行したい場合

「プログラムの中から、特定の[[コントローラー]]の処理（`User[[Controller]].Profile(5)`など）を狙って実行したい」と思った場合、**「あなたが本当にやりたいことは何か？」** によって正解が3パターンに分かれます。

ここで最も重要なルールがあります。それは**「他の[[C#]]のコードから、[[Controller]]の[[メソッド]]を直接呼び出してはいけない」**ということです。（例：別の[[クラス]]から `var c = new User[[Controller]](); c.Profile(5);` と書くのは絶対NGです）

[[Controller]]はあくまで「Webからのリクエスト（[[HTTP]]）を受け取る専用の窓口」だからです。

では、目的別にどうすればいいかを見ていきましょう。

---

## パターン1：「この[[URL]]にアクセスした時に実行させたい」場合（[[URL]]のカスタマイズ）

デフォルトの `/User/Profile/5` という[[URL]]ではなく、例えば `/mypage/5` という[[URL]]でアクセスが来た時に `User[[Controller]].Profile(5)` を実行させたい場合です。

この場合は、おっしゃる通り**「[[ルーティング]]の設定」**を弄るのが大正解です。

現代のASP.NET Coreでは `Program.cs`（昔は `RouteConfig.cs`）に書くか、もっと簡単な**属性[[ルーティング]] (Attribute Routing)** を使います。

```csharp
public class User[[Controller]] : [[Controller]]
{
    // [Route]属性をつけることで、「/mypage/5」という[[URL]]とこの[[メソッド]]を紐づける！
    [Route("mypage/{id}")]
    public IActionResult Profile(int id)
    {
        // 処理
        return [[View]]();
    }
}
```

## パターン2：「別の処理が終わった後に、自動的にProfile画面に飛ばしたい」場合（リダイレクト）

例えば、「ログイン処理（Login[[メソッド]]）」が終わった後に、自動的に `Profile(5)` を実行して画面を表示させたい場合です。

この場合は、**リダイレクト（RedirectToAction）**という機能を使います。これは、サーバー側からブラウザに対して「今度はこの[[URL]]にアクセスし直してね」と命令を出す機能です。

```csharp
public class Auth[[Controller]] : [[Controller]]
{
    public IActionResult Login()
    {
        // ... ログイン成功の処理 ...

        int loggedInUserId = 5;

        // User[[Controller]]のProfile[[メソッド]](引数id=5)へ、ブラウザを強制移動させる！
        return RedirectToAction("Profile", "User", new { id = loggedInUserId });
    }
}
```

## パターン3：「Profileの中の『計算ロジック』だけを別の場所でも使い回したい」場合（Service層への切り出し）

「画面を表示したいわけじゃないけど、`Profile` [[メソッド]]の中に書いてある『ユーザー情報を取得して複雑な計算をする処理』を、夜間の自動バッチ処理や別の[[API]]からも実行したい」という場合です。

これがまさに前回の**「Service層を作る（Fat [[Controller]]を避ける）」**話に繋がります。
[[Controller]]の[[メソッド]]を直接呼ぶのではなく、**中身のロジックだけをServiceに移動させて、それをみんなで共有して呼び出します。**

```csharp
// 【Service[[クラス]]（使い回すロジックの本体）】
public class UserService
{
    // Profile[[メソッド]]の中にあった処理をこっちに移動する
    public UserData GetUserProfileData(int id)
    {
        // DBから取得して計算する処理...
        return data;
    }
}

// 【元のUser[[Controller]]】
public class User[[Controller]] : [[Controller]]
{
    public IActionResult Profile(int id)
    {
        // Serviceを呼び出すだけ
        var data = _userService.GetUserProfileData(id);
        return [[View]](data);
    }
}

// 【夜間バッチなど、別のプログラム】
public class NightBatch
{
    public void Run()
    {
        // 同じServiceを呼び出せる！（[[Controller]]は経由しない）
        var data = _userService.GetUserProfileData(5); 
        // 別の処理...
    }
}
```

---

### まとめ

1. **[[URL]]を変えたい** → [[ルーティング]]（`[Route]` 属性など）を使う。
2. **処理後に画面を移動させたい** → `RedirectToAction` を使う。
3. **ロジックを使い回したい** → 中身を `Service` [[クラス]]に抜き出して、それを呼ぶ。

「プログラムから[[Controller]]を直接呼ぶ」という発想が出た時は、「あ、ロジックをServiceに分けるサインだな」と思い出してみてください！
