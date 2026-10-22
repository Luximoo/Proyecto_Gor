-- =============================================================================
-- Esquema Relacional de Base de Datos - Sistema de Pedidos Gorditas y Sopes
-- =============================================================================
-- ADVERTENCIA: Este script elimina las tablas anteriores para recrear el
-- esquema relacional desde cero.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS gorditas
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE gorditas;

-- Desactivar temporalmente revisión de llaves foráneas para limpiar en cualquier orden
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS item_modificadores;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS platos;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS producto_ingrediente;
DROP TABLE IF EXISTS ingredientes;
DROP TABLE IF EXISTS productos;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- 1. Catálogo de Productos (Gordita, Sope, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT uq_productos_nombre UNIQUE (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. Catálogo de Ingredientes (Guisos y complementos como Queso, Crema, Cebolla)
-- -----------------------------------------------------------------------------
CREATE TABLE ingredientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    es_guiso TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 = Guiso principal, 0 = Complemento/Guarnición',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT uq_ingredientes_nombre UNIQUE (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. Reglas de Ingredientes Permitidos por Producto (BASE, EXTRA, SIN)
-- -----------------------------------------------------------------------------
CREATE TABLE producto_ingrediente (
    producto_id INT NOT NULL,
    ingrediente_id INT NOT NULL,
    tipo ENUM('BASE', 'EXTRA', 'SIN') NOT NULL,
    PRIMARY KEY (producto_id, ingrediente_id, tipo),
    CONSTRAINT fk_prod_ing_producto
        FOREIGN KEY (producto_id) REFERENCES productos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_ing_ingrediente
        FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. Cabecera de Pedidos
-- -----------------------------------------------------------------------------
CREATE TABLE pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Número de pedido',
    tipo_servicio ENUM('MESA', 'LLEVAR') NOT NULL COMMENT 'MESA = Comer ahí, LLEVAR = Para llevar',
    estado ENUM('PENDIENTE', 'COMPLETADO') NOT NULL DEFAULT 'PENDIENTE',
    version INT NOT NULL DEFAULT 1 COMMENT 'Se incrementa en cada edición para control de cambios',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_pedidos_estado_created (estado, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. Platos dentro de un Pedido (Plato 1, Plato 2, ...)
-- -----------------------------------------------------------------------------
CREATE TABLE platos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    numero INT NOT NULL COMMENT 'Número de plato dentro del pedido (1, 2, 3...)',
    CONSTRAINT uq_platos_pedido_numero UNIQUE (pedido_id, numero),
    CONSTRAINT fk_platos_pedido
        FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. Platillos (Items) dentro de cada Plato
-- -----------------------------------------------------------------------------
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plato_id INT NOT NULL,
    producto_id INT NOT NULL,
    guiso_id INT NOT NULL,
    cantidad INT NOT NULL,
    nota VARCHAR(255) NOT NULL DEFAULT '',
    CONSTRAINT chk_items_cantidad CHECK (cantidad > 0),
    CONSTRAINT fk_items_plato
        FOREIGN KEY (plato_id) REFERENCES platos(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_items_producto
        FOREIGN KEY (producto_id) REFERENCES productos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_items_guiso
        FOREIGN KEY (guiso_id) REFERENCES ingredientes(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. Modificadores de cada Item (Con extra guiso/queso/crema, Sin cebolla, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE item_modificadores (
    item_id INT NOT NULL,
    ingrediente_id INT NOT NULL,
    tipo ENUM('EXTRA', 'SIN') NOT NULL,
    PRIMARY KEY (item_id, ingrediente_id, tipo),
    CONSTRAINT fk_item_mod_item
        FOREIGN KEY (item_id) REFERENCES items(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_item_mod_ingrediente
        FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
