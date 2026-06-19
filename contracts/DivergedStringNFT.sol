// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title DivergedStringNFT
 * @notice 乖離文字列の発見者記録 NFT。
 *         リージョン + 文字列 + 読み の組み合わせは世界に1枚のみ発行される。
 *         J-Genom上の所有権は登録から10年で失効し、コモンズへ移行する。
 */
contract DivergedStringNFT is ERC721, Ownable {
    struct DivergedString {
        string text;        // 文字列（例: 小鳥遊）
        string reading;     // 読み（例: たかなし）
        uint256 diScore;    // DI スコア × 100（例: 33.7 → 3370）
        string region;      // リージョン（例: JA-JP）
        address registrant; // 登録者アドレス
        uint256 registeredAt; // 登録タイムスタンプ
    }

    // J-Genom上の所有権有効期間: 10年
    uint256 public constant OWNERSHIP_DURATION = 10 * 365 days;

    uint256 private _nextTokenId;

    mapping(uint256 => DivergedString) public divergedStrings;

    // リージョン + 文字列 + 読み の一意性チェック
    mapping(bytes32 => bool) public registered;

    event StringRegistered(
        uint256 indexed tokenId,
        address indexed registrant,
        string text,
        string reading,
        uint256 diScore,
        string region
    );

    constructor() ERC721("J-Genom Diverged String", "JGDS") Ownable(msg.sender) {}

    /**
     * @notice 乖離文字列を登録し NFT を発行する。
     * @param to      登録者アドレス
     * @param text    文字列
     * @param reading 読み（ひらがな）
     * @param diScore DI スコア × 100
     * @param region  リージョンコード
     */
    function register(
        address to,
        string calldata text,
        string calldata reading,
        uint256 diScore,
        string calldata region
    ) external onlyOwner returns (uint256) {
        bytes32 key = keccak256(abi.encodePacked(region, text, reading));
        require(!registered[key], "Already registered in this region");

        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);

        divergedStrings[tokenId] = DivergedString({
            text: text,
            reading: reading,
            diScore: diScore,
            region: region,
            registrant: to,
            registeredAt: block.timestamp
        });
        registered[key] = true;

        emit StringRegistered(tokenId, to, text, reading, diScore, region);
        return tokenId;
    }

    /**
     * @notice J-Genom上の所有権が有効かどうかを返す。
     *         登録から10年経過するとコモンズへ移行する。
     */
    function isOwnershipValid(uint256 tokenId) external view returns (bool) {
        return block.timestamp < divergedStrings[tokenId].registeredAt + OWNERSHIP_DURATION;
    }
}
