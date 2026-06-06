# Forest Survival ゲーム — 自動バグ修正ループ 引き継ぎドキュメント

## 概要

このリポジトリの `/game/index.html` はシングルファイルのPhaser.js 3製ブラウザゲーム「Forest Survival」です。
**継続的バグ発見・修正ループ**を実施中です。引き継いだClaude Codeはループを継続してください。

---

## 作業ルール（必須）

- **全レスポンスは日本語**
- **作業ブランチ**: `claude/forest-survival-game-3vyC7`
- **ファイル修正後は必ず** `/home/user/kai/docs/index.html` にも同期: `cp game/index.html docs/index.html`
- **コミット・プッシュ**: 修正のたびに `git add game/index.html docs/index.html && git commit && git push -u origin claude/forest-survival-game-3vyC7`
- バグを見つけるエージェントは**常に稼働**させること（ループを止めない）

---

## ゲーム構成

- **ファイル**: `/home/user/kai/game/index.html`（約1685行、全てここに集約）
- **Phaser.js 3** ゲーム、シーン構成:
  - `TitleScene` — タイトル画面
  - `GameScene` — ゲーム本体（プレイヤー・敵・リソース・WAVEシステム）
  - `UIScene` — HUD・アップグレード・ポーズ・クラフトパネル
- **物理エンジン**: Arcade Physics
- **BGM**: Web Audio API（オシレーター＋LFO自前実装）

### 主要グローバル変数

```javascript
const STATE = { gold, wood, meat, skin, gem, stone, weaponLv, armorLv, baseLv,
                kills, totalGold, areas, wave, craftAtk, craftCol, craftBurst, playTime }
const SAVE_KEY = 'fsurvival_v3'
const HS_KEY = 'fsurvival_hs'
let _bgm = null   // BGMノード群
let _ac = null    // AudioContext シングルトン
```

---

## バグ発見ループの手順

### 毎ラウンドの作業

1. **4つのExploreエージェントを並列起動**（異なる調査対象を割り当てる）
2. 全エージェントの結果を待つ
3. 各報告に対して **FALSE POSITIVE フィルタリング** を実施:
   - Phaser 3の組み込み機能（InputPlugin.shutdown()等）が自動処理するもの → FALSE POSITIVE
   - JavaScriptシングルスレッドで安全なもの → FALSE POSITIVE
   - ゲームデザインの意図的な仕様 → FALSE POSITIVE
4. REAL BUGのみ修正 → コミット → プッシュ
5. 次のラウンドへ

### エージェント起動例

```
Agent(subagent_type="Explore", prompt="Forest Survival Phaser.js 3ゲーム（/home/user/kai/game/index.html）の[調査対象]を詳細に調査してください。バグ候補はFALSE POSITIVE/REAL BUGで分類し、行番号と修正案を日本語で報告してください。")
```

---

## 修正済みバグ一覧（R130〜R141）

| ラウンド | 行番号（修正後） | バグ内容 | 修正内容 |
|---------|--------------|---------|---------|
| R130-A | ~1123 | `_milestones()` の `prev` 変数がループ外で固定され、BURSTで複数閾値を同時突破すると全てのマイルストーン報酬が発火 | `prev` をループ内で参照せず `this._lastMilestone` を直接比較するよう変更 |
| R130-B | ~674 | コンボラベルのtweenが2500msで早すぎて読めない | `duration: 2500` → `duration: 3000` |
| R131 | ~1636-1665 | `notify()` がキューなし実装で通知が上書きされる | `_notifyQ` キュー + `_showNotify()` による順次表示に変更 |
| R132 | ~1083 | WAVE敵のspawn数がcount=0でも「×0体出現！」と通知 | `if(count>0)` ガードを追加 |
| R134 | ~1407 | ポーズ時にGameSceneのupdateループは止まるがWeb Audio BGMは継続 | ポーズ時に `_bgm.master.gain` をフェードアウト、再開時にフェードイン |
| R136 | ~168 | `hasSave()` が破損JSONでも `true` を返す | `JSON.parse()` でtry-catch検証を追加 |
| R137 | ~579-583 | ロックマーカーがアンロック済みエリアでも500ms表示される | 生成時に `setVisible(!areaUnlocked(lk.areaId))` で初期可視性を設定 |
| R138 | ~494 | `this.tSave=0` でゲーム起動直後の自動セーブ時、最大60秒分のplayTimeが水増しされる | `this.tSave=this.time.now` に変更 |
| R141 | ~682-684, 963-970 | エリアアンロック前に死んだ敵は `enemyQ` に追加されず、アンロック後も永遠に復活しない | 死亡時のareaチェックを廃止し、スポーン時に `areaUnlocked()` を確認するよう変更 |

