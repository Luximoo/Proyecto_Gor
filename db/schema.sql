-- Esquema inicial de la base de datos para el proyecto Gorditas

CREATE DATABASE IF NOT EXISTS gorditas 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE gorditas;

CREATE TABLE IF NOT EXISTS pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estado TINYINT NOT NULL DEFAULT 1 COMMENT '1: Pendiente/Activo, 3: Completado',
    pedido TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
