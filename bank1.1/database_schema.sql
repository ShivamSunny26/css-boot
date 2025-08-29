use bgb_bank;


-- Drop tables if they exist to allow for a clean creation
DROP TABLE IF EXISTS `transactions`;
DROP TABLE IF EXISTS `money_transfer_record`;
DROP TABLE IF EXISTS `users`;

-- Table for user accounts
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(255) NOT NULL,
    `account_no` VARCHAR(10) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `balance` DECIMAL(10, 2) NOT NULL DEFAULT '0.00',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for `account_no` for faster lookups
CREATE INDEX `idx_account_no` ON `users` (`account_no`);

-- Table to log all transactions (internal and refunds)
CREATE TABLE `transactions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `transaction_id` VARCHAR(36) NOT NULL UNIQUE,
    `from_account` VARCHAR(10) NOT NULL,
    `to_account` VARCHAR(10) NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `note` TEXT,
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`from_account`) REFERENCES `users`(`account_no`) ON DELETE CASCADE,
    FOREIGN KEY (`to_account`) REFERENCES `users`(`account_no`) ON DELETE CASCADE
);

-- Table to record interbank money transfers that interact with the gateway simulator
CREATE TABLE `money_transfer_record` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `transfer_ref` VARCHAR(255) NOT NULL UNIQUE,
    `from_account` VARCHAR(10) NOT NULL,
    `to_account` VARCHAR(10),
    `amount` DECIMAL(10, 2) NOT NULL,
    `gateway_id` VARCHAR(255),
    `status` ENUM('PENDING', 'SUCCESS', 'FAILED', 'REVERSED') NOT NULL DEFAULT 'PENDING',
    `gateway_response` TEXT,
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`from_account`) REFERENCES `users`(`account_no`) ON DELETE CASCADE
);