---

## 重要な設計知識（FALSE POSITIVE判定の参考）

- **y-sort depth**: 敵は `py+80`、プレイヤーは `y+50` でdepth設定 → 意図的な設計
- **scene.stop()**: Phaser 3はInputPlugin.shutdown()とTimePlugin.shutdown()を自動呼び出し → リスナー多重登録なし
- **Web Audio LFO disconnect**: stopBGM()でdisconnectしていないが、pageリロードで解放 → 低リスク
- **採取スロットル1秒**: `if(time-this.tCol<1000) return` → 意図的なゲームデザイン
- **木のリスポーン14秒 vs 岩22秒**: バランス設計
- **クラフト画面中のゲーム進行**: ポーズとは独立した設計
- **WAVEタイマーベース**: 敵の生死に関係なく時間経過でWAVE進行 → 意図的

---

## 調査済みエリア（再調査不要）

- [x] ドロップアイテム収集ロジック（TTL・スロットル・重複防止）
- [x] エリアアンロック処理（STATE.areas・ロックマーカー）
- [x] アップグレードUI・コスト計算
- [x] リスポーン・ゲームオーバー処理
- [x] WAVEスポーン・タイマーロジック
- [x] BURSTスキル（alive チェック確認済み）
- [x] クラフト強化システム
- [x] BGM・Webオーディオシステム
- [x] セーブ・ロードシステム
- [x] リソース（木・岩）採取ロジック
- [x] 敵リスポーンキュー処理
- [x] HUD・統計パネル表示

---

## 未調査エリア（次ラウンドから継続）

次のラウンド（R142）は以下の4テーマで並列調査を開始してください：

### R142-A: プレイヤー攻撃処理
- `_attack()` メソッドの実装
- 攻撃範囲（`this.prng`）と攻撃間隔（`this.tAtk`）
- 攻撃対象の選択（最近傍の敵）
- 攻撃ヒット判定と `e.hit(dmg)` の呼び出し

### R142-B: 無敵時間・コンボシステム詳細
- `invincibleUntil` の設定と参照箇所
- プレイヤーの被ダメージ処理（`_damage()`等）
- コンボ数の増加条件（3秒以内の連続撃破）
- コンボラベルの表示と更新

### R142-C: パッシブスキル（`_passive()`）
- `_passive()` の実装全体
- `BASE_DATA[baseLv].passive` の定義と効果
- パッシブスキルの発動タイミング（tPassiveタイマー）
- パッシブとアクティブスキルの干渉

### R142-D: 仮想ジョイスティック（タッチ操作）
- VJoy（仮想ジョイスティック）の実装
- `_vjInput.dx`, `_vjInput.dy` の正規化処理
- タッチ開始・移動・終了イベントのハンドリング
- ポーズ時のVJoyリセット（`dx=0, dy=0`）との整合性

---

## 現在のコミット状態

- **最新コミット**: `d99e1dc` (R141: エリアアンロード前死亡の敵が復活しないバグ修正)
- **ブランチ**: `claude/forest-survival-game-3vyC7`
- **プッシュ済み**: ✅

---

## GitHub Pages

ユーザーが以下の設定をすると `/docs/index.html` がWeb公開される（ユーザー作業）:
- Repository Settings → Pages → Branch: `claude/forest-survival-game-3vyC7` / Folder: `/docs` → Save
