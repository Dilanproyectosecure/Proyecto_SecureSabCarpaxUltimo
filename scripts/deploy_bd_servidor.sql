-- ============================================
-- SCRIPT SQL: Replicar cambios de BD al servidor
-- Ejecutar en el MySQL del servidor Azure
-- ============================================

SET FOREIGN_KEY_CHECKS=0;

-- ============================================
-- 1. LIMPIAR DATOS RELACIONADOS
-- ============================================
DELETE FROM asistencia_ambiente;
DELETE FROM asistencia_sede;
DELETE FROM justificacion;
DELETE FROM novedad;
DELETE FROM llamado_atencion;
DELETE FROM ficha_instructor;
DELETE FROM registro_manual;
DELETE FROM visitante;
DELETE FROM gestor_sistema_registro_actividad;
DELETE FROM historial_fallos;
DELETE FROM huella;
DELETE FROM notification;
DELETE FROM role_user;

-- ============================================
-- 2. ELIMINAR USUARIOS EXCEPTO LOS NECESARIOS
-- Mantener: instructores(14,15), coordinador(22), aprendices de ficha 1
-- ============================================
DELETE FROM usuarios WHERE id_usuario NOT IN (
    1, 14, 15, 22, 23, 57, 58, 59,
    84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98
);

-- ============================================
-- 3. ELIMINAR FICHAS EXCEPTO 3065834 (ID:1)
-- ============================================
DELETE FROM ficha WHERE id_ficha != 1;

-- ============================================
-- 4. RENOMBRAR INSTRUCTORES
-- ============================================
UPDATE usuarios SET nombre='Marcela', apellido='Reyes' WHERE id_usuario=14;
UPDATE usuarios SET nombre='Nelson', apellido='Rodriguez' WHERE id_usuario=15;

-- ============================================
-- 5. ALTERAR PK DE ficha_instructor A 3 COLUMNAS
-- ============================================
ALTER TABLE ficha_instructor MODIFY COLUMN id_competencia INT NOT NULL;
ALTER TABLE ficha_instructor DROP PRIMARY KEY;
ALTER TABLE ficha_instructor ADD PRIMARY KEY (id_ficha, id_instructor, id_competencia);

-- ============================================
-- 6. ASIGNAR COMPETENCIAS EN FICHA 1 (3065834)
-- Marcela Reyes (14) -> Ingles (28)
-- Nelson Rodriguez (15) -> Software (17) + Implementar software (27)
-- ============================================
INSERT INTO ficha_instructor (id_ficha, id_instructor, id_competencia) VALUES
    (1, 14, 28),
    (1, 15, 17),
    (1, 15, 27);

-- ============================================
-- 7. ASIGNAR ROLES
-- ============================================
INSERT INTO role_user (id_usuario, role_id) VALUES
    (14, 3),   -- Marcela -> instructor
    (15, 3),   -- Nelson -> instructor
    (22, 5),   -- Laura -> coordinador
    (1, 2),    -- Aprendices -> rol aprendiz
    (23, 2),
    (57, 2),
    (58, 2),
    (59, 2),
    (84, 2),
    (85, 2),
    (86, 2),
    (87, 2),
    (88, 2),
    (89, 2),
    (90, 2),
    (91, 2),
    (92, 2),
    (93, 2),
    (94, 2),
    (95, 2),
    (96, 2),
    (97, 2),
    (98, 2);

-- ============================================
-- 8. CREAR VIGILANTE: Carlos Sanchez
-- ============================================
INSERT INTO usuarios (id_usuario, tipo_documento, cedula, correo, nombre, apellido, id_ficha, telefono, estado, password, is_active, is_staff, is_superuser)
VALUES (25, 'CC', '1000856999', 'carlos@senaa.edu.co', 'Carlos', 'Sanchez', NULL, '3001234567', 'Activo',
    'bcrypt_sha256$$2b$12$Tlc31Xe81F48XWpYzPBLE.FNoj3CKIu8R2VQtAuYu.8iCKlf6D3SW',
    1, 0, 0);

INSERT INTO role_user (id_usuario, role_id) VALUES (25, 6);  -- vigilante

SET FOREIGN_KEY_CHECKS=1;

-- ============================================
-- VERIFICACION
-- ============================================
SELECT 'Fichas' AS tabla, COUNT(*) AS total FROM ficha
UNION ALL
SELECT 'Usuarios', COUNT(*) FROM usuarios
UNION ALL
SELECT 'FichaInstructor', COUNT(*) FROM ficha_instructor
UNION ALL
SELECT 'RoleUser', COUNT(*) FROM role_user
UNION ALL
SELECT 'AsistenciaAmbiente', COUNT(*) FROM asistencia_ambiente
UNION ALL
SELECT 'AsistenciaSede', COUNT(*) FROM asistencia_sede;
