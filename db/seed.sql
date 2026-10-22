-- =============================================================================
-- Datos Iniciales del Catálogo (Seed) - Gorditas y Sopes
-- =============================================================================

USE gorditas;

-- 1. Productos
INSERT IGNORE INTO productos (nombre, activo) VALUES
    ('Gordita', 1),
    ('Sope', 1);

-- 2. Ingredientes: Guisos principales (es_guiso = 1)
INSERT IGNORE INTO ingredientes (nombre, es_guiso, activo) VALUES
    ('Chicharron', 1, 1),
    ('Papas', 1, 1),
    ('Huevo rojo', 1, 1),
    ('Huevo verde', 1, 1),
    ('Nopales', 1, 1),
    ('Aldilla', 1, 1),
    ('Rajas', 1, 1),
    ('Chorizo', 1, 1);

-- 3. Ingredientes: Complementos y guarniciones (es_guiso = 0)
INSERT IGNORE INTO ingredientes (nombre, es_guiso, activo) VALUES
    ('Queso', 0, 1),
    ('Crema', 0, 1),
    ('Cebolla', 0, 1),
    ('Verdura', 0, 1);

-- 4. Reglas para GORDITA:
--    - BASE: todos los guisos
INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
SELECT p.id, i.id, 'BASE'
FROM productos p
CROSS JOIN ingredientes i
WHERE p.nombre = 'Gordita' AND i.es_guiso = 1;

--    - EXTRA: todos los guisos + Queso + Crema
INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
SELECT p.id, i.id, 'EXTRA'
FROM productos p
CROSS JOIN ingredientes i
WHERE p.nombre = 'Gordita'
  AND (i.es_guiso = 1 OR i.nombre IN ('Queso', 'Crema'));

-- 5. Reglas para SOPE:
--    - BASE: todos los guisos
INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
SELECT p.id, i.id, 'BASE'
FROM productos p
CROSS JOIN ingredientes i
WHERE p.nombre = 'Sope' AND i.es_guiso = 1;

--    - EXTRA: todos los guisos + Queso
INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
SELECT p.id, i.id, 'EXTRA'
FROM productos p
CROSS JOIN ingredientes i
WHERE p.nombre = 'Sope'
  AND (i.es_guiso = 1 OR i.nombre IN ('Queso'));

--    - SIN: Cebolla, Verdura, Crema, Queso
INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
SELECT p.id, i.id, 'SIN'
FROM productos p
CROSS JOIN ingredientes i
WHERE p.nombre = 'Sope'
  AND i.nombre IN ('Cebolla', 'Verdura', 'Crema', 'Queso');
