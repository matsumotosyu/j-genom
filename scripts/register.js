const hre = require("hardhat");

async function main() {
  const [owner] = await hre.ethers.getSigners();

  const jgem = await hre.ethers.getContractAt("JGEMToken", process.env.JGEM_TOKEN_ADDRESS);
  const nft  = await hre.ethers.getContractAt("DivergedStringNFT", process.env.NFT_CONTRACT_ADDRESS);

  // 登録する文字列
  const text    = "小鳥遊";
  const reading = "たかなし";
  const diScore = 337;   // DI 33.7 → 整数で扱うため × 10
  const region  = "JA-JP";
  const to      = owner.address;

  console.log(`登録: ${text} / ${reading} (DI: ${diScore / 10}, region: ${region})`);

  // NFT 登録
  const tx1 = await nft.register(to, text, reading, diScore, region);
  await tx1.wait();
  console.log("NFT 登録完了:", tx1.hash);

  // JGEM 発行（DI スコアぶん）
  const amount = hre.ethers.parseUnits(String(diScore / 10), 18);
  const tx2 = await jgem.mint(to, amount);
  await tx2.wait();
  console.log("JGEM 発行完了:", tx2.hash);

  // 残高確認
  const balance = await jgem.balanceOf(to);
  console.log("JGEM 残高:", hre.ethers.formatEther(balance), "JGEM");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
