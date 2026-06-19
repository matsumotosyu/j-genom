const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("デプロイアカウント:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("残高:", hre.ethers.formatEther(balance), "ETH\n");

  // JGEMToken デプロイ
  console.log("JGEMToken をデプロイ中...");
  const JGEMToken = await hre.ethers.getContractFactory("JGEMToken");
  const jgem = await JGEMToken.deploy();
  await jgem.waitForDeployment();
  console.log("JGEMToken:", await jgem.getAddress());

  // DivergedStringNFT デプロイ
  console.log("DivergedStringNFT をデプロイ中...");
  const DivergedStringNFT = await hre.ethers.getContractFactory("DivergedStringNFT");
  const nft = await DivergedStringNFT.deploy();
  await nft.waitForDeployment();
  console.log("DivergedStringNFT:", await nft.getAddress());

  // JGenomGenesis デプロイ
  console.log("JGenomGenesis をデプロイ中...");
  const JGenomGenesis = await hre.ethers.getContractFactory("JGenomGenesis");
  const genesis = await JGenomGenesis.deploy();
  await genesis.waitForDeployment();
  console.log("JGenomGenesis:", await genesis.getAddress());
  console.log("ジェネシスブロック:", await genesis.genesisBlock());

  console.log("\n✓ デプロイ完了");
  console.log("---");
  console.log("JGEM_TOKEN_ADDRESS=", await jgem.getAddress());
  console.log("NFT_CONTRACT_ADDRESS=", await nft.getAddress());
  console.log("GENESIS_CONTRACT_ADDRESS=", await genesis.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
