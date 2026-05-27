-- Estate Asset Manager Database Schema
-- Optimized with proper indexing for performance

CREATE DATABASE IF NOT EXISTS estate_assets;
USE estate_assets;

-- Locations table
CREATE TABLE locations (
    location_id   INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location_name (location_name)
);

-- Assets base table (for all asset types)
CREATE TABLE assets (
    asset_id      INT AUTO_INCREMENT PRIMARY KEY,
    asset_type    VARCHAR(50) NOT NULL,
    description   VARCHAR(500) NOT NULL,
    location_id   INT,
    value         DECIMAL(12,2),
    disposition   VARCHAR(100),
    image_url     VARCHAR(500),
    notes         TEXT,
    is_archived   TINYINT(1) NOT NULL DEFAULT 0,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_assets_location
        FOREIGN KEY (location_id)
        REFERENCES locations(location_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    
    INDEX idx_asset_type (asset_type),
    INDEX idx_is_archived (is_archived),
    INDEX idx_location_id (location_id),
    INDEX idx_created_at (created_at),
    INDEX idx_asset_type_archived (asset_type, is_archived)
);

-- Video-specific details
CREATE TABLE video_details (
    asset_id        INT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    format          VARCHAR(50),
    upc             VARCHAR(12),
    cover_image_url VARCHAR(500),
    
    CONSTRAINT fk_videodetails_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(asset_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    INDEX idx_title (title),
    INDEX idx_upc (upc)
);

-- View for all video assets with joins
CREATE OR REPLACE VIEW v_video_assets AS
SELECT
    a.asset_id,
    a.description,
    a.location_id,
    l.location_name,
    a.value,
    a.disposition,
    a.image_url,
    a.notes,
    a.is_archived,
    a.created_at,
    a.updated_at,
    vd.title,
    vd.format,
    vd.upc,
    vd.cover_image_url
FROM assets a
LEFT JOIN video_details vd ON a.asset_id = vd.asset_id
LEFT JOIN locations l ON a.location_id = l.location_id
WHERE a.asset_type = 'video';

-- View for active (non-archived) video assets
CREATE OR REPLACE VIEW v_video_assets_active AS
SELECT * FROM v_video_assets WHERE is_archived = 0;

-- View for archived video assets
CREATE OR REPLACE VIEW v_video_assets_archived AS
SELECT * FROM v_video_assets WHERE is_archived = 1;

-- Audit log table (optional - for tracking changes)
CREATE TABLE asset_audit_log (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    asset_id      INT NOT NULL,
    action        VARCHAR(50) NOT NULL,
    old_values    JSON,
    new_values    JSON,
    changed_by    VARCHAR(100),
    changed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_audit_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(asset_id)
        ON DELETE CASCADE,
    
    INDEX idx_asset_id (asset_id),
    INDEX idx_changed_at (changed_at)
);
