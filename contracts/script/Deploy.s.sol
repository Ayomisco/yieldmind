// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {YieldVault} from "../src/YieldVault.sol";
import {MockWstETH} from "../src/MockWstETH.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address agentWallet = vm.envAddress("AGENT_WALLET_ADDRESS");

        vm.startBroadcast(deployerKey);

        // 1. Deploy mock wstETH (testnet only)
        MockWstETH mockWstETH = new MockWstETH();
        console.log("MockWstETH deployed:", address(mockWstETH));

        // 2. Deploy YieldVault
        uint256 maxPerTx = 0.01 ether;   // 0.01 wstETH per tx
        uint256 dailyCap = 0.05 ether;   // 0.05 wstETH per day
        YieldVault vault = new YieldVault(
            address(mockWstETH),
            agentWallet,
            maxPerTx,
            dailyCap
        );
        console.log("YieldVault deployed:", address(vault));

        // 3. Whitelist agent wallet as recipient
        vault.addRecipient(agentWallet);

        vm.stopBroadcast();

        // Post-deployment logs
        console.log("\n=== DEPLOYMENT COMPLETE ===");
        console.log("MockWstETH:", address(mockWstETH));
        console.log("YieldVault:", address(vault));
        console.log("Agent wallet:", agentWallet);
        console.log("\n=== ADD TO .env ===");
        console.log("MOCK_WSTETH_ADDRESS=", address(mockWstETH));
        console.log("YIELD_VAULT_ADDRESS=", address(vault));
    }
}
