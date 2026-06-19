export const JGEM_TOKEN_ADDRESS = "0x087d73D1c10EA7116C46a21A7a493800C09d5e35" as const;
export const NFT_CONTRACT_ADDRESS = "0xaE1414F966A9000911590B457863DB0171bFd08F" as const;

export const JGEM_ABI = [
  {
    inputs: [{ internalType: "address", name: "account", type: "address" }],
    name: "balanceOf",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "address", name: "to", type: "address" },
      { internalType: "uint256", name: "amount", type: "uint256" },
    ],
    name: "mint",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
] as const;

export const NFT_ABI = [
  {
    inputs: [
      { internalType: "address", name: "to", type: "address" },
      { internalType: "string", name: "text", type: "string" },
      { internalType: "string", name: "reading", type: "string" },
      { internalType: "uint256", name: "diScore", type: "uint256" },
      { internalType: "string", name: "region", type: "string" },
    ],
    name: "register",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [{ internalType: "address", name: "owner", type: "address" }],
    name: "balanceOf",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
] as const;
