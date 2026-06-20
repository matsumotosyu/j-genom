import { useState } from "react";
import { useAccount, useConnect, useDisconnect, useWriteContract, useReadContract } from "wagmi";
import { parseUnits, formatUnits } from "viem";
import { JGEM_TOKEN_ADDRESS, NFT_CONTRACT_ADDRESS, JGEM_ABI, NFT_ABI } from "./contracts";
import "./App.css";

function friendlyError(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e);
  if (/user rejected|user denied|rejected the request/i.test(msg))
    return "トランザクションがキャンセルされました";
  if (/already registered/i.test(msg))
    return "この文字列はすでに登録されています";
  if (/unauthorized|not the owner|onlyOwner/i.test(msg))
    return "オーナーアカウントでのみ登録できます";
  if (/insufficient funds/i.test(msg))
    return "Sepolia ETH が不足しています。フォーセットから補充してください";
  if (/failed to fetch|network/i.test(msg))
    return "サーバーに接続できません。しばらく待ってから再度お試しください（初回起動に30秒ほどかかる場合があります）";
  if (/execution reverted/i.test(msg))
    return "トランザクションが失敗しました（コントラクトにより拒否されました）";
  return "エラーが発生しました。しばらく待ってから再度お試しください";
}

const REGIONS = ["JA-JP", "EN-GB", "EN-US", "ZH-CN", "ZH-TW", "KO-KR"];

interface DIResult {
  text: string;
  reading: string;
  machine_reading: string;
  kanji_count: number;
  mora_count: number;
  avg_strokes: number;
  mora_kanji_ratio: number;
  penalty_factor: number;
  score_ratio: number;
  score_prediction: number;
  score_strokes: number;
  score_rarity: number;
  di_score: number;
}

function WalletSection() {
  const { address, isConnected } = useAccount();
  const { connect, connectors } = useConnect();
  const { disconnect } = useDisconnect();

  const { data: jgemBalance } = useReadContract({
    address: JGEM_TOKEN_ADDRESS,
    abi: JGEM_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: { enabled: !!address },
  });

  const { data: nftBalance } = useReadContract({
    address: NFT_CONTRACT_ADDRESS,
    abi: NFT_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: { enabled: !!address },
  });

  if (!isConnected) {
    return (
      <div className="wallet-section">
        <button onClick={() => connect({ connector: connectors[0] })}>
          MetaMask を接続
        </button>
      </div>
    );
  }

  return (
    <div className="wallet-section connected">
      <div className="address">{address?.slice(0, 6)}...{address?.slice(-4)}</div>
      <div className="balances">
        <span>JGEM: {jgemBalance !== undefined ? formatUnits(jgemBalance, 18) : "—"}</span>
        <span>NFT: {nftBalance?.toString() ?? "—"}</span>
      </div>
      <button className="disconnect" onClick={() => disconnect()}>切断</button>
    </div>
  );
}

function DIForm({ onResult }: { onResult: (r: DIResult) => void }) {
  const [text, setText] = useState("");
  const [reading, setReading] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("https://j-genom.onrender.com/calculate-di", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, reading }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail ?? "エラーが発生しました");
      }
      const data: DIResult = await res.json();
      onResult(data);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="di-form">
      <div className="field">
        <label>文字列</label>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="例: 小鳥遊"
          required
        />
      </div>
      <div className="field">
        <label>読み（ひらがな）</label>
        <input
          value={reading}
          onChange={(e) => setReading(e.target.value)}
          placeholder="例: たかなし"
          required
        />
      </div>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "計算中..." : "DI を計算"}
      </button>
    </form>
  );
}

function DIResult({ result }: { result: DIResult }) {
  return (
    <div className="di-result">
      <div className="di-score">{result.di_score}</div>
      <div className="di-label">Divergence Index</div>
      <table className="breakdown">
        <tbody>
          <tr><td>機械読み</td><td>{result.machine_reading}</td></tr>
          <tr><td>漢字数</td><td>{result.kanji_count}</td></tr>
          <tr><td>モーラ数</td><td>{result.mora_count}</td></tr>
          <tr><td>平均画数</td><td>{result.avg_strokes}</td></tr>
          <tr><td>比率スコア</td><td>{result.score_ratio.toFixed(3)}</td></tr>
          <tr><td>予測スコア</td><td>{result.score_prediction.toFixed(3)}</td></tr>
          <tr><td>画数スコア</td><td>{result.score_strokes.toFixed(3)}</td></tr>
          <tr><td>希少性スコア</td><td>{result.score_rarity.toFixed(3)}</td></tr>
          {result.penalty_factor < 1 && (
            <tr className="penalty"><td>ペナルティ係数</td><td>{result.penalty_factor.toFixed(3)}</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function RegisterSection({ result }: { result: DIResult }) {
  const { address, isConnected } = useAccount();
  const [region, setRegion] = useState("JA-JP");
  const [recipient, setRecipient] = useState(address ?? "");
  const { writeContract, isPending, isSuccess, error } = useWriteContract();

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    const to = (recipient || address) as `0x${string}`;
    const diScoreInt = BigInt(Math.round(result.di_score * 10));
    const amount = parseUnits(String(result.di_score), 18);

    writeContract({
      address: NFT_CONTRACT_ADDRESS,
      abi: NFT_ABI,
      functionName: "register",
      args: [to, result.text, result.reading, diScoreInt, region],
    });

    // JGEM mint は NFT 登録後に別途送信が必要（onSuccess で連鎖させるのが理想だが、
    // シンプルに保つため今はここに記載のみ）
    void amount;
  }

  if (!isConnected) return null;

  return (
    <form onSubmit={handleRegister} className="register-form">
      <h3>NFT 登録（オーナーのみ）</h3>
      <div className="field">
        <label>リージョン</label>
        <select value={region} onChange={(e) => setRegion(e.target.value)}>
          {REGIONS.map((r) => <option key={r}>{r}</option>)}
        </select>
      </div>
      <div className="field">
        <label>受取アドレス</label>
        <input
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
          placeholder={address}
        />
      </div>
      {error && <p className="error">{friendlyError(error)}</p>}
      {isSuccess && <p className="success">トランザクションを送信しました。Etherscan で確認できます</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "送信中..." : `${result.text} を登録`}
      </button>
    </form>
  );
}

export default function App() {
  const [result, setResult] = useState<DIResult | null>(null);

  return (
    <div className="app">
      <header>
        <h1>J-Genom</h1>
        <p className="subtitle">じゅげむ — 文字と読みの乖離を刻む</p>
        <WalletSection />
      </header>

      <main>
        <section className="card">
          <h2>Divergence Index 計算</h2>
          <DIForm onResult={setResult} />
        </section>

        {result && (
          <>
            <section className="card">
              <h2>{result.text}（{result.reading}）</h2>
              <DIResult result={result} />
            </section>
            <section className="card">
              <RegisterSection result={result} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}
