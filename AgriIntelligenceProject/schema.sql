CREATE DATABASE IF NOT EXISTS agri_intelligence;
USE agri_intelligence;

-- 1. Master Crops Table (A-Z details)
CREATE TABLE IF NOT EXISTS master_crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    scientific_name VARCHAR(255),
    growth_duration_days INT,
    best_season ENUM('Kharif', 'Rabi', 'Zaid', 'Perennial'),
    ideal_temperature_range VARCHAR(50),
    best_soil_types TEXT,
    growing_months VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    website_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Input Products Table (Seeds, Fertilizers, Pesticides)
CREATE TABLE IF NOT EXISTS input_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category ENUM('Seed', 'Fertilizer', 'Pesticide', 'Herbicide', 'Fungicide', 'Other') NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    brand_id INT,
    technical_name VARCHAR(255), -- Active ingredient
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    unit_value DECIMAL(10, 2), -- e.g., 500
    unit_measure VARCHAR(20), -- e.g., gm, kg, ml, L
    source_url VARCHAR(500),
    image_url VARCHAR(500),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES companies(id),
    UNIQUE KEY unique_product (category, product_name, brand_id, technical_name)
);

-- 4. Crop Advisories Table (Mapping Crops to technical requirements)
CREATE TABLE IF NOT EXISTS crop_advisories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    growth_stage VARCHAR(100), -- e.g., Sowing, Flowering, Harvest
    requirement_type ENUM('Seed', 'Fertilizer', 'Pesticide'),
    technical_recommendation VARCHAR(255), -- e.g., "Urea", "NPK 19:19:19"
    dosage_per_acre VARCHAR(100),
    notes TEXT,
    FOREIGN KEY (crop_id) REFERENCES master_crops(id)
);

-- 5. Mandi Prices Table
CREATE TABLE IF NOT EXISTS mandi_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    state VARCHAR(100),
    district VARCHAR(100),
    mandi_name VARCHAR(255),
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    modal_price DECIMAL(10, 2),
    retail_min_price DECIMAL(10, 2),
    retail_max_price DECIMAL(10, 2),
    mall_min_price DECIMAL(10, 2),
    mall_max_price DECIMAL(10, 2),
    units VARCHAR(50),
    price_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES master_crops(id),
    UNIQUE KEY unique_mandi_price (mandi_name, crop_id, price_date)
);
