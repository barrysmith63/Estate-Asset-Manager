-- Stored Procedures for Estate Asset Manager
-- Optimized for performance and data integrity

USE estate_assets;

DELIMITER $$

-- Add new video asset
CREATE PROCEDURE add_video_asset (
    IN p_description      VARCHAR(500),
    IN p_location_id      INT,
    IN p_value            DECIMAL(12,2),
    IN p_disposition      VARCHAR(100),
    IN p_image_url        VARCHAR(500),
    IN p_notes            TEXT,
    IN p_title            VARCHAR(200),
    IN p_format           VARCHAR(50),
    IN p_upc              VARCHAR(12),
    IN p_cover_image_url  VARCHAR(500)
)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE exit_code INT DEFAULT 0;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET exit_code = 1;
    
    START TRANSACTION;
    
    -- Validate required fields
    IF p_description IS NULL OR TRIM(p_description) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Description cannot be empty';
    END IF;
    
    IF p_title IS NULL OR TRIM(p_title) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Title cannot be empty';
    END IF;
    
    -- Insert into assets table
    INSERT INTO assets (
        asset_type, description, location_id, value,
        disposition, image_url, notes
    ) VALUES (
        'video', p_description, p_location_id, p_value,
        p_disposition, p_image_url, p_notes
    );
    
    -- Insert into video_details table
    INSERT INTO video_details (
        asset_id, title, format, upc, cover_image_url
    ) VALUES (
        LAST_INSERT_ID(), p_title, p_format, p_upc, p_cover_image_url
    );
    
    COMMIT;
    
    IF exit_code = 1 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Failed to add video asset';
    END IF;
END$$

-- Update existing video asset
CREATE PROCEDURE update_video_asset (
    IN p_asset_id         INT,
    IN p_description      VARCHAR(500),
    IN p_location_id      INT,
    IN p_value            DECIMAL(12,2),
    IN p_disposition      VARCHAR(100),
    IN p_image_url        VARCHAR(500),
    IN p_notes            TEXT,
    IN p_title            VARCHAR(200),
    IN p_format           VARCHAR(50),
    IN p_upc              VARCHAR(12),
    IN p_cover_image_url  VARCHAR(500)
)
DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    DECLARE exit_code INT DEFAULT 0;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET exit_code = 1;
    
    START TRANSACTION;
    
    -- Validate asset exists and is a video
    IF NOT EXISTS (SELECT 1 FROM assets WHERE asset_id = p_asset_id AND asset_type = 'video') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Video asset not found';
    END IF;
    
    -- Validate required fields
    IF p_description IS NULL OR TRIM(p_description) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Description cannot be empty';
    END IF;
    
    IF p_title IS NULL OR TRIM(p_title) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Title cannot be empty';
    END IF;
    
    -- Update assets table
    UPDATE assets
    SET 
        description = p_description,
        location_id = p_location_id,
        value       = p_value,
        disposition = p_disposition,
        image_url   = COALESCE(p_image_url, image_url),
        notes       = p_notes
    WHERE asset_id = p_asset_id
      AND asset_type = 'video';
    
    -- Update video_details table
    UPDATE video_details
    SET 
        title           = p_title,
        format          = p_format,
        upc             = p_upc,
        cover_image_url = p_cover_image_url
    WHERE asset_id = p_asset_id;
    
    COMMIT;
    
    IF exit_code = 1 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Failed to update video asset';
    END IF;
END$$

-- Delete video asset (hard delete)
CREATE PROCEDURE delete_video_asset (IN p_asset_id INT)
DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    DECLARE exit_code INT DEFAULT 0;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET exit_code = 1;
    
    START TRANSACTION;
    
    -- Verify asset is a video before deleting
    IF NOT EXISTS (SELECT 1 FROM assets WHERE asset_id = p_asset_id AND asset_type = 'video') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Video asset not found';
    END IF;
    
    -- Delete from video_details (cascade will handle this, but explicit for clarity)
    DELETE FROM video_details WHERE asset_id = p_asset_id;
    
    -- Delete from assets
    DELETE FROM assets WHERE asset_id = p_asset_id AND asset_type = 'video';
    
    COMMIT;
    
    IF exit_code = 1 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Failed to delete video asset';
    END IF;
END$$

-- Archive asset (soft delete)
CREATE PROCEDURE archive_asset (IN p_asset_id INT)
DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    UPDATE assets
    SET is_archived = 1
    WHERE asset_id = p_asset_id;
END$$

-- Unarchive asset
CREATE PROCEDURE unarchive_asset (IN p_asset_id INT)
DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    UPDATE assets
    SET is_archived = 0
    WHERE asset_id = p_asset_id;
END$$

-- Get asset count by type
CREATE PROCEDURE get_asset_count (
    IN p_asset_type VARCHAR(50),
    OUT p_total INT,
    OUT p_archived INT,
    OUT p_active INT
)
DETERMINISTIC
READS SQL DATA
BEGIN
    SELECT COUNT(*) INTO p_total 
    FROM assets WHERE asset_type = p_asset_type;
    
    SELECT COUNT(*) INTO p_archived 
    FROM assets WHERE asset_type = p_asset_type AND is_archived = 1;
    
    SELECT COUNT(*) INTO p_active 
    FROM assets WHERE asset_type = p_asset_type AND is_archived = 0;
END$$

-- Get assets by location
CREATE PROCEDURE get_assets_by_location (
    IN p_location_id INT,
    IN p_asset_type VARCHAR(50) DEFAULT 'video',
    IN p_include_archived TINYINT DEFAULT 0
)
DETERMINISTIC
READS SQL DATA
BEGIN
    SELECT 
        a.asset_id,
        a.description,
        a.value,
        a.disposition,
        a.is_archived,
        a.created_at,
        vd.title,
        vd.format
    FROM assets a
    LEFT JOIN video_details vd ON a.asset_id = vd.asset_id
    WHERE a.location_id = p_location_id
      AND a.asset_type = p_asset_type
      AND (p_include_archived = 1 OR a.is_archived = 0)
    ORDER BY a.created_at DESC;
END$$

-- Search videos
CREATE PROCEDURE search_videos (
    IN p_search_term VARCHAR(255),
    IN p_limit INT DEFAULT 50,
    IN p_include_archived TINYINT DEFAULT 0
)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE search_pattern VARCHAR(257);
    SET search_pattern = CONCAT('%', p_search_term, '%');
    
    SELECT
        a.asset_id,
        a.description,
        a.location_id,
        l.location_name,
        a.value,
        a.is_archived,
        vd.title,
        vd.format,
        vd.upc,
        CASE
            WHEN vd.title LIKE search_pattern THEN 2
            WHEN a.description LIKE search_pattern THEN 1
            ELSE 0
        END AS relevance
    FROM assets a
    LEFT JOIN video_details vd ON a.asset_id = vd.asset_id
    LEFT JOIN locations l ON a.location_id = l.location_id
    WHERE a.asset_type = 'video'
      AND (vd.title LIKE search_pattern OR a.description LIKE search_pattern)
      AND (p_include_archived = 1 OR a.is_archived = 0)
    ORDER BY relevance DESC, vd.title ASC
    LIMIT p_limit;
END$$

DELIMITER ;
