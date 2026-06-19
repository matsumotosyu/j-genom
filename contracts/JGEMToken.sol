// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title JGEMToken
 * @notice J-Genom プロジェクトのユーティリティトークン。
 *         乖離文字列の登録時に DI スコアに比例して発行される。
 *         DI 計算はオフチェーンで行われ、オーナーが mint を呼び出す。
 */
contract JGEMToken is ERC20, Ownable {
    constructor() ERC20("J-Genom Token", "JGEM") Ownable(msg.sender) {}

    /**
     * @notice DI スコアに比例したトークンを発行する。
     * @param to     受取アドレス（登録者）
     * @param amount 発行量（DI スコア × 10^18 を想定）
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
