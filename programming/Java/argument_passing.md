# [[Java]]における引数渡し

[[Java]]は厳密には**「すべて[[値渡し]] (Pass-by-Value)」**です。しかし、オブジェクトを扱う場合は「オブジェクトへの参照（[[ポインタ]]のようなもの）」を値として渡すため、挙動を正しく理解する必要があります。

## 1. プリミティブ型（int, double等）
値そのものがコピーされます。関数内での変更は呼び出し元に影響しません。

## 2. オブジェクト型
「オブジェクトへの参照」の値がコピーされます。

### 具体例
```java
class MyNumber {
    int value;
}

public class Main {
    public static void main(String[] args) {
        MyNumber obj = new MyNumber();
        obj.value = 10;

        modify(obj);
        System.out.println(obj.value); // 結果: 20 (中身は書き換わる)

        reassign(obj);
        System.out.println(obj.value); // 結果: 20 (指し示す先は変わらない)
    }

    static void modify(MyNumber n) {
        n.value = 20; // 参照先の中身を操作
    }

    static void reassign(MyNumber n) {
        n = new MyNumber(); // 引数nに新しいオブジェクトを代入
        n.value = 50;       // これは呼び出し元のobjには影響しない
    }
}
```

## 3. なぜ再代入は反映されないのか（コップの比喩）
[[Java]]の変数は、オブジェクトの「住所（参照）」が入った**「コップ」**だと考えると分かりやすいです。

1. **呼び出し時**: `main` にあるコップ `obj` の中身（住所A）が、関数のコップ `n` に**コピー**されます。
2. **`n.value = 20`**: コップ `n` に入っている住所Aの場所へ行き、その建物の壁の色を塗り替えます。これは `main` の `obj` が指している建物と同じなので、変更が見えます。
3. **`n = new MyNumber()`**: コップ `n` の中身（住所）を、新しく建てた「住所B」に書き換えます。
4. **結果**: `main` のコップ `obj` の中身は「住所A」のままです。`n` というコップの中身をどう入れ替えても、`obj` というコップには何の影響もありません。
