// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title JGenomGenesis
 * @notice J-Genom の起源ブロック。
 *         落語「寿限無」において子に与えられた名前の文字列を永続化する。
 *
 *         寿限無は「意味の過積載が機能不全を生む」という逆説を体現する。
 *         これはハッシュ関数の衝突耐性の限界——固定長の出力空間に無限の入力を
 *         写像する以上、一意性を完全には保てないという数学的必然——と構造的に同一である。
 *
 *         このコントラクトが刻まれたブロックが J-Genom の起源となる。
 */
contract JGenomGenesis {
    string public constant JUGEMU =
        unicode"寿限無、寿限無、五劫の擦り切れ、海砂磨る砂利の水行末"
        unicode"雲来末、風来末、食う寝るところに住むところ"
        unicode"やぶら小路のぶら小路、パイポパイポ、パイポのシューリンガン"
        unicode"シューリンガンのグーリンダイ、グーリンダイのポンポコピーのポンポコナーの"
        unicode"長久命の長助";

    uint256 public immutable genesisBlock;
    uint256 public immutable genesisTimestamp;

    event Genesis(
        string text,
        uint256 indexed blockNumber,
        uint256 timestamp
    );

    constructor() {
        genesisBlock = block.number;
        genesisTimestamp = block.timestamp;
        emit Genesis(JUGEMU, block.number, block.timestamp);
    }
}
